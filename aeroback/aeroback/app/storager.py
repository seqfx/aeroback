import os
#import sys
#import time
#from datetime import datetime

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import dbr_storstats as dbr
import iface.storage_gsutil as storage_iface

import aeroback.util.url as urlutil

'''
Storage operations:
- retrieve DB from storage
- read/write to storage
- update DB

Required modules:
    -

Children modules:
    - dbr_storstats
'''


#-----------------------------------------------------------------------
# States for other modules
#-----------------------------------------------------------------------
class States(object):

    def __init__(self):
        self.dbr = None

    def debug_vars(self):
        return [
                'dbr', self.dbr
                ]


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self, atype, scheme, bucket, dirstorage, date_str, date_int, dir_temp, url_db):
        super(Model, self).__init__()

        self.atype = atype
        self.scheme = scheme
        self.bucket = bucket
        self.dirstorage = dirstorage
        self.date_str = date_str
        self.date_int = date_int
        self.dir_temp = dir_temp
        self.url_db = url_db

    def debug_vars(self):
        return [
                'type', self.atype,
                'scheme', self.scheme,
                'bucket', self.bucket,
                'dirstorage', self.dirstorage,
                'date_str', self.date_str,
                'date_int', self.date_int,
                'dir_temp', self.dir_temp,
                'url_db', self.url_db
                ]


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model
        self.states = States()

        self.stored_stats = {}
        self.restored_stats = {}

    def debug_vars(self):
        return [
                'stored_stats', self.stored_stats,
                'restored_stats', self.restored_stats
                ]


#-------------------------------------------------------------------
# Increment stored stats
#-------------------------------------------------------------------
def _increment_stored_stats(state, atype, size):
    '''
    Add to counter of stored date for given type of backup
    '''
    if not atype:
        return

    stats = state.stored_stats.get(atype, None)
    if stats:
        state.stored_stats[atype] += size
    else:
        state.stored_stats[atype] = size


#-------------------------------------------------------------------
# Get stored stats
#-------------------------------------------------------------------
def get_stored_stats(state):
    '''
    How much was stored
    '''
    total = 0
    for atype in state.stored_stats:
        total += state.stored_stats[atype]

    return total


#-------------------------------------------------------------------
# Increment restored stats
#-------------------------------------------------------------------
def _increment_restored_stats(state, atype, size):
    '''
    Add to counter of restored date for given type of backup
    '''
    if not atype:
        atype = 'backup_?'
    stats = state.restored_stats.get(atype, None)
    if stats:
        state.restored_stats[atype] += size
    else:
        state.restored_stats[atype] = size


#-------------------------------------------------------------------
# Get restored stats
#-------------------------------------------------------------------
def get_restored_stats(state):
    '''
    How much was restored
    '''
    total = 0
    for atype in state.restored_stats:
        total += state.restored_stats[atype]

    return total


#-------------------------------------------------------------------
# Build storage URL
#-------------------------------------------------------------------
def build_url(state, *paths):
    '''
    Build storage url by adding paths to scheme://bucket/dirstorage
    '''
    return ''.join(
        urlutil.url_build(
                state.model.scheme,
                state.model.bucket,
                state.model.dirstorage,
                *paths
        ))


#-------------------------------------------------------------------
# Store: local --> storage
#-------------------------------------------------------------------
def store(state, path, suburl, atype):
    '''
    Store local file to remote storge
    '''
    filename = os.path.basename(path)
    url = build_url(state, suburl, filename)
    result, err, msg = storage_iface.copy_local_to_storage(path, url)
    if err:
        msg = "Error storing from {}, to {}: {}".format(path, url, msg)

    else:
        # Add size to stats
        _increment_stored_stats(state, atype, os.stat(path).st_size)

    return err, msg


#-------------------------------------------------------------------
# Restore: local <--- storage
#-------------------------------------------------------------------
def restore(state, suburl, path, filename, atype):
    '''
    Restore file from storage to local disk
    '''
    url = build_url(state, suburl, filename)
    result, err, msg = storage_iface.copy_storage_to_local(url, path)
    if err:
        msg = "Error restoring from {}, to {}: {}".format(url, path, msg)

    else:
        # Add size to stats
        # TODO finish
        #_increment_stats_restore(state, atype, os.stat(os.path.join(path, filename)).st_size)
        pass

    return err, msg


