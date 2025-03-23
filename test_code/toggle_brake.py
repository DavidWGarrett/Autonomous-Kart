from gpiozero import LED
from time import sleep

# Assign GPIO pins
moving = LED(12)       # GPIO 12
stationary = LED(13)   # GPIO 13

def extend_actuator():
    print("Extending actuator...")
    stationary.off()   # Ensure reverse is off
    moving.on()
    sleep(20)
    moving.off()

def retract_actuator():
    print("Retracting actuator...")
    moving.off()       # Ensure forward is off
    stationary.on()
    sleep(20)
    stationary.off()

try:
    while True:
        extend_actuator()
        sleep(1)
        retract_actuator()
        sleep(1)

except KeyboardInterrupt:
    print("Stopping actuator...")
    moving.off()
    stationary.off()
