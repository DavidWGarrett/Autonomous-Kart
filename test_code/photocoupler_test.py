from gpiozero import LED
from time import sleep

# Define the GPIO pin connected to the 4N35 anode through a resistor
photocoupler_led = LED(6)  # GPIO6

try:
    while True:
        print("Turning ON 4N35 input LED")
        photocoupler_led.on()  # Current flows through 4N35's LED
        sleep(20)

        print("Turning OFF 4N35 input LED")
        photocoupler_led.off()  # Stops current
        sleep(20)

except KeyboardInterrupt:
    print("\nExiting program.")