#-------------------------------------------------------------------
# Unstore: delete file from storage
#-------------------------------------------------------------------
def unstore(state, suburl, filename):
    '''
    Delete file from storage
    '''
    url = build_url(state, suburl, filename)
    result, err, msg = storage_iface.remove_from_storage(url)
    if err:
        _D.ERROR(
                __name__,
                "Error unstoring file",
                'url', url,
                'result', result,
                'msg', msg
                )

    return result, err, msg


#-------------------------------------------------------------------
# Store DB: local ---> storage
#-------------------------------------------------------------------
def _store_db(path, url, filename):
    '''
    Special case of store. DB files need to be handled differently
    '''
    path = os.path.join(path, filename)
    url = "{}/{}".format(url, filename)
    res, err, msg = storage_iface.copy_local_to_storage(path, url)
    if err:
        msg = "Error storing DB from {}, to {}, file {}: {}".format(url, path, filename, res)

    return err, msg


#-------------------------------------------------------------------
# Restore DB: local <--- storage
#-------------------------------------------------------------------
def _restore_db(url, path, filename):
    '''
    Special case of restore. DB files need to be handled differently
    '''
    url = "{}/{}".format(url, filename)
    res, err, msg = storage_iface.copy_storage_to_local(url, path)
    if err:
        msg = "Error restoring DB from {}, to {}, file {}: {}".format(url, path, filename, res)

    return err, msg


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

    if not params.get('type', None):
        return None, 1, "params:type must be provided"
    if not params.get('scheme', None):
        return None, 1, "params:scheme must be provided"
    if not params.get('bucket', None):
        return None, 1, "params:bucket must be provided"
    if not params.get('dirstorage', None):
        return None, 1, "params:dirstorage must be provided"

    # Remote DB URL
    url_db = ''.join(
                urlutil.url_build(
                        params['scheme'],
                        params['bucket'],
                        params['dirstorage'],
                        '_aeroback'
                ))

    model = Model(
                atype = params['type'],
                scheme = params['scheme'],
                bucket = params['bucket'],
                dirstorage = params['dirstorage'],
                date_str = date_str,
                date_int = date_int,
                dir_temp = dir_temp,
                url_db = url_db
                )

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
def init(date_str, date_int, dir_temp, params):
    ''' Initialize model and state'''

    # Model
    model, err, msg = _init_model(date_str, date_int, dir_temp, params)
    if err:
        return None, err, msg

    _D.OBJECT(
            __name__,
            "Storager model",
            model
            )

    # State
    state, err, msg = _init_state(model)
    if err:
        return None, err, msg

    # Init storage stats manager
    dbrstate, err, msg = dbr.init(
            date_str,
            date_int,
            model.dir_temp,
            '_aerostats.db')
    if err:
        return None, err, msg
    state.states.dbr = dbrstate

    return state, err, msg


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):
    '''Execute state'''

    # Restore DB from storage
    err, msg = _restore_db(
            state.model.url_db,
            state.model.dir_temp,
            state.states.dbr.model.filename
            )
    if err:
        state.add_msg_warning("Storage Statistics DB not found in storage. Ignore if that's the first run")
        _D.WARNING(
                __name__,
                "Storage Statistics DB not found in storage. Ignore if that's the first run",
                'msg', msg
                )

    # Execute storage stats manager
    err, msg = dbr.execute(state.states.dbr)
    if err:
        return 1, "Error executing storage stats manager: {}".format(msg)

    return 0, None


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''

    # Update DB stats with latest store/restore values
    dbr.update(
            state.states.dbr,
            state.stored_stats,
            state.restored_stats
            )

    # Dump DB
    '''
    dbr.dump(state.states.dbr)
    '''

    # Reset stats in state
    state.stored_stats = {}
    state.restored_stats = {}

    # Cleanup stats manager
    dbr.cleanup(state.states.dbr)

    # Store DB, report exception
    err, msg = _store_db(
            state.model.dir_temp,
            state.model.url_db,
            state.states.dbr.model.filename
            )
    if err:
        _D.ERROR(
                __name__,
                "Error storing Stats DB",
                'msg', msg
                )
