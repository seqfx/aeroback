import os

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import storager
import dbr_filevers as dbr

import aeroback.util.cmd as cmdutil
import aeroback.util.fs as fsutil
import aeroback.util.fmt as fmtutil

'''
Dir Compress feeder module:
    - compresses directory into TAR
    - stores to storage
    - updates versioned file tracking DB
    - stores DB

Required modules:
    - storager

Children modules:
    - dbr_filevers
'''


#-----------------------------------------------------------------------
# States for other modules
#-----------------------------------------------------------------------
class States(object):

    def __init__(self):
        self.storager = None
        self.dbr = None

    def debug_vars(self):
        return [
                'storager', self.storager,
                'dbr', self.dbr
                ]


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self, atype, dirs, dirstorage, description, history_size, date_str, date_int, dir_temp):
        super(Model, self).__init__()

        self.atype = atype
        self.dirs = dirs
        self.dirstorage = dirstorage
        self.description = description
        self.history_size = history_size
        self.date_str = date_str
        self.date_int = date_int
        self.dir_temp = dir_temp

    def debug_vars(self):
        return [
                'atype', self.atype,
                'dirs', self.dirs,
                'dirstorage', self.dirstorage,
                'description', self.description,
                'history_size', self.history_size,
                'date_str', self.date_str,
                'date_int', self.date_int,
                'dir_temp', self.dir_temp
                ]


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model
        self.states = States()

        self.archive_filename = None
        self.archive_filepath = None

        self.total_stored_files = 0

    def debug_vars(self):
        return [
                'archive_filename', self.archive_filename,
                'archive_filepath', self.archive_filepath
                ]


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(date_str, date_int, dir_temp, params):
    # Validate
    if not date_str:
        return None, 1, "date_str must be provided"
    if not date_int:
        return None, 1, "date_int must be provided"
    if not dir_temp:
        return None, 1, "dir_temp must be provided"

    if not params:
        return None, 1, "params must be provided"

    atype = params.get('type', None)
    if not atype:
        return None, 1, "params:type must be provided"
    elif atype != 'dir_compress':
        return None, 1, "params:type = {} is not among supported types (dir_compress)".format(atype)

    if not params.get('dirs', None):
        return None, 1, "params:dirs must be provided"

    if not params.get('dirstorage', None):
        return None, 1, "params:dirstorage must be provided"

    if not params.get('description', None):
        return None, 1, "params:description must be provided"

    if params.get('history', None) is None:
        return None, 1, "params:history must be provided"

    # Validate dirs exist
    verified_dirs = []
    dirs = params['dirs']
    for d in dirs:
        if os.path.exists(d):
            verified_dirs.append(os.path.normpath(d))
        else:
            _D.WARNING(
                    __name__,
                    "Backup directory missing",
                    'dir', d
                    )

    if not verified_dirs:
        return None, 1, "No directories found"

    # Model
    model = Model(
                atype = atype,
                dirs = verified_dirs,
                dirstorage = params['dirstorage'],
                description = params['description'],
                history_size = params['history'],
                date_str = date_str,
                date_int = date_int,
                dir_temp = dir_temp
                )

    return model, 0, None


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model, storstate):
    if not storstate:
        return 1, "storstate must be provided"

    state = State(model)

    # Storager state
    state.states.storager = storstate

    # Init storage stats manager
    #NOTE we save all dirs into one single archive file
    #NOTE archived name for now: _aeroback_dir_compress.db
    dbrstate, err, msg = dbr.init(
            model.date_str,
            model.date_int,
            model.dir_temp,
            "_aeroback_{}.db".format(model.atype))
    if err:
        return None, err, msg

    state.states.dbr = dbrstate

    return state, 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(date_str, date_int, dir_temp, storstate, params):
    ''' Initialize model and state'''

    # Model
    model, err, msg = _init_model(date_str, date_int, dir_temp, params)
    if err:
        return State(None), err, msg

    '''
    _D.OBJECT(
            __name__,
            "Feeder Dir Compress Model",
            model
            )
    '''

    # State
    state, err, msg = _init_state(model, storstate)
    if err:
        return State(None), err, msg

    # Description for reporting
    state.set_description(state.model.description)

    # Descriptors for reporting
    state.set_descriptor('Type', state.model.atype)
    state.set_descriptor('Storage dir', state.model.dirstorage)
    state.set_descriptor('Local dirs', state.model.dirs)
    state.set_descriptor('History size', state.model.history_size)

    # Stats for reporting
    state.set_stats('Stats:', '&nbsp')

    return state, err, msg


