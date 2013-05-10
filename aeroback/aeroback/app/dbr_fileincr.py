import os

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import iface.db_sqlite3 as db_iface

import aeroback.util.fmt as fmtutil
'''
Incremental File Tracker DB maintainer:
    - keeps track of incrementally added files

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

        self.db_conn_upload = None
        self.db_curs_upload = None

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
                "File Incremental Tracking DB found on disk",
                'filepath', state.model.filepath,
                'db_conn', state.db_conn
                )
        '''
    else:
        state.db_conn = db_iface.db_create(state.model.filepath)
        '''
        _D.DEBUG(
                __name__,
                "File Incremental Tracking DB not found on disk, creating new",
                'filepath', state.model.filepath,
                'db_conn', state.db_conn
                )
        '''

        c = state.db_conn.cursor()

        # Table files: list of files in storage
        sql = "CREATE TABLE files_storage \
                ( \
                name TEXT UNIQUE, \
                modified INTEGER, \
                size INTEGER \
                )"
        c.execute(sql)

        # Table files_local: list of files found on local disk
        sql = "CREATE TABLE files_local \
                ( \
                name TEXT UNIQUE, \
                modified INTEGER, \
                size INTEGER \
                )"
        c.execute(sql)

        # Table files_upload: list of files to be stored
        sql = "CREATE TABLE files_upload \
                ( \
                name TEXT UNIQUE, \
                modified INTEGER, \
                size INTEGER \
                )"
        c.execute(sql)

        # Table stats: stored amount of data by date
        sql = "CREATE TABLE stats \
                ( \
                date TEXT, \
                size INTEGER \
                )"
        c.execute(sql)

        # Table params: about this backup
        sql = "CREATE TABLE params \
                ( \
                id INTEGER PRIMARY KEY, \
                dir_local TEXT, \
                url_storage TEXT \
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
# Set params table
#-----------------------------------------------------------------------
def update_params(state, dir_local, url_storage):
    c = state.db_conn.cursor()
    if not c:
        return

    sql = "INSERT OR REPLACE INTO params \
          (id, dir_local, url_storage) VALUES('{}','{}','{}') \
          ".format(0, dir_local, url_storage)

    c.execute(sql)
    state.db_conn.commit()


#-----------------------------------------------------------------------
# Clear session data in DB
#-----------------------------------------------------------------------
def clear_locals_uploads(state):
    c = state.db_conn.cursor()
    if not c:
        return

    # Clear list of local files
    sql = "DELETE FROM files_local"
    c.execute(sql)

    # Clear list of files to be uploaded
    sql = "DELETE FROM files_upload"
    c.execute(sql)

    state.db_conn.commit()


#-----------------------------------------------------------------------
# Add local file
#-----------------------------------------------------------------------
def add_local_file(state, filepath, modified, size):
    """
    Add item to table files_local:
        - filepath
        - modified - integer stamp
        - size - integer
    """
    c = state.db_conn.cursor()

    sql = "INSERT INTO files_local \
            VALUES ('{}','{}','{}') \
            ".format(filepath, modified, size)

    c.execute(sql)


#-----------------------------------------------------------------------
# Commit added local file
#-----------------------------------------------------------------------
def commit_added_local_files(state):
    state.db_conn.commit()


#-----------------------------------------------------------------------
# Find differences between storage and local files
#-----------------------------------------------------------------------
def find_local_storage_diff(state, max_total_size):
    """
    Finds files that new/modified compared to files already in storage.
    maxSize (if > 0) specifies max total size of files.
    """
    c = state.db_conn.cursor()

    # Open second temporary connection
    conn_temp = db_iface.db_open(state.model.filepath)
    cursor_temp = conn_temp.cursor()

    # How many files are already in storage
    sql = "SELECT COUNT(*) FROM files_storage"
    c.execute(sql)
    row = c.fetchone()

    # Storage is empty ?
    if not row or row[0] == 0:
        # Use all local files
        sql = "SELECT DISTINCT * FROM files_local"

    else:
        # Find difference
        sql = "SELECT DISTINCT a.* \
        FROM files_local a \
        INNER JOIN files_storage b \
        ON \
        a.name NOT IN (SELECT name FROM files_storage) \
        OR \
        a.name=b.name AND (a.modified!=b.modified OR a.size!=b.size)"

    c.execute(sql)

    # For each found file...
    i = 0
    total_size = 0
    for row in c:
        total_size += row[2]
        if max_total_size <= 0:
            add = True
        elif total_size < max_total_size or i == 0:
            # To make sure first file can bypass max_total_size
            add = True
        else:
            add = False
        if add:
            sql = "INSERT INTO files_upload \
                   VALUES ('{}','{}','{}') \
                   ".format(row[0], row[1], row[2])
            cursor_temp.execute(sql)
            i += 1
        else:
            # Deduct this file size from total if beyond max
            total_size -= row[2]
            if total_size < 0:
                total_size = 0

    # Commit and close temporary connection
    if i > 0:
        conn_temp.commit()
    conn_temp.close()

    # Debug
    '''
    _D.DEBUG(
            __name__,
            "File Incremental Tracking DB found differences",
            'TODO', 'Check count!',
            'count', i,
            'total_size', fmtutil.byte_size(total_size),
            'max_total_size', fmtutil.byte_size(max_total_size),
            '% of allowed', 100 * total_size / max_total_size
            )
    '''

    return 0, None


