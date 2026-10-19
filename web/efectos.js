// Efectos de ambiente: polvo de estrellas pixelado al fondo y el latido de espera.

const quieto = matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- polvo: partículas que flotan con ondita, en píxeles gruesos ----------

const PIXEL = 4;  // cada partícula es un píxel de 4x4 en pantalla
const COLORES = ['227,176,99', '246,220,160', '216,195,165', '201,138,94', '181,236,154'];

export function polvo(canvas) {
  const ctx = canvas.getContext('2d');
  let w = 0, h = 0, motas = [];

  function medir() {
    w = Math.ceil(innerWidth / PIXEL);
    h = Math.ceil(innerHeight / PIXEL);
    canvas.width = w;
    canvas.height = h;
    const n = Math.round(Math.min(110, (w * h) / 260));
    motas = Array.from({ length: n }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.06,
      vy: -0.015 - Math.random() * 0.05,          // suben despacito, como polvo al sol
      onda: 2 + Math.random() * 6,                 // qué tanto se mecen
      fase: Math.random() * Math.PI * 2,
      ritmo: 0.0004 + Math.random() * 0.0008,
      color: COLORES[Math.random() < 0.12 ? 4 : Math.floor(Math.random() * 4)],
      brillo: 0.15 + Math.random() * 0.5,
      grande: Math.random() < 0.08,
    }));
  }

  function cuadro(t) {
    ctx.clearRect(0, 0, w, h);
    for (const m of motas) {
      if (!quieto) {
        m.x += m.vx;
        m.y += m.vy;
        if (m.y < -2) { m.y = h + 2; m.x = Math.random() * w; }
        if (m.x < -8) m.x = w + 8; else if (m.x > w + 8) m.x = -8;
      }
      const x = Math.round(m.x + Math.sin(t * m.ritmo + m.fase) * m.onda);
      const y = Math.round(m.y);
      const a = m.brillo * (0.55 + 0.45 * Math.sin(t * m.ritmo * 3 + m.fase));
      ctx.fillStyle = `rgba(${m.color},${a.toFixed(3)})`;
      if (m.grande) {  // una crucecita de 3 píxeles
        ctx.fillRect(x - 1, y, 3, 1);
        ctx.fillRect(x, y - 1, 1, 3);
      } else {
        ctx.fillRect(x, y, 1, 1);
      }
    }
    if (!quieto && !document.hidden) requestAnimationFrame(cuadro);
  }

  medir();
  addEventListener('resize', medir);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) requestAnimationFrame(cuadro); });
  requestAnimationFrame(cuadro);
}

// ---------- espera: una onda de píxeles que late mientras el Oracool duerme ----------

export function espera(canvas) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  let activo = false, buscando = false, id = 0;

  function cuadro(t) {
    ctx.clearRect(0, 0, W, H);
    const vel = buscando ? 0.006 : 0.0022;
    const amp = buscando ? 5 : 2.5 + 1.5 * Math.sin(t * 0.0012);  // respira
    for (let x = 0; x < W; x += 2) {
      const borde = Math.sin((x / (W - 1)) * Math.PI);            // más alta al centro
      const y = H / 2 + Math.sin(x * 0.18 - t * vel) * amp * borde;
      const a = 0.25 + 0.75 * borde;
      ctx.fillStyle = buscando ? `rgba(181,236,154,${a})` : `rgba(227,176,99,${a})`;
      ctx.fillRect(x, Math.round(y), 1, 1);
      if (buscando) {  // una segunda onda que se cruza con la primera
        const y2 = H / 2 + Math.sin(x * 0.11 + t * vel * 1.3) * amp * 0.7 * borde;
        ctx.fillStyle = `rgba(227,176,99,${a * 0.7})`;
        ctx.fillRect(x + 1, Math.round(y2), 1, 1);
      }
    }
    if (activo) id = requestAnimationFrame(cuadro);
  }

  return {
    encender() { if (!activo) { activo = true; id = requestAnimationFrame(cuadro); } },
    apagar() { activo = false; cancelAnimationFrame(id); },
    buscar(si) { buscando = si; },
  };
}
