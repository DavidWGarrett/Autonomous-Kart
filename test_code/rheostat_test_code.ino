/*
PINS

Hardware Assumptions

MCP4162 is powered at 5 V with a shared ground to the Arduino and the RC receiver.
MCP4162 pins:
VDD → 5 V, VSS → GND
CS → D10, SCK → D13, SDI → D11, SDO → D12
WP → GND (write‐protect disabled)
SHDN → 5 V (pot always active)
Rheostat Mode: use P0W and P0B as your two terminals to the throttle input; leave P0A floating.
The R88 V2 receiver PWM signal wire goes to Arduino digital pin 2 (configured as INPUT).
The signal is a standard hobby servo pulse: ~1000 µs (low) to 2000 µs (high).
For safety, be sure the throttle/motor controller setup is correct for a 5 kΩ range pot or as recommended by your controller’s documentation.
*/

#include <SPI.h>

// MCP4162 connections
const int MCP4162_CS = 10;    // Chip Select pin for the MCP4162

// Receiver (PWM) input pin
const int RECEIVER_PIN = 2;

// We want: 
//   at 1500 µs => wiper = 0
//   at 2000 µs => wiper = 50
// Anything below 1500 => clamp to 0
// Anything above 2000 => clamp to 50

void setup() {
  // Optional serial monitor for debugging
  Serial.begin(9600);

  // Initialize SPI
  SPI.begin();

  // Configure the MCP4162 CS pin
  pinMode(MCP4162_CS, OUTPUT);
  digitalWrite(MCP4162_CS, HIGH); // Deselect by default

  // Pin for reading the RC servo pulse
  pinMode(RECEIVER_PIN, INPUT);

  // Optionally configure SPI speed & mode.
  // The MCP4162 supports up to 10 MHz (5 V), but we can start slower
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));

  // Set an initial "safe" throttle = 0
  setWiper(0);
  delay(500);
}

// Function to write an 8-bit wiper value to the MCP4162's volatile register
// Range is 0-255, but we only plan to use 0-50 in this example
void setWiper(byte value) {
  digitalWrite(MCP4162_CS, LOW);

  // Command byte: 0x00 => "Write data to Wiper 0 (Volatile)"
  SPI.transfer(0x00);

  // Data byte: the wiper position
  SPI.transfer(value);

  digitalWrite(MCP4162_CS, HIGH);

  // Debug print
  Serial.print("Wiper set to: ");
  Serial.println(value);
}

void loop() {
  // Measure the width of the incoming pulse (HIGH state) in microseconds
  // Timeout 25000 µs (~25 ms) to avoid blocking if no signal
  unsigned long pulseWidth = pulseIn(RECEIVER_PIN, HIGH, 25000);

  // If pulseWidth == 0, we didn't receive a valid pulse within 25 ms
  if(pulseWidth == 0) {
    // No signal (fail-safe) => set to 0 or do nothing. 
    // For safety, let's keep it at 0.
    setWiper(0);
  }
  else {
    // Map 1500-2000 µs => 0-50
    // Values below 1500 clamp to 0, above 2000 clamp to 50
    int wiperValue = map(pulseWidth, 1500, 2000, 0, 50);

    // Constrain to ensure it's within 0..50
    wiperValue = constrain(wiperValue, 0, 50);

    setWiper((byte)wiperValue);
  }

  // Adjust loop delay to match how often you want to sample the RC pulse
  delay(20);
}