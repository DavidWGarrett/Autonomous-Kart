import spidev
import time
from gpiozero import DigitalOutputDevice

"""
CS → GPIO17
SCK → GPIO21 (SPI1_SCLK)
MOSI → GPIO20 (SPI1_MOSI)
MISO → GPIO19 (SPI1_MISO)
VDD → 5V
VSS → GND
P0W → Alltrax Throttle 1
P0B → Alltrax Throttle 2
"""


# MCP4162 constants
WIPER_VOLATILE_REGISTER = 0x00  # Command byte for volatile write

# Setup SPI1
spi_bus = 1
spi_device = 0

spi = spidev.SpiDev()
spi.open(spi_bus, spi_device)
spi.max_speed_hz = 1000000  # 1 MHz
spi.mode = 0b00

# CS on GPIO17
cs = DigitalOutputDevice(17, active_high=False, initial_value=True)

def set_wiper(value):
    if value < 0 or value > 255:
        print("Wiper value must be between 0 and 255")
        return
    cs.off()  # Enable device (active low)
    spi.xfer2([WIPER_VOLATILE_REGISTER, value])
    cs.on()   # Disable device
    print(f"Wiper set to: {value}")

try:
    print("Starting MCP4162 ramp loop (0 to 50 to 0)...")

    while True:
        # Ramp up
        for val in range(0, 255):
            set_wiper(val)
            time.sleep(0.1)

        # Ramp down
        for val in reversed(range(0, 255)):
            set_wiper(val)
            time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    spi.close()
    cs.close()
