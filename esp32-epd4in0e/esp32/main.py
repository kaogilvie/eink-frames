import machine
from neopixel import NeoPixel
import time
import wifi_config
import epd4in0e

pin = machine.Pin(48, machine.Pin.OUT)   
np = NeoPixel(pin, 1)   
np[0] = (10,0,0) 
np.write()              
r, g, b = np[0]

print("RGB Demo")

wifi = wifi_config.connect_to_wifi()

if wifi:
    print("SUCCESS: Connected to Wi-Fi!")
    print("Fetching newest photo from network...")
    # [YOUR DOWNLOAD CODE HERE]
    
else:
    print("WARNING: Wi-Fi connection failed. Skipping download.")

print("Initializing Solder-Free 4-Inch HAT+ Photo Frame")

# Bind the S3 high-speed SPI channels
spi = machine.SPI(1, baudrate=4000000, polarity=0, phase=0, sck=machine.Pin(12), mosi=machine.Pin(11))

# Set the 4-inch control line parameters
cs_pin   = machine.Pin(10, machine.Pin.OUT) # White Wire
dc_pin   = machine.Pin(17, machine.Pin.OUT) # Green Wire
rst_pin  = machine.Pin(16, machine.Pin.OUT) # Brown Wire
busy_pin = machine.Pin(4,  machine.Pin.IN)  # Purple Wire

display = epd4in0e.EPD(spi, cs_pin, dc_pin, rst_pin, busy_pin)

try:
    display.init()
    print("Clearing 4-inch display panels...")
    display.Clear()
    print("SUCCESS: 4-inch framework calibrated perfectly!")
    display.sleep()
except Exception as error:
    print("Communication Error:", error)