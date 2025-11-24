# energy_mode_test.py

# Standard Libraries
import time
import os

# Third-party Libraries
import serial
from dotenv import load_dotenv

# Custom Modules
from routines import generate_crc


def build_energy_mode_command(mode: int) -> bytes:
    """
    Build Modbus RTU frame:
    Slave 0x04, Function 0x10 (Write Multiple Registers),
    Address 0x4E8D, 1 register, value = mode (1..4)
    """
    if mode not in (1, 2, 3, 4):
        raise ValueError("Mode must be 1=SBU, 2=SUB, 3=UTI, 4=SOL")

    slave_id = 0x04
    func = 0x10
    addr_hi, addr_lo = 0x4E, 0x8D     # 0x4E8D
    qty_hi, qty_lo = 0x00, 0x01       # 1 register
    byte_count = 0x02

    # value = 0x0001 / 0x0002 / 0x0003 / 0x0004
    value_hi = (mode >> 8) & 0xFF
    value_lo = mode & 0xFF

    # Без CRC:
    # 04 10 4E 8D 00 01 02 00 01  (для mode=1)
    hex_str = f"{slave_id:02X} {func:02X} {addr_hi:02X} {addr_lo:02X} " \
              f"{qty_hi:02X} {qty_lo:02X} {byte_count:02X} " \
              f"{value_hi:02X} {value_lo:02X}"

    # generate_crc очікує HEX-string, додає CRC як 2 останні байти
    frame = generate_crc(hex_str)
    return bytes(frame)


def send_energy_mode(port: str, mode: int):
    frame = build_energy_mode_command(mode)
    print("Sending frame:", frame.hex(" ").upper())

    ser = serial.Serial(port, baudrate=19200, timeout=1)
    ser.setRTS(True)
    ser.write(frame)

    # дати інвертору трошки часу
    time.sleep(0.2)

    # відповіді може й не бути (або буде echo/ack) — зчитаємо все, що є
    resp = ser.read(ser.in_waiting or 1)
    ser.close()

    print("Response raw:", resp)
    return resp


if __name__ == '__main__':
    print("Will send energy mode command in 3 seconds...")
    time.sleep(3)

    load_dotenv()
    MUST_PORT = os.getenv("MUST_PORT", "/dev/ttyUSB0")

    #   1 = SBU, 2 = SUB, 3 = UTI, 4 = SOL
    send_energy_mode(MUST_PORT, mode=1)

    print(f"Command sent on port {MUST_PORT}.")
