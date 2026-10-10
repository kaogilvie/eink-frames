import logging
logging.basicConfig(level=logging.DEBUG)
print("1 start")

import epdconfig
print("2 config ok, busy =", epdconfig.digital_read(epdconfig.BUSY_PIN))

import epd4in0e
print("3 driver imported")

epd = epd4in0e.EPD()
print("4 init...")
epd.init()
print("5 init done")

epd.Clear()
print("6 clear done")
epd.sleep()
print("7 finished")