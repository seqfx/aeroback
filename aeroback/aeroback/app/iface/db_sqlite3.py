import os
import sqlite3

#-----------------------------------------------------------------------
import aeroback.diagnostics.diagnostics as _D


#-----------------------------------------------------------------------
# Open DB
#-----------------------------------------------------------------------
def db_open(filepath):
    # If DB doesn't exist on disk, do not create new one
    if not os.path.exists(filepath):
        return None

    # Try connecting
    try:
        conn = sqlite3.connect(filepath)
        return conn

    except Exception as e:
        _D.ERROR(
                __name__,
                "Error connecting to DB",
                'reason', str(e))
        return None


#-----------------------------------------------------------------------
# Create DB
#-----------------------------------------------------------------------
def db_create(filepath):
    return sqlite3.connect(filepath)


#-----------------------------------------------------------------------
# Close DB
#-----------------------------------------------------------------------
def db_close(conn):
    if conn:
        conn.close()
