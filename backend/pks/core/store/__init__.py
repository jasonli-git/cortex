"""Storage layer for the Core Knowledge Engine.

The engine talks to repository protocols (see interfaces.py); the SQLite
implementation (sqlite.py) is the V1 backend. Swapping to Postgres later means
writing a new module that satisfies the same protocols — nothing above the
store changes.
"""

from pks.core.store.sqlite import SqliteStore

__all__ = ["SqliteStore"]
