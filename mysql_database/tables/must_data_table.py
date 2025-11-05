#mysql_database/tables/must_data_table.py

# Custom Modules
from mysql_database.mysql_connection_handler import MysqlConnectionHandler


class MustDataTable:
    def __init__(self, connection_handler: MysqlConnectionHandler):
        self._table_name = "must_data"
        self._connection_handler = connection_handler

    def initialize_table(self):
        create_table_query = (
            f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
            f"id INT AUTO_INCREMENT PRIMARY KEY, "
            f"timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, "
    
            # STATES
            f"ChargerWorkstate INT, "
            f"MpptState INT, "
            f"ChargingState INT, "
            f"WorkState INT, "
    
            # MAIN VOLTAGE AND CURRENCY
            f"PvVoltage FLOAT, "
            f"BatteryVoltage FLOAT, "
            f"InverterBatteryVoltage FLOAT, "
            f"InverterVoltage FLOAT, "
            f"GridVoltage FLOAT, "
            f"BusVoltage FLOAT, "
    
            f"ChargerCurrent FLOAT, "
            f"InverterCurrent FLOAT, "
            f"GridCurrent FLOAT, "
            f"LoadCurrent FLOAT, "
    
            # POWER (W)
            f"ChargerPower FLOAT, "
            f"PInverter FLOAT, "
            f"PGrid FLOAT, "
            f"PLoad FLOAT, "
            f"LoadPercent INT, "
    
            # COMPONENTS S / Q
            f"SInverter FLOAT, "
            f"SGrid FLOAT, "
            f"Sload FLOAT, "
            f"Qinverter FLOAT, "
            f"Qgrid FLOAT, "
            f"Qload FLOAT, "
    
            # FREQUENCIES
            f"InverterFrequency FLOAT, "
            f"GridFrequency FLOAT, "
    
            # TEMPERATURES
            f"RadiatorTemperature FLOAT, "
            f"AcRadiatorTemperature FLOAT, "
            f"TransformerTemperature FLOAT, "
            f"DcRadiatorTemperature FLOAT, "
            f"ExternalTemperature FLOAT, "
    
            # BATTERIES
            f"BattPower FLOAT, "
            f"BattCurrent FLOAT, "
            f"BattVolGrade INT, "
            f"BattVoltageGrade INT, "
    
            # ENERGY (accumulated)
            f"AccumulatedPower FLOAT, "
            f"AccumulatedChargerPower FLOAT, "
            f"AccumulatedDischargerPower FLOAT, "
            f"AccumulatedBuyPower FLOAT, "
            f"AccumulatedSellPower FLOAT, "
            f"AccumulatedLoadPower FLOAT, "
            f"AccumulatedSelf_usePower FLOAT, "
            f"AccumulatedPV_sellPower FLOAT, "
            f"AccumulatedGrid_chargerPower FLOAT, "
    
            # Relay / States
            f"BatteryRelay TINYINT, "
            f"PvRelay TINYINT, "
            f"InverterRelayState TINYINT, "
            f"GridRelayState TINYINT, "
            f"LoadRelayState TINYINT, "
            f"N_LineRelayState TINYINT, "
            f"DCRelayState TINYINT, "
            f"EarthRelayState TINYINT, "
    
            # Errors / Warning
            f"ErrorMessage INT, "
            f"WarningMessage INT, "
    
            # Other/Misc
            f"RatedPower INT, "
            f"RatedPowerW INT, "
            f"RatedCurrent FLOAT, "
            f"ArrowFlag INT "
    
            f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
        )

        with self._connection_handler.get_poll_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(create_table_query)
            connection.commit()

    def insert_data(self, data: dict):
        """
        Insert new data into must_data table.
        Accepts dict with data from inverter.
        """

        # Table fields
        columns = [
            "ChargerWorkstate", "MpptState", "ChargingState", "WorkState",
            "PvVoltage", "BatteryVoltage", "InverterBatteryVoltage", "InverterVoltage",
            "GridVoltage", "BusVoltage", "ChargerCurrent", "InverterCurrent",
            "GridCurrent", "LoadCurrent", "ChargerPower", "PInverter", "PGrid",
            "PLoad", "LoadPercent", "SInverter", "SGrid", "Sload", "Qinverter",
            "Qgrid", "Qload", "InverterFrequency", "GridFrequency",
            "RadiatorTemperature", "AcRadiatorTemperature", "TransformerTemperature",
            "DcRadiatorTemperature", "ExternalTemperature", "BattPower", "BattCurrent",
            "BattVolGrade", "BattVoltageGrade", "AccumulatedPower",
            "AccumulatedChargerPower", "AccumulatedDischargerPower",
            "AccumulatedBuyPower", "AccumulatedSellPower", "AccumulatedLoadPower",
            "AccumulatedSelf_usePower", "AccumulatedPV_sellPower",
            "AccumulatedGrid_chargerPower", "BatteryRelay", "PvRelay",
            "InverterRelayState", "GridRelayState", "LoadRelayState",
            "N_LineRelayState", "DCRelayState", "EarthRelayState", "ErrorMessage",
            "WarningMessage", "RatedPower", "RatedPowerW", "RatedCurrent", "ArrowFlag"
        ]

        # Select only those fields, which have data
        filtered_data = {k: data.get(k, None) for k in columns}

        # Creating SQL
        cols_str = ", ".join(filtered_data.keys())
        placeholders = ", ".join(["%s"] * len(filtered_data))

        sql = (
            f"INSERT INTO {self._table_name} "
            f"({cols_str}) VALUES ({placeholders})"
        )

        values = tuple(filtered_data.values())

        # Executing query
        with self._connection_handler.get_poll_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, values)
            connection.commit()
