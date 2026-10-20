# Oracools

A phygital sculptural collection by Julio Sahagún Sánchez and Tessa Fansa Vega

Edición phygital de los **Oráculos telúrico-sintéticos**: esculturas impresas en 3D con un
ESP32-C3 y una pantallita OLED de 0.42" (72×40) adentro, que se despiertan y conversan
desde el celular por Bluetooth.

> El celular es la mente, el Oracool es el cuerpo.

## Partes

| Carpeta | Qué es |
|---|---|
| `firmware/` | MicroPython para el ESP32-C3: pantalla, glifos, Bluetooth y estados |
| `web/` | La webapp (PWA, sin frameworks) que se publica en cools.oraculos.app |
| `herramientas/` | Pruebas y utilidades (algunas corren en la placa con `mpremote run`) |
| `respaldos/` | Firmware original de la placa (no va al repo) |

## Hardware

- ESP32-C3 (QFN32, 4 MB), USB nativo → aparece como puerto COM
- OLED SSD1306 72×40 en I2C: **SDA = GPIO5, SCL = GPIO6**, dirección `0x3C`
  (el panel vive en las columnas 28–99 de la memoria del controlador)
- Botón BOOT = GPIO9 → el "toque"

## Cargar el firmware

```bash
python -m mpremote connect COM3 cp firmware/oled42.py firmware/glifos.py firmware/enlace.py firmware/oracool.py firmware/main.py : + reset
```

## Probar la webapp en local

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory web
```

Abre http://localhost:8000 en **Chrome** (Web Bluetooth necesita Chrome/Edge en Android o
computadora; en iPhone, la app Bluefy). Fuera de localhost tiene que ser HTTPS.

## Protocolo Bluetooth

Servicio `4f524143-4f4f-4c53-8000-000000000001` ("ORACOOLS"), anuncia como `Oracool`.

| Característica | UUID termina en | Dirección | Contenido |
|---|---|---|---|
| ESCUCHA | `…0002` | app → Oracool | comandos de texto terminados en `\n` (trozos de 20 bytes) |
| VOZ | `…0003` | Oracool → app | eventos: `SOY:<nombre>`, `ESTADO:<cara>`, `TOQUE`, `?<desconocido>`, `ERR:…` |
| LIENZO | `…0004` | ambas | pantalla cruda MONO_VLSB de 360 bytes en 20 bloques: 2 bytes de posición (LE) + 18 de píxeles |

Comandos: `HOLA`, `CARA:<glifo>` (ojo, ojos, tercer, boca, habla, nariz, rostro, cuernos, sol, luna, cielo, orbe, runa, rombo, circuito, espiral, gota, onda, dormido, o `reposo` = desfile), `TXT:<texto>`
(`|` = salto de renglón), `BRILLO:<0-255>`, `INV:<0|1>`, `ESPEJO`, `LIMPIA`.

Cada vez que cambia lo que se ve, el Oracool manda su pantalla por LIENZO (el "espejo"),
así la app muestra exactamente lo mismo.

## Publicar

```bash
bash herramientas/publicar.sh   # https://cools.oraculos.app
```

Cada vez que cambies estilo.css, app.js o efectos.js, sube el `?v=` en index.html,
app.js y sw.js (y la VERSION de sw.js) para que ningún navegador se quede con lo viejo.

## Pruebas

```bash
python -m mpremote connect COM3 run herramientas/prueba_firmware.py
python -m mpremote connect COM3 run herramientas/prueba_animo.py
python -m mpremote connect COM3 run herramientas/prueba_ofrendas.py
python herramientas/prueba_ble.py
```

## Licencia

CC0 1.0 Universal (ver `LICENSE`).
