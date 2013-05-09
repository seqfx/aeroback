import os

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import iface.db_sqlite3 as db_iface

'''
Storage stats DB maintainer:
    - updates stats DB
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
                "DB Stats found on disk",
                'filepath', state.model.filepath,
                'db_conn', state.db_conn
                )
        '''
    else:
        state.db_conn = db_iface.db_create(state.model.filepath)
        '''
        _D.WARNING(
                __name__,
                "DB Stats not found on disk, creating new",
                'filepath', state.model.filepath,
                'db_conn', state.db_conn
                )
        '''

        c = state.db_conn.cursor()
        sql = "CREATE TABLE sessions_store \
                ( \
                id INTEGER PRIMARY KEY, \
                date INTEGER, \
                backup_type TEXT, \
                size INTEGER \
                )"
        c.execute(sql)
        state.db_conn.commit()


#-----------------------------------------------------------------------
# Disconnect DB
#-----------------------------------------------------------------------
def _disconnect(state):
    db_iface.db_close(state.db_conn)


#-----------------------------------------------------------------------
# Get DB file size
#-----------------------------------------------------------------------
def get_db_file_size(state):
    return os.path.getsize(state.model.filepath)


#-----------------------------------------------------------------------
# Update Stats DB - store type
#-----------------------------------------------------------------------
def update_stored(state, atype, size):
        c = state.db_conn.cursor()

        # Check for pre-existing
        sql = "SELECT * FROM sessions_store \
                WHERE date='{}' AND backup_type='{}'\
                ".format(state.model.date_int, atype)

        c.execute(sql)
        row = c.fetchone()

        if row:
            # Pre-existing
            sql = "UPDATE sessions_store \
                    SET size='{}' WHERE id='{}'\
                    ".format(row[3] + size, row[0])
        else:
            # New row
            sql = "INSERT INTO sessions_store (date, backup_type, size) \
                VALUES ('{}', '{}', '{}') \
                ".format(state.model.date_int, atype, size)

        c.execute(sql)
        state.db_conn.commit()


#-----------------------------------------------------------------------
# Update Stats DB - store total
#-----------------------------------------------------------------------
def update_stored_total(state, size):
        c = state.db_conn.cursor()

        # Check for pre-existing
        sql = "SELECT * FROM sessions_store \
                WHERE date='{}' AND backup_type IS NULL\
                ".format(state.model.date_int)

        c.execute(sql)
        row = c.fetchone()

        if row:
            # Pre-existing
            sql = "UPDATE sessions_store \
                    SET size='{}' WHERE id='{}'\
                    ".format(row[3] + size, row[0])
        else:
            # New row
            sql = "INSERT INTO sessions_store (date, size) \
                VALUES ('{}', '{}') \
                ".format(state.model.date_int, size)

        c.execute(sql)
        state.db_conn.commit()


#-----------------------------------------------------------------------
# Update Stats DB
#-----------------------------------------------------------------------
def update(state, stored_stats, restored_stats):

    # Stored:
    total_size = 0
    # Update each type
    for key in stored_stats:
        size = stored_stats[key]
        total_size += size
        update_stored(state, key, size)

    # Update total
    update_stored_total(state, total_size)

    #TODO restored stats update
    '''
    # Restored:
    total_size = 0
    # Update each type
    for key in restored_stats:
        size = restored_stats[key]
        total_size += size
        update_restored(state, key, size)

    # Update total
    update_restored_total(state, total_size)
    '''


#-----------------------------------------------------------------------
# Dump Stats DB
#-----------------------------------------------------------------------
def dump(state):
        c = state.db_conn.cursor()
        sql = "SELECT * FROM sessions_store \
                WHERE date='{}' \
                ".format(state.model.date_int)
        c.execute(sql)

        entries = {}
        for row in c:
            atype = row[2]
            if not atype:
                atype = 'TOTAL'
            entries[atype] = row[3]

        _D.DEBUG(
                __name__,
                "Storage DB Stats dump",
                'date', state.model.date_str,
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
            "Storage Stats model",
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
