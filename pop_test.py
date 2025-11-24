# pop_test.py

# Standard Libraries
import time
import os

# Third-party Libraries
import serial
from dotenv import load_dotenv

# Custom Modules
from routines import generate_crc


# Map numeric mode → ASCII code digit
ascii_digit = {
    1: "31",  # '1'
    2: "32",  # '2'
    3: "33",  # '3'
    4: "34",  # '4'
}


def send_pop_command(port: str, mode: int):
    """
    Sends POPxx command to Must inverter.
    mode: 1=SBU, 2=SUB, 3=UTI, 4=SOL.
    """

    if mode not in ascii_digit:
        raise ValueError("Mode must be 1, 2, 3 or 4")

    # Build ASCII POP command in HEX
    command_hex = f"50 4F 50 30 {ascii_digit[mode]}"

    # Add CRC
    command_bytes = generate_crc(command_hex)

    print("Sending bytes:", command_bytes.hex().upper())

    try:
        ser = serial.Serial(port, baudrate=19200, timeout=1)
        ser.setRTS(True)

        ser.write(command_bytes)
        time.sleep(0.1)

        # Read response (usually something like "(ACK" or similar)
        resp = ser.read(ser.in_waiting or 1)
        ser.close()

        print("Response raw:", resp)
        return resp

    except Exception as e:
        print("Error sending POP command:", e)


def send_pop_ascii(port: str, mode: int):
    if mode not in [1,2,3,4]:
        print("Mode must be 1-4")
        return

    cmd = f"POP0{mode}\r"     # ASCII command
    print("Sending:", repr(cmd))

    try:
        ser = serial.Serial(port, baudrate=2400, timeout=1)  # ❗ тут 2400 для ASCII, НЕ 19200
        ser.write(cmd.encode('ascii'))

        time.sleep(0.2)
        resp = ser.read(ser.in_waiting or 1)
        ser.close()

        print("Response:", resp)
    except Exception as e:
        print("Error:", e)



if __name__ == '__main__':
    # === DEBUG ===
    print("Sending POP command in 3 seconds!")
    time.sleep(3)

    # Start
    load_dotenv()
    MUST_PORT = os.getenv("MUST_PORT", "/dev/ttyUSB0")

    # Try №1. Send POP command (fail)
    # send_pop_command(port=MUST_PORT, mode=1)  # SBU

    # Try №2. Send POP ASCII command
    send_pop_ascii(port="COM3", mode=1)  # SBU

    print(f"POP command on port {MUST_PORT} sent.")
