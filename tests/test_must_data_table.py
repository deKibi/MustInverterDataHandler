# tests/test_must_data_table.py

# Standard Libraries
import unittest
from unittest.mock import MagicMock

# Custom Modules
from mysql_database.tables.must_data_table import MustDataTable


class MustDataTableTestCase(unittest.TestCase):
    def test_get_recent_solar_switch_data_returns_cursor_rows(self):
        rows = [{"timestamp": "value"}]
        cursor = MagicMock()
        cursor.fetchall.return_value = rows
        connection = MagicMock()
        connection.cursor.return_value = cursor
        connection_context = MagicMock()
        connection_context.__enter__.return_value = connection
        connection_handler = MagicMock()
        connection_handler.get_poll_connection.return_value = (
            connection_context
        )
        table = MustDataTable(connection_handler=connection_handler)

        result = table.get_recent_solar_switch_data(lookback_minutes=10)

        self.assertEqual(rows, result)
        connection.cursor.assert_called_once_with(dictionary=True)
        cursor.execute.assert_called_once()
        self.assertEqual((10,), cursor.execute.call_args.args[1])
        cursor.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
