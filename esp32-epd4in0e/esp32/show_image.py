# Run this on the BOARD. Shows a .bin made by convert.py on the e-ink screen.
# It reads the file in small chunks, so it doesn't need 120 KB of free RAM.

import epdconfig
import epd4in0e as e

IMAGE = "pics/r2.bin"     # change to your file name
CHUNK = 2000

epd = e.EPD()
print("init...")
epd.init()

print("sending", IMAGE)
epd.send_command(0x10)
epdconfig.digital_write(epd.dc_pin, 1)
epdconfig.digital_write(epd.cs_pin, 0)
sent = 0
with open(IMAGE, "rb") as f:
    while True:
        chunk = f.read(CHUNK)
        if not chunk:
            break
        epdconfig.spi_writebyte2(chunk)
        sent += len(chunk)
epdconfig.digital_write(epd.cs_pin, 1)

if sent != e.BUF_SIZE:
    print("warning: file is %d bytes, expected %d" % (sent, e.BUF_SIZE))

print("refreshing (about 20-30 s)...")
epd.TurnOnDisplay()
epd.sleep()
print("done")