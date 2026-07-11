# mysql_database/mysql_connection_handler.py

# Standard Libraries
from contextlib import contextmanager
import logging
import sys
from typing import Optional

# Third-party Libraries
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import MySQLConnection


logger = logging.getLogger(__name__)


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
            logger.info(
                "MySQL connection pool with the name %s and size %s "
                "successfully created.",
                pool_name,
                pool_size,
            )
        except Exception as e:
            logger.exception(
                "Unable to connect to MySQL database %s at %s via user %s: %s",
                db_name,
                db_host,
                db_user,
                e,
            )
            sys.exit(1)

    @contextmanager
    def get_poll_connection(self) -> MySQLConnection:
        if self._connection_pool is None:
            logger.warning(
                "MySQL connection pool is empty: pool not established yet or "
                "you used an instance of class where the pool is not established."
            )

        connection = self._connection_pool.get_connection()
        try:
            yield connection
        finally:
            connection.close()
