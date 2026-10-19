"""Prueba de punta a punta por Bluetooth desde la PC, hablando igual que la webapp.

Uso:  python herramientas/prueba_ble.py
"""
import asyncio
from bleak import BleakClient, BleakScanner

SERVICIO = "4f524143-4f4f-4c53-8000-000000000001"
ESCUCHA = "4f524143-4f4f-4c53-8000-000000000002"
VOZ = "4f524143-4f4f-4c53-8000-000000000003"
LIENZO = "4f524143-4f4f-4c53-8000-000000000004"
W, H, TAM, BLOQUE = 72, 40, 360, 18

voces = []
espejo = bytearray(TAM)
espejos = 0


def al_oir(_, datos):
    voces.append(datos.decode())
    print("  <-", datos.decode())


def al_ver(_, datos):
    global espejos
    pos = datos[0] | datos[1] << 8
    espejo[pos:pos + BLOQUE] = datos[2:2 + BLOQUE]
    if pos + BLOQUE >= TAM:
        espejos += 1


def ascii(buf):
    for y in range(0, H, 2):
        print("   " + "".join("#" if (buf[(y >> 3) * W + x] >> (y & 7)) & 1 else "." for x in range(W)))


async def mandar(c, texto):
    datos = (texto + "\n").encode()
    for i in range(0, len(datos), 20):
        await c.write_gatt_char(ESCUCHA, datos[i:i + 20], response=True)


async def main():
    print("buscando…")
    d = await BleakScanner.find_device_by_filter(
        lambda d, ad: (d.name or ad.local_name or "").startswith("Oracool"), timeout=15)
    assert d, "no encontré ningún Oracool"
    print("encontré", d.name, d.address)
    async with BleakClient(d) as c:
        await c.start_notify(VOZ, al_oir)
        await c.start_notify(LIENZO, al_ver)

        print("-> HOLA"); await mandar(c, "HOLA"); await asyncio.sleep(1.5)
        assert any(v.startswith("SOY:") for v in voces), "no respondió SOY"
        assert espejos >= 1, "no llegó el espejo"
        print("espejo tras HOLA (cada 2 renglones):"); ascii(espejo)

        print("-> CARA:sol"); n = espejos
        await mandar(c, "CARA:sol"); await asyncio.sleep(1.5)
        assert espejos > n, "no llegó el espejo del sol"
        ascii(espejo)

        print("-> TXT largo con acentos"); n = espejos
        await mandar(c, "TXT:¿De dónde venimos? ¿Quiénes somos? ¿A dónde vamos?")
        await asyncio.sleep(1.5)
        assert espejos > n
        ascii(espejo)

        print("-> lienzo: tablero de ajedrez")
        tablero = bytearray(TAM)
        for i in range(TAM):
            tablero[i] = 0x0F if (i // 4) % 2 else 0xF0
        for pos in range(0, TAM, BLOQUE):
            await c.write_gatt_char(LIENZO, bytes((pos & 255, pos >> 8)) + tablero[pos:pos + BLOQUE], response=True)
        await asyncio.sleep(0.5)
        print("-> ESPEJO"); n = espejos
        await mandar(c, "ESPEJO"); await asyncio.sleep(1.5)
        assert espejos > n and espejo == tablero, "el lienzo no volvió igualito"
        print("   el lienzo volvió idéntico")

        print("-> NOEXISTE"); await mandar(c, "NOEXISTE"); await asyncio.sleep(0.5)
        assert any(v.startswith("?") for v in voces)
        await mandar(c, "CARA:ojo"); await asyncio.sleep(0.5)
    print("¡todo bien!")


asyncio.run(main())
