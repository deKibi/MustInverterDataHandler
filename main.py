# main.py

# Standard Libraries
import importlib
from logging.handlers import TimedRotatingFileHandler
import logging
from pathlib import Path
from types import ModuleType
from typing import Optional

# Custom Modules
from mapper import *
from routines import *


LOGGER = logging.getLogger(__name__)


def configure_bootstrap_logging() -> None:
    """Configure console logging before application config is imported."""
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )


def load_application_config() -> ModuleType:
    """Import and validate the application configuration."""
    return importlib.import_module("config")


def configure_logging(log_level: int) -> None:
    """Configure console and daily rotating file logging."""
    logs_directory = Path(__file__).resolve().parent / "logs"
    logs_directory.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        filename=logs_directory / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        handlers=(console_handler, file_handler),
        force=True,
    )


class MustInverterDataHandler:
    def __init__(self, serial_port: str | None = None):
        # Define the serial port (change the port name as needed)
        # (Optional) Get the port from .env
        if serial_port is None:
            from config import MUST_PORT

            serial_port = MUST_PORT

        # serial_port (for Linux primarily) = "/dev/ttyUSB0"
        self._serial_port = serial_port

        # Define the configuration for command strings # Set to True or False as needed
        # This configuration can slow down the execution
        self._command_config = {
            "command_1_enabled": False,  # not really needed/implemented
            "command_2_enabled": False,
            "command_3_enabled": True,  # good data
            "command_4_enabled": False,
            "command_5_enabled": True,
            "command_6_enabled": True  # good data
        }

        # Construct the command strings based on the configuration
        charger_id = '04'
        inverter_id = '04'

        self._command_string_1 = f"{charger_id} 03 27 11 00 0A"
        self._command_string_2 = f"{charger_id} 03 27 75 00 18"
        self._command_string_3 = f"{charger_id} 03 3B 61 00 15"
        self._command_string_4 = f"{inverter_id} 03 4E 21 00 10"
        self._command_string_5 = f"{inverter_id} 03 4E 85 00 2C"
        self._command_string_6 = f"{inverter_id} 03 62 71 00 4F"

    def get_data(self) -> Optional[dict]:
        try:
            # Calculate the CRC value for the command
            command_bytes_1 = generate_crc(self._command_string_1)
            command_bytes_2 = generate_crc(self._command_string_2)
            command_bytes_3 = generate_crc(self._command_string_3)
            command_bytes_4 = generate_crc(self._command_string_4)
            command_bytes_5 = generate_crc(self._command_string_5)
            command_bytes_6 = generate_crc(self._command_string_6)

            # Perform other operations with the serial connection
            ser = serial.Serial(self._serial_port, baudrate=19200, timeout=1)
            ser.setRTS(True)
            responses = []

            if self._command_config["command_1_enabled"]:
                response_1 = get_part_arr(ser, command_bytes_1, 10, 20)
                time.sleep(0.03)
                responses.append(convert_partArr1_to_json(response_1))

            if self._command_config["command_2_enabled"]:
                response_2 = get_part_arr(ser, command_bytes_2, 24, 20)
                time.sleep(0.03)
                responses.append(convert_partArr2_to_json(response_2))

            if self._command_config["command_3_enabled"]:
                response_3 = get_part_arr(ser, command_bytes_3, 21, 20)
                time.sleep(0.03)
                responses.append(convert_partArr3_to_json(response_3))

            if self._command_config["command_4_enabled"]:
                response_4 = get_part_arr(ser, command_bytes_4, 16, 20)
                time.sleep(0.03)
                responses.append(convert_partArr4_to_json(response_4))

            if self._command_config["command_5_enabled"]:
                # === Getting EnergyUseMode  ===
                response_5 = get_part_arr(ser, command_bytes_5, 44, 20)
                time.sleep(0.03)
                responses.append(convert_partArr5_to_json(response_5))

            if self._command_config["command_6_enabled"]:
                response_6 = get_part_arr(ser, command_bytes_6, 79, 40)
                responses.append(convert_partArr6_to_json(response_6))

            # Close the serial connection when done
            ser.close()

            # Gather all data and convert it to dict
            merged_result_str: str = merge_json(responses)
            merged_result: dict = json.loads(merged_result_str)

            return merged_result

        except Exception:
            LOGGER.exception("Failed to get inverter data.")


def main():
    configure_bootstrap_logging()

    try:
        app_config = load_application_config()
    except ValueError as error:
        LOGGER.error("Application configuration is invalid: %s", error)
        raise SystemExit(1) from None

    configure_logging(log_level=app_config.LOG_LEVEL)

    # Import application services only after configuration validation.
    from energy_mode_control.energy_mode_controller import (
        handle_energy_mode_control,
    )
    from mysql_database import MysqlConnectionHandler
    from mysql_database.tables import MustDataTable

    LOGGER.info("Application configuration loaded and validated.")
    LOGGER.info(app_config.get_startup_configuration_summary())
    app_config.log_configuration_warnings()
    LOGGER.info("Initializing application.")

    # 1. Create instance of class MustInverterDataHandler
    must_inverter_data_handler = MustInverterDataHandler(
        serial_port=app_config.MUST_PORT,
    )

    # 2. Initialize MySQL database connection
    LOGGER.info("Connecting to MySQL. This may take some time.")
    mysql_connection_handler = MysqlConnectionHandler()
    mysql_connection_handler.initialize_connection(
        db_host=app_config.MYSQL_HOST,
        db_port=app_config.MYSQL_PORT,
        db_name=app_config.MYSQL_DATABASE,
        db_user=app_config.MYSQL_USER,
        db_password=app_config.MYSQL_PASSWORD,
        pool_name="must_python_worker",
        pool_size=2,
    )
    LOGGER.info("Initializing MySQL tables. This may take some time.")
    must_data_table = MustDataTable(connection_handler=mysql_connection_handler)
    must_data_table.initialize_table()

    # 3. Read & save data
    LOGGER.info("Starting inverter data collection.")
    LOGGER.info(
        "Data gathering interval is set to %d seconds.",
        app_config.DATA_GATHER_INTERVAL_SECONDS,
    )
    if app_config.ENABLE_AUTO_SWITCH:
        LOGGER.info("Time-based energy mode auto-switch is enabled.")
    if app_config.ENABLE_GRID_OUTAGE_AUTO_SWITCH:
        LOGGER.info("Grid outage energy mode auto-switch is enabled.")

    while True:
        # 1. Get data
        must_data = must_inverter_data_handler.get_data()
        LOGGER.debug("Inverter data received: %s", must_data)

        # 2. Check & insert data
        if must_data and len(must_data) > 2:
            must_data_table.insert_data(data=must_data)
            LOGGER.info("Inverter data inserted into the database.")

            # 3. Handle optional energy mode control
            handle_energy_mode_control(must_data=must_data)
        else:
            LOGGER.warning("Unable to get data from the inverter.")

        LOGGER.info(
            "Sleeping for %d seconds.",
            app_config.DATA_GATHER_INTERVAL_SECONDS,
        )
        time.sleep(app_config.DATA_GATHER_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()
