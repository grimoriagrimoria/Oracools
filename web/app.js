// Oracools: la app que despierta y le habla a un Oracool por Bluetooth.
// El protocolo vive en firmware/enlace.py y firmware/oracool.py.

const SERVICIO = '4f524143-4f4f-4c53-8000-000000000001';
const ESCUCHA = '4f524143-4f4f-4c53-8000-000000000002';
const VOZ = '4f524143-4f4f-4c53-8000-000000000003';
const LIENZO = '4f524143-4f4f-4c53-8000-000000000004';

const W = 72, H = 40, TAM = W * H / 8;   // 360 bytes, formato MONO_VLSB
const BLOQUE = 18;                        // píxeles por bloque BLE (+2 de posición)
const ESCALA = 6;                         // 72x40 -> 432x240 en el canvas

import { polvo, espera } from './efectos.js';

const $ = (s) => document.querySelector(s);
const pantalla = $('#pantalla');
const ctx = pantalla.getContext('2d');

let dispositivo = null;
let chars = null;            // { escucha, voz, lienzo }
let cola = Promise.resolve(); // las operaciones GATT van una por una
let buf = new Uint8Array(TAM);       // lo que muestra el canvas
const espejo = new Uint8Array(TAM);  // donde se arma lo que manda el Oracool
let dibujando = false;

// ---------- pantalla -------------------------------------------------------

function px(b, x, y) { return (b[(y >> 3) * W + x] >> (y & 7)) & 1; }
function ponPx(b, x, y, v) {
  const i = (y >> 3) * W + x, m = 1 << (y & 7);
  b[i] = v ? b[i] | m : b[i] & ~m;
}

const css = getComputedStyle(document.documentElement);
function pintar() {
  ctx.fillStyle = css.getPropertyValue('--oled').trim() || '#0b1413';
  ctx.fillRect(0, 0, pantalla.width, pantalla.height);
  ctx.fillStyle = css.getPropertyValue('--pixel').trim() || '#b5ec9a';
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++)
      if (px(buf, x, y)) ctx.fillRect(x * ESCALA, y * ESCALA, ESCALA - 1, ESCALA - 1);
}

// ---------- bitácora y estado ----------------------------------------------

const RELATOS = {
  ojo: 'El Oracool abrió su ojo.',
  boca: 'El Oracool guarda silencio con los labios cerrados.',
  habla: 'El Oracool murmura.',
  rostro: 'El Oracool muestra su rostro.',
  sol: 'El Oracool irradia.',
  tercer: 'El Oracool abrió el tercer ojo.',
  dormido: 'El Oracool volvió al sueño de la tierra.',
  reposo: 'El Oracool se entrega al azar: sus glifos desfilan.',
  cuernos: 'El Oracool muestra su silueta de dos puntas.',
  rombo: 'El Oracool guarda el rombo de la Á.',
  circuito: 'Chispas recorren los circuitos del Oracool.',
  espiral: 'El Oracool gira hacia adentro.',
  luna: 'Sale la luna en el Oracool.',
  cielo: 'El Oracool mira las estrellas.',
  gota: 'Algo escurre del Oracool.',
  ojos: 'El Oracool te mira con dos ojos.',
  trisquel: 'Tres espirales giran en el Oracool.',
  orbe: 'El orbe del Oracool late.',
  runa: 'El Oracool traza su runa.',
  onda: 'Ondas salen del centro del Oracool.',
  texto: 'El Oracool sostiene tus palabras.',
  lienzo: 'El Oracool muestra tu dibujo.',
};

function anotar(msg) {
  const li = document.createElement('li');
  const t = document.createElement('time');
  t.textContent = new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
  li.append(t, msg);
  $('#bitacora').prepend(li);
}

function estado(msg) { $('#estado').textContent = msg; }

// ---------- Bluetooth ------------------------------------------------------

function enCola(fn) {
  const p = cola.then(fn);
  cola = p.catch(() => {});
  return p;
}

async function escribir(c, datos) {
  await c.writeValueWithResponse(datos);
}

function mandar(texto) {
  if (!chars) return Promise.resolve();
  const bytes = new TextEncoder().encode(texto + '\n');
  return enCola(async () => {
    for (let i = 0; i < bytes.length; i += 20) await escribir(chars.escucha, bytes.slice(i, i + 20));
  }).catch((e) => anotar('No se pudo mandar: ' + e.message));
}

