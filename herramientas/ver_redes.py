# Se corre EN la placa: dice si hay Wi-Fi conectado y qué redes ve.
import network

w = network.WLAN(network.STA_IF)
print("wifi activo:", w.active())
w.active(True)
print("conectado:", w.isconnected(), w.ifconfig() if w.isconnected() else "")
for r in sorted(w.scan(), key=lambda r: -r[3]):
    print("  red:", r[0].decode() or "(oculta)", "señal:", r[3], "dBm", "canal:", r[2])
w.active(False)