#-----------------------------------------------------------------------
# Archive dirs
#-----------------------------------------------------------------------
def _archive_dirs(state):
    name = '-'.join(state.model.description.lower().split())
    if len(name) > 100:
        name = name[:99]
    state.archive_filename = "{}_{}.tar.gz".format(
            name, state.model.date_str)
    state.archive_filepath = os.path.join(
            state.model.dir_temp,
            state.archive_filename
            )

    # Read TAR help on -C option:
    # http://www.gnu.org/software/tar/manual/html_section/one.html#SEC117
    invocation = ['tar',
                '-czvf',
                state.archive_filepath]

    # Append each dir
    for d in state.model.dirs:
        parent, folder = fsutil.path_to_body_tail(d)
        # If either is empty then we don't support this one
        if not parent or not folder:
            _D.WARNING(
                    __name__,
                    "Directory path cannot be split for archiving, skipping it",
                    'dir', d,
                    'parent', parent,
                    'folder', folder
                    )
            continue

        invocation.append('-C')
        invocation.append(parent)
        invocation.append(folder)

    res, err, msg = cmdutil.call_cmd(invocation)
    if err:
        return 1, "Error archiving dirs: {}".format(msg)
    else:
        return 0, None
    pass


#-----------------------------------------------------------------------
# Store archived dirs
#-----------------------------------------------------------------------
def _store_archive(state):
    err, msg = storager.store(
            state.states.storager,
            state.archive_filepath,
            state.model.dirstorage,
            state.model.atype)
    if err:
        return 1, "Error storing archive: {}".format(msg)

    state.total_stored_files += 1
    size = os.stat(state.archive_filepath).st_size
    state.set_stats('Uploaded', fmtutil.byte_size(size))

    # Add file to DB
    dbr.add_version(
            state.states.dbr,
            state.archive_filename,
            size)

    # Get list of older versions to remove
    filenames = dbr.remove_versions_older_than(
            state.states.dbr,
            state.model.history_size)

    # Remove files from storage
    for filename in filenames:
        storager.unstore(
                state.states.storager,
                state.model.dirstorage,
                filename)

    return 0, None


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):

    # Restore tracking DB from storage, ignore possible error
    err, msg = storager.restore(
            state.states.storager,
            "{}/{}".format(state.model.dirstorage, '_aeroback'),
            state.states.dbr.model.dir_db,
            state.states.dbr.model.filename,
            None)
    if err:
        warn = "Backup {}: File Versioned Tracking DB not found in storage. Ignore if that's the first run".format(state.model.atype)
        state.add_msg_warning(warn)
        _D.WARNING(
                __name__,
                warn,
                'msg', msg
                )

    # Tracking DBr execute
    err, msg = dbr.execute(state.states.dbr)
    if err:
        return 1, msg

    # Compress directories
    err, msg = _archive_dirs(state)
    if err:
        return 1, "Error archiving dirs: {}".format(msg)

    # Store archive
    err, msg = _store_archive(state)
    if err:
        return 1, msg

    return 0, None


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''

    # Dump DBr
    '''
    dbr.dump(state.states.dbr)
    '''

    # Disconnect DBr
    dbr.cleanup(state.states.dbr)

    # Get DB file size for statistics
    db_size = fmtutil.byte_size(dbr.get_db_file_size(state.states.dbr))
    state.set_stats_category('Tracking DB', 'Size', db_size)

    # Store DB (local --> storage)
    err, msg = storager.store(
            state.states.storager,
            state.states.dbr.model.filepath,
            "{}/{}".format(state.model.dirstorage, '_aeroback'),
            None)
    if err:
        _D.ERROR(
                __name__,
                "Error storing File Versioned Tracking DB",
                'file', state.states.dbr.model.filename,
                'msg', msg
                )
