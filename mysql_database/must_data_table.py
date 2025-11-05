#mysql_database/tables/must_data_table.py

# Custom Modules
from mysql_connection_handler import MysqlConnectionHandler


class MustDataTable:
    def __init__(self, mysql_con_handler: MysqlConnectionHandler):
        self._table_name = "must_data"
        self._mysql_con_handler = mysql_con_handler

    def create_table_if_not_exists(self):
        create_table_query = (
            f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
            f")"
        )

        with self._mysql_con_handler.get_poll_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(create_table_query)
            connection.commit()
