# energy_mode_control/energy_mode_switcher.py

# Standard Libraries
import logging
import time

# Third-Party Libraries
import serial

# Custom Modules
from config import EnergyMode, MUST_PORT
from routines import generate_crc


logger = logging.getLogger(__name__)


def build_energy_mode_command(mode: EnergyMode) -> bytes:
    """
    Build a Modbus RTU command for changing the inverter energy mode.

    Frame:
        Slave: 0x04
        Function: 0x10 — Write Multiple Registers
        Register address: 0x4E8D
        Register quantity: 1
        Register value: energy mode code

    Energy modes:
        1 = SBU
        2 = SUB
        3 = UTI
        4 = SOL

    Args:
        mode: Target inverter energy mode.

    Returns:
        Complete Modbus RTU frame with CRC.
    """
    if not isinstance(mode, EnergyMode):
        raise TypeError(
            "mode must be an EnergyMode enum value"
        )

    slave_id = 0x04
    function_code = 0x10

    address_high = 0x4E
    address_low = 0x8D

    quantity_high = 0x00
    quantity_low = 0x01

    byte_count = 0x02

    mode_value = mode.value

    value_high = (mode_value >> 8) & 0xFF
    value_low = mode_value & 0xFF

    hex_string = (
        f"{slave_id:02X} "
        f"{function_code:02X} "
        f"{address_high:02X} "
        f"{address_low:02X} "
        f"{quantity_high:02X} "
        f"{quantity_low:02X} "
        f"{byte_count:02X} "
        f"{value_high:02X} "
        f"{value_low:02X}"
    )

    frame = generate_crc(hex_string)

    return bytes(frame)


def switch_energy_mode(
    target_mode: EnergyMode,
    port: str = MUST_PORT,
) -> bytes:
    """
    Send an energy mode switch command to the inverter.

    Args:
        target_mode: Target inverter energy mode.
        port: Serial port used to communicate with the inverter.

    Returns:
        Raw response received from the inverter.
    """
    frame = build_energy_mode_command(target_mode)

    logger.info(
        "Switching inverter energy mode to %s (%s).",
        target_mode.name,
        target_mode.value,
    )
    logger.info("Sending frame: %s", frame.hex(" ").upper())

    with serial.Serial(
        port=port,
        baudrate=19200,
        timeout=1,
        write_timeout=1,
    ) as serial_connection:
        serial_connection.setRTS(True)
        serial_connection.write(frame)
        serial_connection.flush()

        # Give the inverter some time to process the command.
        time.sleep(0.2)

        response = serial_connection.read(
            serial_connection.in_waiting or 1
        )

    logger.info("Response raw: %r", response)

    return response


if __name__ == "__main__":
    # print("Will send energy mode command in 3 seconds...")
    # time.sleep(3)
    #
    # load_dotenv()
    # MUST_PORT = os.getenv("MUST_PORT", "/dev/ttyUSB0")
    #
    # #   1 = SBU, 2 = SUB, 3 = UTI, 4 = SOL
    # send_energy_mode(MUST_PORT, mode=1)
    #
    # print(f"Command sent on port {MUST_PORT}.")
    print("debugging energy_mode_switcher.py")

    test_target_mode = EnergyMode.SBU

    test_target_mode_name = test_target_mode.name
    test_target_mode_code = test_target_mode.value

    print("Target switch mode:", test_target_mode_name)
    print("Object Type:", type(test_target_mode_name))

    print("Target mode code:", test_target_mode_code)
    print("Object Type:", type(test_target_mode_code))

    print("Will send energy mode command in 3 seconds...")
    time.sleep(3)

    response = switch_energy_mode(
        target_mode=test_target_mode,
    )

    print(
        f"{test_target_mode.name} command sent "
        f"on port {MUST_PORT}."
    )
    print("Response:", response)
