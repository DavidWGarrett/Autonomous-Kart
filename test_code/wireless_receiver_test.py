import serial

# Configuration
PORT = "/dev/ttyACM0"
BAUD = 115200

def main():
    try:
        with serial.Serial(PORT, BAUD, timeout=1) as ser:
            print(f"Listening on {PORT} at {BAUD} baud...\n")
            while True:
                # Read one line (until \n)
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                # Print raw line
                print("Raw:", line)

                # Optional: parse CSV format
                parts = line.split(',')
                if len(parts) == 9:
                    try:
                        values = list(map(int, parts))
                        print("Parsed:", values)
                    except ValueError:
                        print("Non-integer value received")
                else:
                    print("Unexpected format")

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nExiting by user")

if __name__ == "__main__":
    main()
