import os
import re

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import storager
import dbr_fileincr as dbr

import aeroback.util.fmt as fmtutil
import aeroback.util.fs as fsutil

'''
Dir Increment feeder module:
    - finds differences between local files and files in DB
    - stores new/modified files to storage
    - updates incremental file tracking DB
    - stores DB

Required modules:
    - storager

Children modules:
    - dbr_filevers

Status accumulates statistics:
    - Local statistics:
        - total number of files
        - total size of files
    - Uploading statistics:
        - files stored
        - bytes stored
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

    def __init__(self, atype, directory, dirstorage, maxupload, ignore_patterns, includes, excludes, description, date_str, date_int, dir_temp):
        super(Model, self).__init__()

        self.atype = atype
        self.directory = directory
        self.dirstorage = dirstorage
        self.maxupload = maxupload
        self.ignore_patterns = ignore_patterns
        self.includes = includes
        self.excludes = excludes
        self.description = description
        self.date_str = date_str
        self.date_int = date_int
        self.dir_temp = dir_temp

    def debug_vars(self):
        return [
                'atype', self.atype,
                'directory', self.directory,
                'dirstorage', self.dirstorage,
                'maxupload', self.maxupload,
                'ignore_patterns', self.ignore_patterns,
                'includes', self.includes,
                'excludes', self.excludes,
                'description', self.description,
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

        self.total_stored_files = 0

    def debug_vars(self):
        return []


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
    elif atype != 'dir_increment':
        return None, 1, "params:type = {} is not among supported types (dir_compress)".format(atype)

    if not params.get('dir', None):
        return None, 1, "params:dir must be provided"

    if not params.get('dirstorage', None):
        return None, 1, "params:dirstorage must be provided"

    if not params.get('maxupload', None):
        return None, 1, "params:maxupload must be provided"

    # Includes - optional
    '''
    if not params.get('includes', None):
        return None, 1, "params:includes must be provided"
    '''

    # Excludes - optional
    '''
    if not params.get('excludes', None):
        return None, 1, "params:excludes must be provided"
    '''

    if not params.get('description', None):
        return None, 1, "params:description must be provided"

    # Validate directory exists
    directory = os.path.normpath(params['dir'])
    if not os.path.exists(directory):
        return None, 1, "Backup directory doesn't exist: {}".format(directory)

    # Validate includes exist
    missing = []
    normalized = []
    includes = params['includes']
    for d in includes:
        path = os.path.join(directory, d)
        if not os.path.exists(path):
            missing.append(path)
        else:
            normalized.append(os.path.normpath(d))

    includes = list(normalized)

    # Error if any missing
    if missing:
        return None, 1, "Some Include directories don't exist: {}".format(
                ', '.join(missing))

    # Validate excludes exist
    missing = []
    normalized = []
    excludes = params['excludes']
    for d in excludes:
        path = os.path.join(directory, d)
        if not os.path.exists(path):
            missing.append(path)
        else:
            normalized.append(os.path.normpath(d))

    excludes = list(normalized)

    # Warn if any missing but keep going
    if missing:
        return None, 1, "Some Exclude directories don't exist: {}".format(
                ', '.join(missing))

    # File ignore patterns
    patterns = [
            r'^\..*',  # starts with  .   '.hello.txt'
            r'^~.*',   # starts with  ~   '~hello.txt'
            r'^.*~$'   # ends with    ~   'hello.txt~'
            ]

    ignore_patterns = []
    for p in patterns:
        ignore_patterns.append(re.compile(p))

    # Model
    model = Model(
                atype = atype,
                directory = directory,
                dirstorage = params['dirstorage'],
                maxupload = params['maxupload'],
                ignore_patterns = ignore_patterns,
                includes = includes,
                excludes = excludes,
                description = params['description'],
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
    #NOTE DB name for now: _aeroback_dir_increment.db
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
    state.set_descriptor('Local dir', state.model.directory)
    state.set_descriptor('Includes', state.model.includes)
    state.set_descriptor('Excludes', state.model.excludes)
    state.set_descriptor('Max session upload', fmtutil.byte_size(state.model.maxupload))

    # Stats for reporting
    state.set_stats('Stats:', '&nbsp')
    state.set_stats_category('Uploaded', 'Files count', 0)
    state.set_stats_category('Uploaded', 'Files size', 0)
    state.set_stats_category('Tracking DB', 'Size', 0)
    state.set_stats_category('Local', 'Files count', 0)
    state.set_stats_category('Local', 'Files size', 0)

    return state, err, msg


#-----------------------------------------------------------------------
# Check if directory needs to be backed up
#-----------------------------------------------------------------------
def _is_dir_child(directory, dir_src, dirs):
    """
    Check if directory matches beginning of any dir in dirs.
    directory = a/b/c ; d = a ---> True
    directory = a/b/c ; d = f/g ---> False
    """

    for d in dirs:
        if directory.startswith(os.path.join(dir_src, d)):
            return True

    return False


#-----------------------------------------------------------------------
# Check if directory needs to be backed up
#-----------------------------------------------------------------------
def _is_dir_valid_for_backup(directory, dir_src, dir_incl, dir_excl):
    """
    Included dirs - highest precedence.
        If empty - means ignore included and check excluded
        If not empty - ignore excluded
    """

    # Source dir itself always valid
    if directory == dir_src:
        return True

    # Included not empty? Only check included, ignore excluded
    if dir_incl:
        return _is_dir_child(directory, dir_src, dir_incl)

    # Included empty, check excluded
    if _is_dir_child(directory, dir_src, dir_excl):
        return False

    return True


#-----------------------------------------------------------------------
# Name matches one of patterns
#-----------------------------------------------------------------------
def _matches(name, patterns):
    for p in patterns:
        if p.search(name):
            #print "\t\t\tmatches = {}".format(p.pattern)
            return True
    return False


#-----------------------------------------------------------------------
# Name matches one of patterns
#-----------------------------------------------------------------------
def _relative_path(filepath, dir_base):
    # Extract path that is in between directory and filename
    pass
    '''
    filedir, filename = fsutil.path_to_body_tail(filepath)
    if len(filedir) > dir_str_len:
        # Case of file in subdirectory of directory
        dirstorage = os.path.join(
                state.model.dirstorage,
                filedir[dir_str_len + 1:])
    else:
        # Case of file located in directory itself
        dirstorage = state.model.dirstorage
    '''


#-----------------------------------------------------------------------
# Scan local files
#-----------------------------------------------------------------------
def _scan_local_files(state):
    # List of directories to ignore
    # Usually those that are hidden (start with '.')
    ignored = []

    # Scan directory
    count = 0
    total_size = 0
    directory = state.model.directory
    includes = state.model.includes
    excludes = state.model.excludes
    ignore_patterns = state.model.ignore_patterns

    for root, subFolders, files in os.walk(directory):

        # Check this directory is not a child of ignored
        skip = False
        for ign in ignored:
            if root.startswith(ign):
                skip = True
                break

        if skip:
            continue

        # Add root directory to ignored if basename matches one of ignore patterns
        base = os.path.basename(root)
        if _matches(base, ignore_patterns):
            print "\t- {}".format(base)
            ignored.append(root)
            continue

        if not _is_dir_valid_for_backup(root, directory, includes, excludes):
            continue

        print "\t  {}".format(root)

        # Legitimate directory, process its files
        for f in files:

            # Skip files matching ignore patterns
            if _matches(f, ignore_patterns):
                print "\t\t- {}".format(f)
                continue

            print "\t\t  {}".format(f)

            # Process file
            filepath = os.path.join(root, f)
            modified = int(os.path.getmtime(filepath))
            size = os.path.getsize(filepath)
            total_size += size

            #print "\t\t  = {}".format(filepath[len(directory) + 1:])
            dbr.add_local_file(
                    state.states.dbr,
                    filepath[len(directory) + 1:],
                    modified,
                    size)
            count += 1

    # Commit, one for all adds
    dbr.commit_added_local_files(state.states.dbr)

    '''
    _D.DEBUG(
            __name__,
            "Finished scanning local files",
            'Number of files', count,
            'Total size', fmtutil.byte_size(total_size)
            )
    dbr.dump_files_local(state.states.dbr)
    '''

    state.set_stats_category('Local', 'Files count', count)
    state.set_stats_category('Local', 'Files size', fmtutil.byte_size(total_size))

    return 0, None


#-----------------------------------------------------------------------
# Store files
#-----------------------------------------------------------------------
def _store(state):
    """
    Store each file.
    Only allows max_fails failures before stopping and returning error.
    """
    max_fails = 5
    fails = 0

    i = 0
    total_size = 0

    # Get files to store
    rows = dbr.get_files_upload(state.states.dbr)

    directory = state.model.directory
    dirstorage = state.model.dirstorage
    #dir_str_len = len(state.model.directory)
    # Store each file
    for row in rows:
        filepath = row[0]
        modified = row[1]
        size = row[2]

        # Extract path that is in between directory and filename
        filedir, filename = fsutil.path_to_body_tail(filepath)
        '''
        if len(filedir) > dir_str_len:
            # Case of file in subdirectory of directory
            dirstorage = os.path.join(
                    state.model.dirstorage,
                    filedir[dir_str_len + 1:])
        else:
            # Case of file located in directory itself
            dirstorage = state.model.dirstorage
        '''

        err, msg = storager.store(
                state.states.storager,
                os.path.join(directory, filepath),
                "{}/{}".format(dirstorage, filedir),
                state.model.atype)
        if err:
            # Log error
            _D.ERROR(
                    __name__,
                    "Error storing file",
                    'file', filepath
                    )
            fails += 1
            if fails == max_fails:
                break

        else:
            # Update DB on file store success
            print "\t+ ", filepath
            state.total_stored_files += 1
            dbr.add_update_storage_file(state.states.dbr, filepath, modified, size)
            i += 1
            total_size += size

    # Commit all added storage files, if any stores happened
    if i:
        dbr.finish_adding_storage_files(state.states.dbr)
        dbr.add_stats(state.states.dbr, state.model.date_str, total_size)

    # Dump stats
    #dbr.dump_stats(state.states.dbr)

    state.set_stats_category('Uploaded', 'Files count', i)
    state.set_stats_category('Uploaded', 'Files size', fmtutil.byte_size(total_size))

    if fails:
        return 1, "Error storing files, aborted after {} failures".format(max_fails)

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
        warn = "Backup {}: File Incremental Tracking DB not found in storage. Ignore if that's the first run".format(state.model.atype)
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

    # Update DB params
    dbr.update_params(state.states.dbr, state.model.directory, state.model.dirstorage)

    # Clear DB list of local files and files to be uploaded
    dbr.clear_locals_uploads(state.states.dbr)

    # Scan local files and add them to DB
    err, msg = _scan_local_files(state)
    if err:
        state.add_msg_error(msg)

    # Find differences
    err, msg = dbr.find_local_storage_diff(state.states.dbr, state.model.maxupload)
    if err:
        state.add_msg_error(msg)

    # Store differences
    err, msg = _store(state)
    if err:
        state.add_msg_error(msg)

    return 0, None


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''

    # Clear DB list of local files and uploaded files to minimize DB size
    dbr.clear_locals_uploads(state.states.dbr)

    # Dump DB
    dbr.dump_params(state.states.dbr)
    dbr.dump_files_storage(state.states.dbr)

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
                "Error storing File Incremental Tracking DB",
                'file', state.states.dbr.model.filename,
                'msg', msg
                )
