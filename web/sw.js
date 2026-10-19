// Guarda la app para que abra aunque no haya internet (el Bluetooth no lo necesita).
// Sube la versión cada vez que publiques cambios.
const VERSION = 'oracools-v2';
const ARCHIVOS = [
  './', 'index.html', 'estilo.css', 'app.js', 'manifest.webmanifest',
  'iconos/icono-192.png', 'iconos/icono-512.png', 'iconos/apple-touch-icon.png',
  'marca/oraculos-logotipo.png', 'fuentes/ChakraPetch-Regular.ttf', 'fuentes/ChakraPetch-Medium.ttf',
  'fuentes/ChakraPetch-SemiBold.ttf',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(ARCHIVOS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// Primero la red (para ver cambios al instante), y si no hay, lo guardado.
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then((r) => {
        const copia = r.clone();
        caches.open(VERSION).then((c) => c.put(e.request, copia));
        return r;
      })
      .catch(() => caches.match(e.request)),
  );
});
