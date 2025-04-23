#!/usr/bin/env python3
"""
steering.py  –  Jog-left / jog-right steering class for Pi 5
────────────────────────────────────────────────────────────
GPIO wiring (BCM numbers)

    19  →  LIO1   – Enable (kept HIGH while class is alive)
    12  →  LIO2   – Fault-Reset (1 ms pulse after *every* jog)
    26  →  LIO3   – Jog-NEG   (turn LEFT when pulsed)
    22  →  LIO4   – Jog-POS   (turn RIGHT when pulsed)

Direction mapping used by `set_direction()`:
    +1  →  left   (Jog-NEG)
     0  →  stop   (no jog pins active)
    –1  →  right  (Jog-POS)
"""
from time import sleep
from gpiozero import DigitalOutputDevice


class Steering:
    """Steering controller that understands –1 / 0 / +1 commands."""

    # --- timings (seconds) -------------------------------------------------
    JOG_PULSE = 0.20        # length of jog command
    FAULT_PULSE = 0.001     # 1 ms reset pulse

    def __init__(
        self,
        enable_pin: int = 19,
        fault_pin: int = 12,
        jog_neg_pin: int = 26,
        jog_pos_pin: int = 22,
    ):
        # Outputs
        self._enable = DigitalOutputDevice(enable_pin, active_high=True, initial_value=False)
        self._fault  = DigitalOutputDevice(fault_pin,  active_high=True, initial_value=False)
        self._jneg   = DigitalOutputDevice(jog_neg_pin, active_high=True, initial_value=False)
        self._jpos   = DigitalOutputDevice(jog_pos_pin, active_high=True, initial_value=False)

        # Latch the drive ON immediately
        self._enable.on()
        print(f"[Steering] Enabled (GPIO{enable_pin}=HIGH)")

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def set_direction(self, direction: int):
        """
        direction = +1 → left
        direction =  0 → stop
        direction = –1 → right
        """
        if direction not in (-1, 0, 1):
            raise ValueError("direction must be -1, 0 or 1")

        # ensure both jog pins low first
        self._jneg.off()
        self._jpos.off()

        if direction == 1:       # left
            print("[Steering] Jog LEFT")
            self._jneg.on()
            sleep(self.JOG_PULSE)
            self._jneg.off()

        elif direction == -1:    # right
            print("[Steering] Jog RIGHT")
            self._jpos.on()
            sleep(self.JOG_PULSE)
            self._jpos.off()
        else:
            print("[Steering] Centre / stop")

        # always issue a brief fault-reset pulse
        self._pulse_fault_reset()

    def close(self):
        """Release GPIOs cleanly."""
        self._enable.off()
        self._fault.off()
        self._jneg.off()
        self._jpos.off()

        for dev in (self._enable, self._fault, self._jneg, self._jpos):
            dev.close()
        print("[Steering] GPIOs released")
    
    def disable(self):
        print("[Steering] Disable (no-op)")

    def enable(self):
        print("[Steering] Enable (no-op)")


    # Support with-statement usage
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #
    def _pulse_fault_reset(self):
        """1 ms high-pulse on the fault-reset line (LIO2)."""
        self._fault.on()
        sleep(self.FAULT_PULSE)
        self._fault.off()
        print("[Steering] Fault-reset pulse")


# ---------------------------------------------------------------------- #
# Stand-alone demo                                                       #
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        with Steering() as steer:
            steer.set_direction(+1)      # left
            sleep(1)
            steer.set_direction(-1)      # right
            sleep(1)
            steer.set_direction(0)       # centre
    except KeyboardInterrupt:
        pass
