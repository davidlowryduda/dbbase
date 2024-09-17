"""
models.py - a very light ORM-like model system

# **********************************************************************
#       This is models.py, part of dbbase.
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
import datetime
import sqlite3


from dbbase.core import DBBase, DatabaseConnectionError
from dbbase.plugin_manager import plugin_manager


# From https://docs.python.org/3/library/sqlite3.html#sqlite3-adapter-converter-recipes
def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()


def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()


def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())


def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return datetime.date.fromisoformat(val.decode())


def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())


def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.datetime.fromtimestamp(int(val))


sqlite3.register_adapter(datetime.date, adapt_date_iso)
sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_adapter(datetime.datetime, adapt_datetime_epoch)
sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("timestamp", convert_timestamp)


class Field:
    """
    Base class for model fields.
    """
    def __init__(self, field_type: str, primary_key: bool = False,
                 nullable: bool = True, unique: bool = False, default=None):
        self.field_type = field_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.unique = unique

    def get_definition(self):
        """
        Return the SQL column definition for this field.
        """
        field_def = f"{self.field_type}"
        if self.primary_key:
            field_def += " PRIMARY KEY"
        if self.unique:
            if not self.primary_key:
                field_def += " UNIQUE"
        if not self.nullable:
            field_def += " NOT NULL"
        if self.default is not None:
            field_def += f" DEFAULT {self.default}"
        return field_def

    def __str__(self):
        return f"FIELD {self.get_definition()}"


class IntegerField(Field):
    def __init__(self, **kwargs):
        super().__init__(field_type="INTEGER", **kwargs)


class TextField(Field):
    def __init__(self, **kwargs):
        super().__init__(field_type="TEXT", **kwargs)


class DatetimeField(Field):
    def __init__(self, **kwargs):
        super().__init__(field_type="DATETIME", **kwargs)


class DateField(Field):
    def __init__(self, **kwargs):
        super().__init__(field_type="DATE", **kwargs)


class ModelMeta(type):
    """
    Metaclass for models, used to automatically build schema from fields.
    """
    def __new__(cls, name, bases, attrs):
        fields = {name: field for name, field in attrs.items() if isinstance(field, Field)}
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._meta = {"fields": fields}
        return new_class


class Model(metaclass=ModelMeta):
    """
    Base class for all models.
    """
    table_name: str = None  # Override in subclasses

    @classmethod
    def create_table(cls, db: DBBase):
        """Create a table in the database based on the model's fields."""
        field_definitions = []
        for field_name, field_obj in cls._meta['fields'].items():
            field_definitions.append(f"{field_name} {field_obj.get_definition()}")
        field_definitions = ", ".join(field_definitions)
        query = f"CREATE TABLE IF NOT EXISTS {cls.table_name} ({field_definitions})"
        with db.transaction():
            db.execute(query)

    @classmethod
    def drop_table(cls, db: DBBase):
        """Drop the table associated with the model."""
        query = f"DROP TABLE IF EXISTS {cls.table_name}"
        with db.transaction():
            db.execute(query)

    @classmethod
    def create(cls, db: DBBase, **kwargs):
        """Insert a new record into the table."""
        plugin_manager.call_hook("before_save", db, **kwargs)
        fields = ", ".join(kwargs.keys())
        values = tuple(kwargs.values())
        placeholders = ", ".join("?" for _ in kwargs)
        query = f"INSERT INTO {cls.table_name} ({fields}) VALUES ({placeholders})"
        with db.transaction():
            db.execute(query, values)
        plugin_manager.call_hook("after_save", db, **kwargs)

    @classmethod
    def all(cls, db: DBBase):
        """Retrieve all records from the table."""
        query = f"SELECT * FROM {cls.table_name}"
        return db.fetch_all(query)

    @classmethod
    def get(cls, db: DBBase, **kwargs):
        """Retrieve a single record based on a query."""
        conditions = " AND ".join(f"{key} = ?" for key in kwargs)
        values = tuple(kwargs.values())
        query = f"SELECT * FROM {cls.table_name} WHERE {conditions} LIMIT 1"
        return db.fetch_one(query, values)

    @classmethod
    def update(cls, db: DBBase, where: dict, updates: dict):
        """Update records in the table."""
        instance_before = cls.get(db, **where)
        plugin_manager.call_hook("before_update", instance_before, updates, db)
        set_clause = ", ".join(f"{key} = ?" for key in updates)
        where_clause = " AND ".join(f"{key} = ?" for key in where)
        values = tuple(updates.values()) + tuple(where.values())
        query = f"UPDATE {cls.table_name} SET {set_clause} WHERE {where_clause}"
        with db.transaction():
            db.execute(query, values)
        instance_after = cls.get(db, **where)
        plugin_manager.call_hook("after_update", instance_before, instance_after, db)

    @classmethod
    def delete(cls, db: DBBase, **kwargs):
        """Delete records from the table."""
        instance = cls.get(db, **kwargs)
        plugin_manager.call_hook("before_delete", instance, db)
        conditions = " AND ".join(f"{key} = ?" for key in kwargs)
        values = tuple(kwargs.values())
        query = f"DELETE FROM {cls.table_name} WHERE {conditions}"
        with db.transaction():
            db.execute(query, values)
        plugin_manager.call_hook("after_delete", instance, db)
