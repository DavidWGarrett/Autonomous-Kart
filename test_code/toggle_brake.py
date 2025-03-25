from gpiozero import LED
from time import sleep

# Assign GPIO pins
moving = LED(12)       # GPIO 12
stationary = LED(13)   # GPIO 13

def extend_actuator():
    print("Extending actuator...")
    stationary.off()   # Ensure reverse is off
    moving.on()
    sleep(20)          # Extend duration
    moving.off()

def retract_actuator():
    print("Retracting actuator...")
    moving.off()       # Ensure forward is off
    stationary.on()
    sleep(20)          # Retract duration
    stationary.off()

try:
    for i in range(5):  # Run 5 cycles
        print(f"\nCycle {i + 1}")
        extend_actuator()
        sleep(10)       # Pause after extending
        retract_actuator()
        sleep(10)       # Pause after retracting

    print("All cycles complete. Cleaning up...")

except KeyboardInterrupt:
    print("Interrupted! Stopping actuator...")

finally:
    moving.off()
    stationary.off()
    moving.close()
    stationary.close()
