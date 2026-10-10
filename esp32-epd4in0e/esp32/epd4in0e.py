# epd4in0e.py - Waveshare 4inch e-Paper HAT+ (E) driver, ported to MicroPython (ESP32-S3).
# Based on Waveshare's epd4in0e.py (MIT license). Changes: no PIL, plain `import epdconfig`,
# and images are passed as a packed bytearray (2 pixels per byte, 4 bits each).

import epdconfig

try:
    import logging
    logger = logging.getLogger(__name__)
except ImportError:
    class _NoLog:
        def debug(self, *a): pass
        info = warning = error = debug
    logger = _NoLog()

EPD_WIDTH  = 400
EPD_HEIGHT = 600

# 4-bit colour codes the panel understands
BLACK  = 0x0
WHITE  = 0x1
YELLOW = 0x2
RED    = 0x3
BLUE   = 0x5
GREEN  = 0x6

BUF_SIZE = EPD_WIDTH * EPD_HEIGHT // 2   # 120,000 bytes


class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    # ---- low level ----
    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(2)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data2(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(self.cs_pin, 1)

    def ReadBusyH(self, timeout_ms=60000):
        logger.debug("e-Paper busy H")
        waited = 0
        while epdconfig.digital_read(self.busy_pin) == 0:   # 0: busy, 1: idle
            epdconfig.delay_ms(5)
            waited += 5
            if waited >= timeout_ms:
                raise RuntimeError("BUSY pin never went high - check wiring (CS, BUSY, PWR, VCC)")
        epdconfig.delay_ms(200)
        logger.debug("e-Paper busy H release")

    def TurnOnDisplay(self):
        self.send_command(0x04)  # POWER_ON
        self.ReadBusyH()

        self.send_command(0x06)
        for b in (0x6F, 0x1F, 0x17, 0x27):
            self.send_data(b)
        epdconfig.delay_ms(200)

        self.send_command(0x12)  # DISPLAY_REFRESH
        self.send_data(0x00)
        self.ReadBusyH()

        self.send_command(0x02)  # POWER_OFF
        self.send_data(0x00)
        self.ReadBusyH()

    def init(self):
        if epdconfig.module_init() != 0:
            return -1
        self.reset()
        self.ReadBusyH()
        epdconfig.delay_ms(30)

        for cmd, data in (
            (0xAA, (0x49, 0x55, 0x20, 0x08, 0x09, 0x18)),
            (0x01, (0x3F,)),
            (0x00, (0x5F, 0x69)),
            (0x05, (0x40, 0x1F, 0x1F, 0x2C)),
            (0x08, (0x6F, 0x1F, 0x1F, 0x22)),
            (0x06, (0x6F, 0x1F, 0x17, 0x17)),
            (0x03, (0x00, 0x54, 0x00, 0x44)),
            (0x60, (0x02, 0x00)),
            (0x30, (0x08,)),
            (0x50, (0x3F,)),
            (0x61, (0x01, 0x90, 0x02, 0x58)),
            (0xE3, (0x2F,)),
            (0x84, (0x01,)),
        ):
            self.send_command(cmd)
            for b in data:
                self.send_data(b)
        self.ReadBusyH()
        return 0

    # ---- drawing ----
    def display(self, buf):
        """buf: bytearray of BUF_SIZE bytes, 2 pixels per byte (high nibble = left pixel)."""
        self.send_command(0x10)
        self.send_data2(buf)
        self.TurnOnDisplay()

    def Clear(self, color=WHITE):
        """Fill the screen with one colour without allocating a 120 KB buffer."""
        byte = (color << 4) | color
        chunk = bytes([byte]) * 2000
        self.send_command(0x10)
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        for _ in range(BUF_SIZE // len(chunk)):
            epdconfig.spi_writebyte2(chunk)
        epdconfig.digital_write(self.cs_pin, 1)
        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x07)  # DEEP_SLEEP
        self.send_data(0xA5)
        epdconfig.delay_ms(2000)
        epdconfig.module_exit()


def new_framebuffer():
    """Return (buf, fb): a bytearray and a framebuf you can draw on with the colour codes above.
    Needs ~120 KB free RAM (fine on boards with PSRAM)."""
    import framebuf
    buf = bytearray([(WHITE << 4) | WHITE]) * BUF_SIZE
    fb = framebuf.FrameBuffer(buf, EPD_WIDTH, EPD_HEIGHT, framebuf.GS4_HMSB)
    return buf, fb