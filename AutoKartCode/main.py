#!/usr/bin/env python3
"""
main.py
=======

 * Reads comma-separated packets from /dev/ttyAMA0 (1200 baud).
 * Maps the six raw numbers exactly as you specified.
 * Spawns threads for throttle, steering, brake and a safety / mode supervisor.
 * If either e-stop goes active the supervisor:
      – disables throttle and steering,
      – applies the brake,
      – drops the enable-pin on GPIO-24.

Hardware pins used
------------------
GPIO-24  (enable for drivetrain – turns OFF during e-stop)
GPIO-27  MCP4162 CS   (driven by Throttle class)
GPIO-11  SPI-SCK      "
GPIO-10  SPI-MOSI     "
GPIO-16  Brake OUT (extend)
GPIO-17  Brake OUT (retract)
GPIO-22  Servo Jog-Left
GPIO-26  Servo Jog-Right
GPIO-12  Servo Enable
GPIO-19  Servo Fault Reset

The three helper modules must expose classes:

    Throttle(cs_pin=27, enable_pin=24, ...)
    Steering(enable_pin=12, fault_reset_pin=19,
             jog_left_pin=22, jog_right_pin=26)
    Brake(ext_pin=16, ret_pin=17)

Each of them must implement at minimum:

    .set(value)        # Throttle 0-255
    .set_dir(value)    # Steering  -1/0/+1     (blocks internally for 1 ms pulse)
    .apply() / .release()   # Brake
    .disable() / .enable()  # For safety

Feel free to adapt the names – just change the calls below.
"""

import serial, threading, time
from gpiozero import DigitalOutputDevice
from throttle import Throttle
from steering import Steering
from brake import Brake


# ---------------------------------------------------------------------------
# Mapping helpers (exactly the same maths you used previously)
# ---------------------------------------------------------------------------
def parse_packet(raw: str):
    """Return list[int] of six values or None if malformed."""
    try:
        vals = [int(x) for x in raw.split(",")]
        return vals if len(vals) == 6 else None
    except ValueError:
        return None


def convert_packet(vals):
    """Return mapped list[int] according to the rules in the brief."""
    t_raw, steer_raw, brake_raw, ea_raw, eb_raw, mode_raw = vals

    # throttle 1809-992  →  0-255  (reversed)
    offset = max(0, min(817, 1809 - t_raw))
    throttle = int(((817 - offset) / 817) * 255)

    # steering              >992:1, ==992:0, <992:-1
    steering = 1 if steer_raw > 992 else -1 if steer_raw < 992 else 0

    # brake                 >992→0  else 1
    brake = 0 if brake_raw > 992 else 1

    # e-stop A/B            <1809→1  else 0
    estop_a = 1 if ea_raw < 1809 else 0
    estop_b = 1 if eb_raw < 1809 else 0

    # mode                  172→1 (auto)  else 0 (remote)
    mode = 1 if mode_raw == 172 else 0

    return [throttle, steering, brake, estop_a, estop_b, mode]


# ---------------------------------------------------------------------------
# Global shared state
# ---------------------------------------------------------------------------
class Shared:
    def __init__(self):
        self.lock = threading.Lock()
        # sane defaults
        self.raw = [992, 992, 1809, 1809, 1809, 1809]
        self.mapped = convert_packet(self.raw)


state = Shared()

# An event other threads can watch
estop_event = threading.Event()


# ---------------------------------------------------------------------------
# Worker threads
# ---------------------------------------------------------------------------
def uart_listener(port="/dev/ttyAMA0"):
    ser = serial.Serial(port, 1200, timeout=1)
    while True:
        line = ser.readline().decode(errors="replace").strip()
        pkt = parse_packet(line)
        if pkt:
            with state.lock:
                state.raw = pkt
                state.mapped = convert_packet(pkt)


def safety_supervisor(actuators):
    """
    * Drops enable-pin GPIO-24 when e-stop asserted.
    * Applies brake, zeroes throttle, disables steering pulses.
    """
    drv_enable = actuators['throttle'].enable

    while True:
        with state.lock:
            t, s, b, ea, eb, mode = state.mapped
        estop_now = ea or eb
        if estop_now:
            if not estop_event.is_set():
                print(">>>  E-STOP TRIGGERED  <<<")
            estop_event.set()
            drv_enable.off()
            actuators['throttle'].disable()
            actuators['steering'].disable()
            actuators['brake'].apply()
        else:
            if estop_event.is_set():
                print("E-stop cleared – drive re-enabled")
            estop_event.clear()
            drv_enable.on()  # driver re-enable
        time.sleep(0.01)


def throttle_worker(th):
    while True:
        if estop_event.is_set():
            time.sleep(0.05)
            continue
        with state.lock:
            throttle_val, *_ = state.mapped
            mode = state.mapped[5]
        if mode == 0:                      # remote mode only
            th.set_wiper(throttle_val)
        else:
            th.set_wiper(0)  # autonomous: set this however you will later
        time.sleep(0.02)


def steering_worker(st):
    while True:
        if estop_event.is_set():
            time.sleep(0.05)
            continue
        with state.lock:
            steer_dir = state.mapped[1]
            mode = state.mapped[5]
        if mode == 0:
            st.set_direction(steer_dir)
        time.sleep(0.05)


def brake_worker(br):
    last = 0
    while True:
        with state.lock:
            brake_cmd = state.mapped[2]
        if brake_cmd != last:
            if brake_cmd:
                br.extend()
            else:
                br.retract()
            last = brake_cmd
        time.sleep(0.05)


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
def main():
    # Instantiate your classes
    throttle = Throttle()   # enable pin reused by supervisor
    steering = Steering()
    brake = Brake()

    actuators = dict(throttle=throttle,
                     steering=steering,
                     brake=brake)

    threads = [
        threading.Thread(target=uart_listener, daemon=True),
        threading.Thread(target=safety_supervisor,
                         args=(actuators,), daemon=True),
        threading.Thread(target=throttle_worker,
                         args=(throttle,), daemon=True),
        threading.Thread(target=steering_worker,
                         args=(steering,), daemon=True),
        threading.Thread(target=brake_worker,
                         args=(brake,), daemon=True),
    ]

    for t in threads:
        t.start()

    # Keep the main thread alive
    try:
        while True:
            with state.lock:
                raw = state.raw
                mapped = state.mapped
            print(f"RAW     : {raw}")
            print(f"MAPPED  : {mapped}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl-C – shutting down…" )


if __name__ == "__main__":
    main()
