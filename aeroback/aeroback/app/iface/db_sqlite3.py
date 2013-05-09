import os
import sqlite3

#-----------------------------------------------------------------------
#import aeroback.diagnostics.diagnostics as _D


#-----------------------------------------------------------------------
# Open DB
#-----------------------------------------------------------------------
def db_open(filepath):
    if os.path.exists(filepath):
        return sqlite3.connect(filepath)
    else:
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
