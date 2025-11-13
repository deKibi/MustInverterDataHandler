# main.py

# Standard Libraries
from typing import Optional
import time  # Import the time module for sleep
import os
from routines import *
from mapper import *

# Third-party Libraries
from dotenv import load_dotenv

# Custom Modules
from mysql_database import MysqlConnectionHandler
from mysql_database.tables import MustDataTable


class MustInverterDataHandler:
    def __init__(self):
        # Define the serial port (change the port name as needed)
        # (Optional) Get the port from .env
        load_dotenv()  # Load vars from .env into our environment
        # serial_port = "/dev/ttyUSB0"
        self._serial_port = os.getenv("MUST_PORT", "/dev/ttyUSB0")  # default, if not found

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

        except Exception as e:
            print("Error while getting inverter's data:", str(e))


def main():
    print("Initializing project.")
    load_dotenv()  # load vars from .env into our environment

    # 1. Create instance of class MustInverterDataHandler
    must_inverter_data_handler = MustInverterDataHandler()

    # 2. Initialize MySQL database connection
    print("Connecting to MySQL, it may take some time, please wait...")
    mysql_connection_handler = MysqlConnectionHandler()
    mysql_connection_handler.initialize_connection(
        db_host=os.getenv("MYSQL_HOST", "localhost"),
        db_name=os.getenv("MYSQL_DATABASE", "must_data"),
        db_user=os.getenv("MYSQL_USER", "root"),
        db_password=os.getenv("MYSQL_PASSWORD", ""),
        pool_name="must_python_worker",
        pool_size=2
    )
    print("Initializing MySQL tables, it may take some time, please wait...")
    must_data_table = MustDataTable(connection_handler=mysql_connection_handler)
    must_data_table.initialize_table()

    # 3. Read & save data
    print("Getting inverter's data...")
    get_inverter_data_delay = os.getenv("DATA_GATHER_INTERVAL_SECONDS", default=60) # seconds
    if get_inverter_data_delay < 10:
        get_inverter_data_delay = 10  # min interval 10 seconds
    elif get_inverter_data_delay > 3600:
        get_inverter_data_delay = 3600  # max internal 1 hour
    while True:
        # 1. Get data
        must_data = must_inverter_data_handler.get_data()
        print("Inverter's data received:", must_data)

        # 2. Check & insert data
        if must_data and len(must_data) > 2:
            must_data_table.insert_data(data=must_data)
            print("Data inserted into the database.")
        else:
            print("Unable to get data from the inverter.")

        print(f"\nSleeping for {get_inverter_data_delay} seconds...")
        time.sleep(get_inverter_data_delay)

if __name__ == '__main__':
    main()
