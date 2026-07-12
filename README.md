# Must Inverter Data Handler

MustInverterDataHandler is Python application designed for interacting with Must Inverter PH1800 devices, enabling the retrieval of solar inverter data in JSON format. This script could work also on other similar inverter, I own just the PH1800 so feel free to try, nothing is going to explode, maybe...

## Features

- **Data Retrieval**: Must Inverter Data Handler allows you to effortlessly retrieve real-time data from your Must Inverter PH1800, including information on power generation, battery status, grid connectivity, and more. It provides this data in a structured JSON format for easy integration into other systems.

- **Command Configuration**: Must Inverter Data Handler offers flexibility through command configuration. You can enable or disable specific data retrieval commands, optimizing performance and focusing on the data you need most.

- **Data Writing (Future Expansion)**: While Must Inverter Data Handler excels at data retrieval, it's designed with future expansion in mind. It offers the flexibility to write data back to the inverter or other connected devices, enabling you to control and manage your solar power system remotely.

- **Open Source**: Must Inverter Data Handler is open source and hosted on GitHub, allowing the community to contribute, customize, and extend its functionality. Feel free to adapt it to your specific needs.

## Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)
- Serial library

### Installation

1. Clone the repository:

- `git clone https://github.com/thelabexpedition67/MustInverterDataHandler.git`
- `cd MustInverterDataHandler`

2. Install the required Python packages:

- `pip install -r requirements.txt`

### Configuration

1. Configure the serial port and command strings in the `main.py` script.

- `serial_port`: Specify the path to the serial port where your Must Inverter PH1800 is connected.
- `command_config`: Enable or disable specific data retrieval commands based on your requirements.

### .env 
```
# CONFIGURATION
MUST_PORT=COM3

# MYSQL DATABASE
MYSQL_HOST='db_ip'
MYSQL_DATABASE='db_name'
MYSQL_USER='db_user'
MYSQL_PASSWORD='user_password'
```
```
# (Optional) DATA_GATHER_INTERVAL_SECONDS
# Min: 10 seconds / Max: 1 hour, Defaul: 60 seconds
DATA_GATHER_INTERVAL_SECONDS=60
```


### Usage

Run the application:

- `python main.py`


### Output Example (2025-11-05)

```
{
    "ChargerWorkstate": 3,
    "MpptState": 0,
    "ChargingState": 0,
    "PvVoltage": "0.00",
    "BatteryVoltage": "27.50",
    "ChargerCurrent": "0.00",
    "ChargerPower": 0,
    "RadiatorTemperature": 22,
    "ExternalTemperature": 0,
    "BatteryRelay": 0,
    "PvRelay": 0,
    "ErrorMessage": 32,
    "WarningMessage": 0,
    "BattVolGrade": 24,
    "RatedCurrent": "60.00",
    "AccumulatedPower": "191.90",
    "AccumulatedTime": "00:00:00",
    "WorkState": 4,
    "AcVoltageGrade": 230,
    "RatedPower": 3200,
    "InverterBatteryVoltage": "27.40",
    "InverterVoltage": "228.90",
    "GridVoltage": "230.60",
    "BusVoltage": "434.30",
    "ControlCurrent": "0.00",
    "InverterCurrent": "0.00",
    "GridCurrent": "1.00",
    "LoadCurrent": "0.80",
    "PInverter": -40,
    "PGrid": -165,
    "PLoad": 127,
    "LoadPercent": 6,
    "SInverter": 0,
    "SGrid": 238,
    "Sload": 127,
    "Qinverter": 0,
    "Qgrid": 164,
    "Qload": 153,
    "InverterFrequency": "50.01",
    "GridFrequency": "50.01",
    "InverterMaxNumber": "0000",
    "CombineType": "0000",
    "InverterNumber": "0000",
    "AcRadiatorTemperature": 43,
    "TransformerTemperature": 56,
    "DcRadiatorTemperature": 0,
    "InverterRelayState": 0,
    "GridRelayState": 1,
    "LoadRelayState": 1,
    "N_LineRelayState": 0,
    "DCRelayState": 0,
    "EarthRelayState": 0,
    "AccumulatedChargerPower": "0.00",
    "AccumulatedDischargerPower": "413.80",
    "AccumulatedBuyPower": "681.70",
    "AccumulatedSellPower": "0.00",
    "AccumulatedLoadPower": "604.10",
    "AccumulatedSelf_usePower": "419.30",
    "AccumulatedPV_sellPower": "0.00",
    "AccumulatedGrid_chargerPower": "297.90",
    "SerialNumber": "FFFFFFFF",
    "HardwareVersion": "1.01.01",
    "SoftwareVersion": "2.25.34",
    "BattPower": -10,
    "BattCurrent": -5,
    "BattVoltageGrade": 24,
    "RatedPowerW": 3200,
    "CommunicationProtocolEdition": "1.04.14",
    "ArrowFlag": 622
}

```

## License

This project is licensed under the MIT License

## Acknowledgments

- pySerial - Python serial library for serial communication.

- I would like to extend my gratitude to the creators of the [Console Dumper for Must Power PH1800 Inverters](https://github.com/aquarat/must_inverter). Their project was needed on the development of this Python version. Below the reasons why I wanted to create this python version.

### Why this Python Version?

- **Faster Retrieval:** The Python version of the Must Inverter Data Handler offers significantly faster data retrieval, making it a great choice for applications where speed matters.

- **Easier Implementation:** Unlike the original C# project, which requires Mono on Linux, this Python version can be used without any additional dependencies, making it easier to set up and run on Linux systems.

I hope this Python implementation proves to be a valuable addition to the Must Inverter community.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests to improve this project.
