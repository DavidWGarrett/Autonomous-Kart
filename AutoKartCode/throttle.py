#!/usr/bin/env python3
"""
throttle.py – MCP4162 digital-potentiometer driver (uses gpiozero)

Wiring (BCM numbering)
────────────────────────────────────────────────────────────
MCP4162   →  Pi 5
────────────────────────────────────────────────────────────
SCLK      →  GPIO 11  (SPI0 SCLK)
MOSI      →  GPIO 10  (SPI0 MOSI)
MISO      →  —        (not used for simple writes)
CS (̅SS̅)   →  GPIO 27  (any free GPIO, active-low)
EN (OE)   →  GPIO 24  (active-high enable for your H-bridge / ESC / etc.)
VSS/GND   →  Pi GND
VDD       →  3V3
────────────────────────────────────────────────────────────
"""

import time
import spidev
from gpiozero import DigitalOutputDevice

class Throttle:
    """
    Thin wrapper around an MCP4162 digital potentiometer used as a throttle.

    Methods
    -------
    enable_output(True/False)
        Enables or disables the analog side (GPIO 24).
    set_wiper(value)
        Sets the wiper 0-255.
    disable()
        Disables the throttle (adds missing method for safety supervisor).
    close()
        Releases GPIOs and closes the SPI device.
    """

    def __init__(
        self,
        spi_bus: int = 0,
        spi_device: int = 0,
        cs_pin: int = 27,
        en_pin: int = 24,
        spi_hz: int = 1_000_000,
    ):
        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.mode = 0b00
        self.spi.max_speed_hz = spi_hz

        # GPIO (gpiozero)
        self.cs = DigitalOutputDevice(cs_pin, active_high=False, initial_value=True)
        self.enable = DigitalOutputDevice(en_pin, active_high=True, initial_value=False)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def enable_output(self, state: bool = True) -> None:
        """Assert or de-assert the enable pin (GPIO 24)."""
        if state:
            self.enable.on()
        else:
            self.enable.off()

    def set_wiper(self, value: int) -> None:
        """Write an 8-bit value to the wiper (clamped 0-255)."""
        value = max(0, min(255, int(value)))
        cmd = [0x00, value]  # 0x00 = Write P0 volatile register
        self.cs.on()               # CS active (low)
        self.spi.xfer2(cmd)
        self.cs.off()              # CS inactive (high)
        print(f"[Throttle] Wiper set to {value}")

    def disable(self) -> None:
        """Disable throttle safely by turning off output and zeroing the wiper."""
        print("[Throttle] Disabling throttle")
        self.set_wiper(0)
        self.enable_output(False)

    # ------------------------------------------------------------------
    # Context-manager helpers (so you can use `with Throttle() as th:`)
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Gracefully release everything."""
        try:
            self.disable()
            self.cs.off()
        finally:
            self.cs.close()
            self.enable.close()
            self.spi.close()

    def __enter__(self):
        """`with Throttle() as th:` support."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

# ----------------------------------------------------------------------
# Stand-alone test when executed directly
# ----------------------------------------------------------------------
if __name__ == "__main__":
    with Throttle() as throttle:
        throttle.enable_output(True)
        print("Throttle enabled")
        print("Setting midpoint (160) for 2 s")
        throttle.set_wiper(160)
        time.sleep(2.0)

        print("Slow sweep 0 → 255 → 0 …")
        for val in range(0, 256, 32):
            throttle.set_wiper(val)
            time.sleep(0.5)
        for val in range(255, -1, -32):
            throttle.set_wiper(val)
            time.sleep(0.5)

        print("Done – throttle disabled")