function mandarLienzo() {
  if (!chars) return Promise.resolve();
  const copia = buf.slice();
  return enCola(async () => {
    for (let pos = 0; pos < TAM; pos += BLOQUE) {
      const b = new Uint8Array(2 + BLOQUE);
      b[0] = pos & 0xff; b[1] = pos >> 8;
      b.set(copia.subarray(pos, pos + BLOQUE), 2);
      await escribir(chars.lienzo, b);
    }
  }).catch((e) => anotar('No se pudo mandar el dibujo: ' + e.message));
}

function alOirVoz(e) {
  const msg = new TextDecoder().decode(e.target.value);
  const [clave, valor] = msg.split(/:(.*)/s);
  if (clave === 'SOY') {
    estado(`${valor} está despierto.`);
  } else if (clave === 'ESTADO') {
    marcarCara(valor);
    if (RELATOS[valor]) anotar(RELATOS[valor]);
  } else if (clave === 'TOQUE') {
    anotar('El Oracool sintió un toque.');
  } else if (clave === 'ERR') {
    anotar('El Oracool se confundió: ' + valor);
  } else {
    anotar('El Oracool dijo: ' + msg);
  }
}

function alVerLienzo(e) {
  const v = new Uint8Array(e.target.value.buffer);
  const pos = v[0] | (v[1] << 8);
  espejo.set(v.subarray(2, 2 + Math.min(BLOQUE, TAM - pos)), pos);
  if (pos + BLOQUE >= TAM && !dibujando) {
    buf = espejo.slice();
    pintar();
  }
}

async function enlazar() {
  estado('Escuchando la tierra…');
  const server = await dispositivo.gatt.connect();
  const svc = await server.getPrimaryService(SERVICIO);
  chars = {
    escucha: await svc.getCharacteristic(ESCUCHA),
    voz: await svc.getCharacteristic(VOZ),
    lienzo: await svc.getCharacteristic(LIENZO),
  };
  chars.voz.addEventListener('characteristicvaluechanged', alOirVoz);
  chars.lienzo.addEventListener('characteristicvaluechanged', alVerLienzo);
  await chars.voz.startNotifications();
  await chars.lienzo.startNotifications();
  $('#despertar').textContent = 'Dormir al Oracool';
  enlazado(true);
  anotar(`Despertaste a ${dispositivo.name}.`);
  await mandar('HOLA');
}

const latido = espera($('#espera'));

async function despertar() {
  if (dispositivo?.gatt.connected) {
    await mandar('CARA:dormido');
    dispositivo.gatt.disconnect();
    return;
  }
  try {
    $('#marco').classList.add('buscando');
    latido.buscar(true);
    if (!dispositivo) {
      anotar('Llamando a los Oracools cercanos…');
      dispositivo = await navigator.bluetooth.requestDevice({
        filters: [{ namePrefix: 'Oracool' }],
        optionalServices: [SERVICIO],
      });
      dispositivo.addEventListener('gattserverdisconnected', alDesconectar);
    }
    await enlazar();
  } catch (e) {
    if (e.name === 'NotFoundError') {
      estado('Ningún Oracool respondió al llamado.');
      anotar('Nadie respondió, o cerraste la ventana. ¿Está encendido el Oracool?');
    }
    else { estado('No se pudo despertar.'); anotar(e.message); }
  } finally {
    $('#marco').classList.remove('buscando');
    latido.buscar(false);
  }
}

function enlazado(si) {
  document.body.classList.toggle('enlazado', si);
  $('#marco').classList.toggle('cerrado', !si);
  if (si) latido.apagar(); else { latido.encender(); salirDeDibujo(); }
  document.querySelectorAll('.requiere').forEach((el) => { el.disabled = !si; });
}

function alDesconectar() {
  chars = null;
  enlazado(false);
  cola = Promise.resolve();
  marcarCara(null);
  estado(`${dispositivo?.name ?? 'El Oracool'} se durmió.`);
  $('#despertar').textContent = 'Despertar al Oracool';
  anotar('Se rompió el hilo.');
}

// ---------- controles ------------------------------------------------------

function marcarCara(cara) {
  document.querySelectorAll('#rostros button').forEach((b) =>
    b.classList.toggle('activo', b.dataset.cara === cara));
}

