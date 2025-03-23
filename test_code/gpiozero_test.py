from gpiozero import LED
from time import sleep

# Replace with the GPIO pin your LED is connected to (e.g., 17 is GPIO17 / Pin 11)
led = LED(17)

print("Turning on the LED...")
led.on()

# Keep it on for 5 seconds
sleep(5)

print("Turning off the LED...")
led.off()

