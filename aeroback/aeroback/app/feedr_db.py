import os

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import aeroback.constants.corestr as corestr
import storager
import dbr_filevers as dbr

import aeroback.util.cmd as cmdutil
import aeroback.util.fmt as fmtutil

'''
Mongo feeder module:
    - dumps Mongo DB
    - compresses into TAR
    - stores to storage
    - updates tracking DB

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

    def __init__(self, atype, host, user, password, dirstorage, history_size, date_str, date_int, dir_temp):
        super(Model, self).__init__()

        self.atype = atype
        self.host = host
        self.user = user
        self.password = password
        self.dirstorage = dirstorage
        self.history_size = history_size
        self.date_str = date_str
        self.date_int = date_int
        self.dir_temp = dir_temp

    def debug_vars(self):
        if self.password:
            pwd = corestr._STR_PASSWORD_HIDDEN
        else:
            pwd = corestr._STR_PASSWORD_NOT_SET
        return [
                'atype', self.atype,
                'host', self.host,
                'user', self.user,
                'password', pwd,
                'dirstorage', self.dirstorage,
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

    atype = params.get('type', None)
    if not atype:
        return None, 1, "params:type must be provided"
    elif atype != 'db_mongo' and atype != 'db_mysql':
        return None, 1, "params:type = {} is not among supported types (db_mongo, db_mysql)".format(atype)

    if not params:
        return None, 1, "params must be provided"

    if not params.get('host', None):
        return None, 1, "params:host must be provided"
    # user and password are optional

    if not params.get('dirstorage', None):
        return None, 1, "params:dirstorage must be provided"
    if params.get('history', None) is None:
        return None, 1, "params:history must be provided"

    # Model
    model = Model(
                atype = atype,
                host = params['host'],
                user = params['user'],
                password = params['password'],
                dirstorage = params['dirstorage'],
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
            "Feeder DB Model",
            model
            )
    '''

    # State
    state, err, msg = _init_state(model, storstate)
    if err:
        return State(None), err, msg

    # Description for reporting
    state.set_description('Mongo DB backup')

    # Descriptors for reporting
    state.set_descriptor('Tables', 'All')
    state.set_descriptor('History size', state.model.history_size)

    # Stats for reporting
    state.set_stats('Stats:', '&nbsp')

    return state, err, msg


#-----------------------------------------------------------------------
# Dump DB Mongo
#-----------------------------------------------------------------------
def _dump_db_mongo(state):
    invocation = ['mongodump',
            '-h', state.model.host,
            '-o', os.path.join(state.model.dir_temp, state.model.atype)]

    if state.model.user and state.model.password:
        invocation.append('-u')
        invocation.append(state.model.user)
        invocation.append('-p')
        invocation.appned(state.model.password)

    res, err, msg = cmdutil.call_cmd(invocation)
    if err:
        return 1, "Error during Mongo DB dump: {}".format(msg)
    else:
        return 0, None


#-----------------------------------------------------------------------
# Dump DB MySQL
#-----------------------------------------------------------------------
def _dump_db_mysql(state):
    warn = "MySQL dump not fully tested. Currently backs up all DBs"
    state.add_msg_warning(warn)
    _D.WARNING(
            __name__,
            warn,
            )

    state.dump_filepath_mysql = os.path.join(
            state.model.dir_temp,
            "{}.sql".format(state.model.atype))

    invocation = ['mysqldump']

    if state.model.user and state.model.password:
        invocation.append('-u"{}"'.format(state.model.user))
        invocation.append('-p"{}"'.format(state.model.password))

    invocation.append('--all-databases')
    invocation.append('-r')
    invocation.append(state.dump_filepath_mysql)

    res, err, msg = cmdutil.call_cmd(invocation)
    if err:
        return 1, "Error during MySQL DB dump: {}".format(msg)
    else:
        return 0, None


#-----------------------------------------------------------------------
# Compress DB dump directory
#-----------------------------------------------------------------------
def _archive_dump(state):
    state.archive_filename = "{}_{}.tar.gz".format(state.model.atype, state.model.date_str)
    state.archive_filepath = os.path.join(
            state.model.dir_temp,
            state.archive_filename
            )

    # Read TAR help on -C option:
    # http://www.gnu.org/software/tar/manual/html_section/one.html#SEC117
    if state.model.atype == 'db_mongo':
        invocation = ['tar',
                    '-czvf',
                    state.archive_filepath,
                    '-C', state.model.dir_temp,
                    state.model.atype]

    elif state.model.atype == 'db_mysql':
        invocation = ['tar',
                    '-czvf',
                    state.archive_filepath,
                    '-C', state.model.dir_temp,
                    os.path.basename(state.dump_filepath_mysql)]

    res, err, msg = cmdutil.call_cmd(invocation)
    if err:
        return 1, "Error archiving DB dump: {}".format(msg)
    else:
        return 0, None


#-----------------------------------------------------------------------
# Store archived DB dump
#-----------------------------------------------------------------------
def _store_archive(state):
    err, msg = storager.store(
            state.states.storager,
            state.archive_filepath,
            state.model.dirstorage,
            state.model.atype)
    if err:
        return 1, "Error storing DB archive: {}".format(msg)

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
            state.model.dirstorage,
            state.states.dbr.model.dir_db,
            state.states.dbr.model.filename,
            None)
    if err:
        warn = "Backup {}: Tracking DB not found in storage. Ignore if that's the first run".format(state.model.atype)
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

    # Dump DB
    if state.model.atype == 'db_mongo':
        err, msg = _dump_db_mongo(state)
    elif state.model.atype == 'db_mysql':
        err, msg = _dump_db_mysql(state)
    else:
        return 1, "Not supported DB type: {}".format(state.model.atype)

    if err:
        return 1, msg

    # Compress DB dump directory
    err, msg = _archive_dump(state)
    if err:
        return 1, msg

    # Store DB archive
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
            state.model.dirstorage,
            None)
    if err:
        _D.ERROR(
                __name__,
                "Error storing DB",
                'file', state.states.dbr.model.filename,
                'msg', msg
                )
