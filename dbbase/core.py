"""
core.py - db interaction

# **********************************************************************
#       This is core.py, part of dbbase.
#       Copyright (c) 2024 David Lowry-Duda <david@lowryduda.com>
#       All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
#                 <http://www.gnu.org/licenses/>.
# **********************************************************************
"""
import sqlite3
from contextlib import contextmanager


from dbbase.plugin_manager import plugin_manager


class DatabaseConnectionError(Exception):
    """
    Custom exception for database connection errors.
    """
    pass


class DBBase:
    def __init__(self, db_path: str):
        """
        Initialize the DBBase class.

        :param db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """
        Establish a connection to the SQLite database.
        """
        try:
            self.connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            self.connection.row_factory = sqlite3.Row  # return results as dictionaries
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to connect to the database: {e}")

    def close(self):
        """
        Close the database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    @contextmanager
    def transaction(self):
        """
        Context manager for handling database transactions.

        Commits the transaction if everything succeeds; otherwise rolls back.
        """
        if self.connection is None:
            raise DatabaseConnectionError("Database connection is not established.")

        try:
            yield
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def execute(self, query: str, params: tuple = ()):
        """
        Execute a SQL query with optional parameters.

        :param query: SQL query to execute.
        :param params: Optional tuple of parameters for the query.
        :return: The cursor after executing the query.
        """
        if self.connection is None:
            raise DatabaseConnectionError("Database connection is not established.")

        plugin_manager.call_hook("before_query", query, params)

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to execute query: {e}")

    def fetch_one(self, query: str, params: tuple = ()):
        """
        Fetch a single record from the database.

        :param query: SQL query to execute.
        :param params: Optional tuple of parameters for the query.
        :return: A single record (as a dictionary) or None.
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple = ()):
        """
        Fetch all records from the database.

        :param query: SQL query to execute.
        :param params: Optional tuple of parameters for the query.
        :return: A list of records (each record as a dictionary).
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def execute_script(self, script: str):
        """
        Execute a SQL script (multiple statements).

        :param script: SQL script to execute.
        """
        if self.connection is None:
            raise DatabaseConnectionError("Database connection is not established.")

        try:
            self.connection.executescript(script)
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to execute script: {e}")
