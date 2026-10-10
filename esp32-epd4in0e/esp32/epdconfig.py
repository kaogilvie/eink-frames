# epdconfig.py - MicroPython (ESP32-S3) replacement for Waveshare's hardware layer.
# Exposes the same functions the Waveshare epdXinX drivers call, so they can import it unchanged.

import time
from machine import Pin, SPI

try:
    import logging
    logger = logging.getLogger(__name__)
except ImportError:
    class _NoLog:
        def debug(self, *a): pass
        info = warning = error = debug
    logger = _NoLog()

# ---- Pin definitions: CHANGE THESE to match your wiring (ESP32-S3 GPIO numbers) ----
# DIN / CLK: the SPI data line and its clock. Data bits travel on DIN, one per CLK tick.
# BUSY: the display signals back that it’s still refreshing, so the driver waits before sending more. E-ink refreshes take seconds, and the 6-color one is slow.
# PWR: switches the display board’s power on and off, so it can draw almost nothing between updates.
# VCC / GND: 3.3V power and ground.
# RST (Reset): pulling it low briefly restarts the display’s controller chip, like a reboot button
# DC (Data/Command): tells the display how to interpret the next bytes on the SPI line. Low means “this is a command” (for example “start refresh”). High means “this is data” (for example the pixel colors or a command’s settings)
# CS (Chip Select): tells the display “I’m talking to you now.” Low means listen, high means ignore the SPI lines.
RST_PIN  = 10
DC_PIN   = 17 
CS_PIN   = 15
BUSY_PIN = 4
PWR_PIN  = 16
MOSI_PIN = 11   # DIN
SCLK_PIN = 12   # CLK

# SPI = SERIAL PERIPHERAL INTERFACE
# BAUD = unit of measurement for symbol rate per second across communication interface
SPI_ID   = 2      # ESP32-S3 MicroPython hardware SPI is 1 or 2
SPI_BAUD = 4_000_000

# ---- Pin objects ----
_rst  = Pin(RST_PIN, Pin.OUT, value=1)
_dc   = Pin(DC_PIN, Pin.OUT, value=0)
_cs   = Pin(CS_PIN, Pin.OUT, value=1)
_busy = Pin(BUSY_PIN, Pin.IN)
_pwr  = Pin(PWR_PIN, Pin.OUT, value=0) if PWR_PIN is not None else None

_out = {RST_PIN: _rst, DC_PIN: _dc, CS_PIN: _cs}
if _pwr is not None:
    _out[PWR_PIN] = _pwr

_spi = None


def digital_write(pin, value):
    p = _out.get(pin)
    if p is not None:
        p.value(1 if value else 0)


def digital_read(pin):
    if pin == BUSY_PIN:
        return _busy.value()
    p = _out.get(pin)
    return p.value() if p is not None else 0


def delay_ms(delaytime):
    time.sleep_ms(int(delaytime))


def _write(buf):
    # Newer Waveshare drivers toggle CS themselves; older ones don't.
    # If CS is still high (driver didn't select the chip), select it just for this write.
    if _cs.value():
        _cs.value(0)
        _spi.write(buf)
        _cs.value(1)
    else:
        _spi.write(buf)


def spi_writebyte(data):
    _write(bytes(data))


def spi_writebyte2(data):
    if not isinstance(data, (bytes, bytearray, memoryview)):
        data = bytes(data)
    _write(data)


def module_init(*args, **kwargs):
    global _spi
    if _pwr is not None:
        _pwr.value(1)
    _spi = SPI(SPI_ID, baudrate=SPI_BAUD, polarity=0, phase=0,
               sck=Pin(SCLK_PIN), mosi=Pin(MOSI_PIN))
    return 0


def module_exit(*args, **kwargs):
    global _spi
    logger.debug("spi end")
    if _spi is not None:
        _spi.deinit()
        _spi = None
    _rst.value(0)
    _dc.value(0)
    if _pwr is not None:
        _pwr.value(0)
    logger.debug("display powered down")