#-----------------------------------------------------------------------
# Get next file to upload
#-----------------------------------------------------------------------
def get_files_upload(state):
    """
    Fetches next file to be uploaded
    """
    c = state.db_conn.cursor()

    sql = "SELECT * FROM files_upload"
    c.execute(sql)
    return c


#-----------------------------------------------------------------------
# Add file to storage files
#-----------------------------------------------------------------------
def add_update_storage_file(state, filepath, modified, size):
    """
    Adds or updates existing storage file with new date/size
    """
    # Open second temporary connection, if not opened yet
    if not state.db_conn_upload or not state.db_curs_upload:
        state.db_conn_upload = db_iface.db_open(state.model.filepath)
        state.db_curs_upload = state.db_conn_upload.cursor()

    sql = "INSERT OR REPLACE INTO files_storage \
          (name, modified, size) VALUES('{}','{}','{}') \
          ".format(filepath, modified, size)

    state.db_curs_upload.execute(sql)


#-----------------------------------------------------------------------
# Commit all storage files adds
#-----------------------------------------------------------------------
def commit_added_storage_files(state):
    """
    """
    # Secondary connection must be open
    if not state.db_conn_upload or not state.db_curs_upload:
        _D.ERROR(
                __name__,
                "Temporary connection for adding storage files must be open"
                )
        return

    state.db_conn_upload.commit()
    state.db_conn_upload.close()

    state.db_conn_upload = None
    state.db_curs_upload = None


#-----------------------------------------------------------------------
# Add file to storage files
#-----------------------------------------------------------------------
def add_stats(state, date, size):
    """
    Add statistical record for session stores:
        - date as plain text
        - size in bytes, integer
    """
    # Open second temporary connection
    conn_temp = db_iface.db_open(state.model.filepath)
    cursor_temp = conn_temp.cursor()

    sql = "INSERT INTO stats \
            VALUES ('{}','{}') \
            ".format(date, size)
    cursor_temp.execute(sql)

    # Commit and close temporary connection
    conn_temp.commit()
    conn_temp.close()


#-----------------------------------------------------------------------
# Dump DB
#-----------------------------------------------------------------------
def dump_params(state):
        c = state.db_conn.cursor()
        if not c:
            return

        sql = "SELECT * FROM params"
        c.execute(sql)

        entries = []
        for row in c:
            entries.append("{}\t{}\t{}".format(row[0], row[1], row[2]))

        _D.DEBUG(
                __name__,
                "File Incremental Tracking DB dump",
                'params', entries
                )


def dump_files_local(state):
        c = state.db_conn.cursor()
        if not c:
            return

        sql = "SELECT * FROM files_local"
        c.execute(sql)

        entries = []
        for row in c:
            entries.append("{}\t{}\t{}".format(row[2], row[1], row[0]))

        _D.DEBUG(
                __name__,
                "File Incremental Tracking DB dump",
                'files_local', entries
                )


#-----------------------------------------------------------------------
def dump_files_storage(state):
        c = state.db_conn.cursor()
        if not c:
            return

        sql = "SELECT * FROM files_storage"
        c.execute(sql)

        entries = []
        for row in c:
            entries.append("{}\t{}\t{}".format(row[2], row[1], row[0]))

        _D.DEBUG(
                __name__,
                "File Incremental Tracking DB dump",
                'files_storage', entries
                )


#-----------------------------------------------------------------------
def dump_stats(state):
        c = state.db_conn.cursor()
        if not c:
            return

        sql = "SELECT * FROM stats"
        c.execute(sql)

        entries = []
        for row in c:
            entries.append("{}\t{}".format(row[0], fmtutil.byte_size(row[1])))

        _D.DEBUG(
                __name__,
                "File Incremental Tracking DB dump",
                'stats', entries
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
            "Incremental File Tracker Model",
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

    # Vacuum DB to minimize size
    c = state.db_conn.cursor()
    if c:
        sql = "VACUUM"
        c.execute(sql)
        state.db_conn.commit()

    # Disconnect DB
    _disconnect(state)