$('#rostros').addEventListener('click', (e) => {
  const b = e.target.closest('button[data-cara]');
  if (!b) return;
  if (!chars) { anotar('Primero despierta al Oracool.'); return; }
  salirDeDibujo();
  marcarCara(b.dataset.cara);
  mandar('CARA:' + b.dataset.cara);
  anotar(RELATOS[b.dataset.cara]);
});

$('#palabras').addEventListener('submit', (e) => {
  e.preventDefault();
  const t = $('#texto').value.trim();
  if (!t) return;
  if (!chars) { anotar('Primero despierta al Oracool.'); return; }
  salirDeDibujo();
  marcarCara(null);
  mandar('TXT:' + t.replace(/\s*\n\s*/g, '|'));
  anotar(`Le susurraste: “${t}”`);
});

let tBrillo;
$('#brillo').addEventListener('input', (e) => {
  clearTimeout(tBrillo);
  tBrillo = setTimeout(() => mandar('BRILLO:' + e.target.value), 120);
});
$('#invertir').addEventListener('change', (e) => mandar('INV:' + (e.target.checked ? 1 : 0)));

// ---------- lienzo ---------------------------------------------------------

let tLienzo, trazo = null;
function lienzoCambio() {
  pintar();
  clearTimeout(tLienzo);
  tLienzo = setTimeout(mandarLienzo, 250);
}

function salirDeDibujo() {
  dibujando = false;
  pantalla.classList.remove('dibujando');
  $('#dibujar').setAttribute('aria-pressed', 'false');
}

$('#dibujar').addEventListener('click', () => {
  dibujando = !dibujando;
  pantalla.classList.toggle('dibujando', dibujando);
  $('#dibujar').setAttribute('aria-pressed', String(dibujando));
  if (dibujando) { marcarCara(null); lienzoCambio(); }
});
$('#borrar').addEventListener('click', () => {
  buf.fill(0);
  if (!dibujando) $('#dibujar').click(); else lienzoCambio();
});
$('#invertir-lienzo').addEventListener('click', () => {
  buf = buf.map((v) => ~v & 0xff);
  if (!dibujando) $('#dibujar').click(); else lienzoCambio();
});

function pixelBajo(e) {
  const r = pantalla.getBoundingClientRect();
  const x = Math.floor((e.clientX - r.left) / r.width * W);
  const y = Math.floor((e.clientY - r.top) / r.height * H);
  return x >= 0 && x < W && y >= 0 && y < H ? [x, y] : null;
}

function trazar(e) {
  const p = pixelBajo(e);
  if (!p) return;
  const [x, y] = p;
  // del último punto al actual, para que las líneas rápidas no queden punteadas
  const [x0, y0] = trazo.ultimo ?? p;
  const pasos = Math.max(Math.abs(x - x0), Math.abs(y - y0), 1);
  for (let i = 0; i <= pasos; i++)
    ponPx(buf, Math.round(x0 + (x - x0) * i / pasos), Math.round(y0 + (y - y0) * i / pasos), trazo.valor);
  trazo.ultimo = p;
  lienzoCambio();
}

pantalla.addEventListener('pointerdown', (e) => {
  if (!dibujando) return;
  const p = pixelBajo(e);
  if (!p) return;
  pantalla.setPointerCapture(e.pointerId);
  trazo = { valor: px(buf, ...p) ? 0 : 1, ultimo: null };  // si empiezas en un píxel encendido, borras
  trazar(e);
});
pantalla.addEventListener('pointermove', (e) => { if (trazo) trazar(e); });
const soltar = () => { trazo = null; };
pantalla.addEventListener('pointerup', soltar);
pantalla.addEventListener('pointercancel', soltar);

// ---------- arranque -------------------------------------------------------

if (!('bluetooth' in navigator)) {
  $('#sin-bluetooth').hidden = false;
  $('#despertar').disabled = true;
}
$('#despertar').addEventListener('click', despertar);
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', pintar);
// los paneles recuerdan si los dejaste abiertos o cerrados
document.querySelectorAll('details.panel').forEach((d) => {
  const clave = 'oracools:panel:' + d.dataset.panel;
  try { const v = localStorage.getItem(clave); if (v !== null) d.open = v === '1'; } catch {}
  d.addEventListener('toggle', () => { try { localStorage.setItem(clave, d.open ? '1' : '0'); } catch {} });
});

polvo($('#polvo'));
enlazado(false);
pintar();
anotar('La app está lista. Toca «Despertar al Oracool» para empezar.');

if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');
