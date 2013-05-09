import os

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import iface.db_sqlite3 as db_iface

'''
Versioned File Tracker DB maintainer:
    - keeps track of file versions

Required modules:
    -

Children modules:
    -
'''


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self, date_str, date_int, dir_db, filename, filepath):
        super(Model, self).__init__()
        self.date_str = date_str
        self.date_int = date_int
        self.dir_db = dir_db
        self.filename = filename
        self.filepath = filepath

    def debug_vars(self):
        return [
                'date_str', self.date_str,
                'date_int', self.date_int,
                'dir_db', self.dir_db,
                'filename', self.filename,
                'filepath', self.filepath
                ]


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model

        self.db_conn = None

    def debug_vars(self):
        return [
                'db_conn', self.db_conn
                ]


#-----------------------------------------------------------------------
# Connect or initialize Stats DB
#-----------------------------------------------------------------------
def _connect(state):

    # Open DB connection
    state.db_conn = db_iface.db_open(state.model.filepath)
    if state.db_conn:
        pass
        '''
        _D.DEBUG(
                __name__,
                "File Versioned Tracking DB found on disk",
                'filepath', state.model.filepath,
                'db_conn', state.db_conn
                )
        '''
    else:
        state.db_conn = db_iface.db_create(state.model.filepath)
        '''
        _D.DEBUG(
                __name__,
                "File Versioned Tracking DB not found on disk, creating new",
                'filepath', state.model.filepath,
                'db_conn', state.db_conn
                )
        '''

        c = state.db_conn.cursor()
        sql = "CREATE TABLE versions \
                ( \
                id INTEGER PRIMARY KEY, \
                date INTEGER UNIQUE, \
                file TEXT, \
                size INTEGER \
                )"
        c.execute(sql)
        state.db_conn.commit()


#-----------------------------------------------------------------------
# Disconnect DB
#-----------------------------------------------------------------------
def _disconnect(state):
    if state.db_conn:
        db_iface.db_close(state.db_conn)


#-----------------------------------------------------------------------
# Get DB file size
#-----------------------------------------------------------------------
def get_db_file_size(state):
    return os.path.getsize(state.model.filepath)


#-----------------------------------------------------------------------
# Add file to DB
#-----------------------------------------------------------------------
def add_version(state, filename, size):
    c = state.db_conn.cursor()

    sql = "INSERT OR REPLACE \
            INTO versions (date, file, size) \
            VALUES ('{}', '{}', '{}')\
            ".format(state.model.date_int, filename, size)
    c.execute(sql)
    state.db_conn.commit()


#-------------------------------------------------------------------
# Remove versions older than last N
#-------------------------------------------------------------------
def remove_versions_older_than(state, count):
    """
    Delete DB records and returns list of entries that were deleted.
    Count means how many latest ones to keep:
        0 - keep only the recent one
        >1 - keep recent plus N older
        <0 - keep all, delete nothing
    """

    if count < 0:
        return []

    count += 1

    c = state.db_conn.cursor()
    sql = "SELECT * FROM versions ORDER BY date DESC"
    c.execute(sql)

    ids = []
    files = []
    skipped = 0

    for row in c:
        if skipped < count:
            skipped += 1
            continue

        files.append(row[2])
        ids.append(str(row[0]))

    # Remove rows with ids
    sql = "DELETE FROM versions \
            WHERE id IN ({}) \
            ".format(', '.join(ids))
    c.execute(sql)
    state.db_conn.commit()

    return files


#-----------------------------------------------------------------------
# Dump DB
#-----------------------------------------------------------------------
def dump(state):
        c = state.db_conn.cursor()
        if not c:
            return

        sql = "SELECT * FROM versions"
        c.execute(sql)

        entries = {}
        for row in c:
            entries[row[0]] = "{}\t{}".format(row[2], row[3])

        _D.DEBUG(
                __name__,
                "File Versioned Tracking DB dump",
                'entries', entries
                )


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(date_str, date_int, dir_db, filename):
    # Validate
    if not date_str:
        return None, 1, "date_str must be provided"
    if not date_int:
        return None, 1, "date_int must be provided"
    if not dir_db:
        return None, 1, "dir_db must be provided"
    if not filename:
        return None, 1, "filename must be provided"

    filepath = os.path.join(dir_db, filename)
    model = Model(date_str, date_int, dir_db, filename, filepath)
    return model, 0, None


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model):
    state = State(model)
    return state, 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(date_str, date_int, dir_db, filename):
    ''' Initialize model and state'''
    # Model
    model, err, msg = _init_model(date_str, date_int, dir_db, filename)
    if err:
        return None, err, msg

    '''
    _D.OBJECT(
            __name__,
            "Versioned File Tracker Model",
            model
            )
    '''

    # State
    return _init_state(model)


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):
    '''Execute state'''

    # Connect to DB or create new DB
    _connect(state)

    return 0, None


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''

    # Disconnect DB
    _disconnect(state)
