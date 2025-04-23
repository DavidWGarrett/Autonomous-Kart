#!/usr/bin/env python3
"""
brake.py – linear-actuator brake driver (Pi 5)

Wiring (BCM):
    extend (forward)  → GPIO 16
    retract (reverse) → GPIO 17
"""
from time import sleep
from gpiozero import LED


class Brake:
    def __init__(self, fwd_pin: int = 16, rev_pin: int = 17):
        self._fwd = LED(fwd_pin)   # extend / apply brake
        self._rev = LED(rev_pin)   # retract / release brake
        print(f"[Brake] Initialised – EXT GPIO{fwd_pin}, RET GPIO{rev_pin}")

    # ---------- high-level actions ------------------------------------
    def extend(self, duration: float = 5.0):
        """Apply brake for *duration* seconds."""
        print("[Brake] Extending actuator …")
        self._rev.off()
        self._fwd.on()
        sleep(duration)
        self._fwd.off()

    def retract(self, duration: float = 5.0):
        """Release brake for *duration* seconds."""
        print("[Brake] Retracting actuator …")
        self._fwd.off()
        self._rev.on()
        sleep(duration)
        self._rev.off()

    def stop(self):
        """De-energise both outputs immediately."""
        self._fwd.off()
        self._rev.off()

    def apply(self):
        """Fallback apply method to match expected interface."""
        print("[Brake] Applying brake (via apply()) …")
        self.extend(1.0)

    # ---------- housekeeping / context manager ------------------------
    def close(self):
        self.stop()
        self._fwd.close()
        self._rev.close()
        print("[Brake] GPIOs released")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Stand-alone sanity test
if __name__ == "__main__":
    try:
        with Brake() as brk:
            brk.apply()
            sleep(2)
            brk.retract(3)
    except KeyboardInterrupt:
        pass

