"""
Serial Diagnostic Tool
══════════════════════
Use this to verify the two-way UART connection between the Pi and Arduino.

1.  Sends a command (e.g., 'S' for Stop).
2.  Waits and prints exactly what the Arduino says back.
"""

import serial
import time
import sys

# Try common Pi UART ports
PORTS = ['/dev/serial0', '/dev/ttyAMA0', '/dev/ttyS0', '/dev/ttyUSB0']
BAUD = 9600

def test_port(port):
    print(f"\n--- Testing {port} ---")
    try:
        ser = serial.Serial(port, BAUD, timeout=2)
        time.sleep(2)  # Wait for Arduino reset if USB, or just settle
        
        # Test command: 'S' (Stop) should return "STOP"
        print(f"Sending 'S' to {port}...")
        ser.write(b"S\n")
        ser.flush()
        
        # Read response
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        if response:
            print(f"✅ SUCCESS! Arduino says: '{response}'")
            return True
        else:
            print(f"⚠️  SENT but NO RESPONSE. Check TX/RX wiring and shared Ground.")
            return False
            
    except Exception as e:
        print(f"❌ FAILED to open port: {e}")
        return False

if __name__ == "__main__":
    found = False
    for p in PORTS:
        if test_port(p):
            found = True
            print(f"\n✨ USE THIS PORT IN config.py: SERIAL_PORT = '{p}'")
            break
            
    if not found:
        print("\n❌ Could not find a working Arduino connection.")
        print("DIAGNOSTIC STEPS:")
        print("1. Are Pi TX (Pin 8) and Arduino RX (Pin 0) connected?")
        print("2. Are Pi RX (Pin 10) and Arduino TX (Pin 1) connected (via divider)?")
        print("3. Do Pi and Arduino share a common GROUND (GND)? (Crucial!)")
        print("4. Is Serial Console disabled in sudo raspi-config?")
