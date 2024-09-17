"""
query.py - CRUD and custom SQL queries

# **********************************************************************
#       This is query.py, part of dbbase.
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
from dbbase.core import DBBase, DatabaseConnectionError


class QueryBuilder:
    """
    A utility class to help build SQL queries programmatically.
    """
    def __init__(self, table_name):
        self.table_name = table_name
        self.filters = []
        self.filter_likes = []
        self.ordering = None

    def add_filter(self, **kwargs):
        """Add filters to the query."""
        for key, value in kwargs.items():
            self.filters.append((key, value))

    def add_filter_like(self, **kwargs):
        """Add LIKE filters to the query."""
        for key, value in kwargs.items():
            self.filter_likes.append((key, value))

    def set_order(self, field_name, descending=False):
        """Set ordering for the query."""
        direction = "DESC" if descending else "ASC"
        self.ordering = f"{field_name} {direction}"

    def build_select(self):
        """Build the SQL SELECT query based on filters and ordering."""
        query = f"SELECT * FROM {self.table_name}"
        if self.filters:
            filter_clauses = " AND ".join([f"{key} = ?" for key, _ in self.filters])
            query += f" WHERE {filter_clauses}"
        if self.filter_likes:
            filter_like_clauses = " AND ".join([f"{key} LIKE ?" for key, _ in
                                                self.filter_likes])
            query += f" WHERE {filter_like_clauses}"
        if self.ordering:
            query += f" ORDER BY {self.ordering}"
        value_tuple = tuple(value for _, value in self.filters)
        value_tuple += tuple("%" + value + "%" for _, value in self.filter_likes)
        return query, value_tuple


class QuerySet:
    """
    A class representing a collection of model instances that can be filtered,
    ordered, and retrieved from the database.
    """
    def __init__(self, model, db: DBBase):
        self.model = model
        self.db = db
        self.query_builder = QueryBuilder(model.table_name)

    def filter(self, **kwargs):
        """
        Add filtering conditions to the query.
        Example:
            Post.filter(title="My Title")
        """
        self.query_builder.add_filter(**kwargs)
        return self

    def filter_like(self, **kwargs):
        """
        Add loose (LIKE) filtering conditions to the query.
        Example:
            Post.filter_like="My Title")
        """
        self.query_builder.add_filter_like(**kwargs)
        return self

    def order_by(self, field_name, descending=False):
        """
        Set ordering for the query.
        Example:
            Post.order_by('title')
        """
        self.query_builder.set_order(field_name, descending)
        return self

    def all(self):
        """Fetch all records matching the query."""
        query, params = self.query_builder.build_select()
        return self.db.fetch_all(query, params)

    def get(self, **kwargs):
        """
        Fetch a single record matching the filter conditions.
        Example:
            Post.get(id=1)
        """
        self.filter(**kwargs)
        query, params = self.query_builder.build_select()
        return self.db.fetch_one(query, params)


# Extend the Model class to integrate querying functionality
class QueryableModel:
    """
    A mixin class that adds querying capabilities to models.
    """
    @classmethod
    def objects(cls, db: DBBase):
        """Return a QuerySet for the model."""
        return QuerySet(cls, db)
