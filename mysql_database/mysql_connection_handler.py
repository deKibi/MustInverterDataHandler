# mysql_database/mysql_connection_handler.py

# Standard Libraries
from typing import Optional
from contextlib import contextmanager
import sys

# Third-party Libraries
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import MySQLConnection


class MysqlConnectionHandler:
    def __init__(self):
        self._connection_pool: Optional[MySQLConnectionPool] = None

    def initialize_connection(
            self,
            db_host: str,
            db_name: str,
            db_user: str,
            db_password: str,
            pool_name:str,
            pool_size: int
    ) -> Optional[MySQLConnectionPool]:
        try:
            new_pool = MySQLConnectionPool(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                pool_name=pool_name,
                pool_size=pool_size
            )
            self._connection_pool = new_pool
            print(f"MySQL connection pool with the name {pool_name} and size {pool_size} successfully created.")
        except Exception as e:
            print(f"Unable to connect to MySQL database {db_name} at {db_host} via user {db_user}: {e}")
            sys.exit(1)

    @contextmanager
    def get_poll_connection(self) -> MySQLConnection:
        if self._connection_pool is None:
            print("MySQL connection pool is empty: pool not established yet or you used an instance of class where the pool is not established.")

        connection = self._connection_pool.get_connection()
        try:
            yield connection
        finally:
            connection.close()
