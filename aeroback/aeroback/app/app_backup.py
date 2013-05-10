import os
import importlib
import tempfile
import datetime

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

import aeroback.context.context as context
import runlogr
import jobconfr
import storager

import aeroback.util.fs as fsutil
import aeroback.util.fmt as fmtutil

'''
App backup module:
- load backup config
- run backup jobs

Required modules:
    -

Children modules:
    - runlogr
    - jobconfr
    - storager
'''


#-----------------------------------------------------------------------
# States for other modules
#-----------------------------------------------------------------------
class States(object):

    def __init__(self):
        self.module = None

        self.runlogr = None

    def debug_vars(self):
        return [
                'module', self.module
                ]


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self):
        super(Model, self).__init__()

        self.date = None
        self.date_str = None
        self.date_int = None

        self.dir_config = None
        self.dir_temp = None

    def debug_vars(self):
        return [
                'date_str', self.date_str,
                'date_int', self.date_int,
                'dir_config', self.dir_config,
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

        self.jobs = []
        self.total_stored_files = 0

    def debug_vars(self):
        return [
                'jobs', self.jobs
                ]


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _(state):
    pass


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(params):
    model = Model()

    err = 0
    msgs = []

    # Date string
    date = params.get('datetime', None)
    if date:
        model.date = date
        model.date_str = date.strftime('%Y-%m-%d_%H-%M')
    else:
        msgs.append('datetime')

    # Date integer
    date_int = params.get('date_int', None)
    if date_int:
        model.date_int = date_int
    else:
        msgs.append('date_int')

    # Config directory
    dir_config = params.get('dir_config', None)
    if dir_config:
        model.dir_config = dir_config
    else:
        msgs.append('dir_config')

    # Temporary work directory
    dir_temp = params.get('dir_temp', None)
    if dir_temp:
        model.dir_temp = dir_temp
    else:
        msgs.append('dir_temp')

    if msgs:
        err = 1
        msgs.insert("App model missing:")

    return model, err, ', '.join(msgs)


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(params):
    '''
    Initialize model and state with params:
        - datetime
        - date_int
        - dir_config
        - dir_temp
    '''
    _D.DEBUG(
            __name__,
            "App init"
            )

    # Model
    model, err, msg = _init_model(params)
    if err:
        return None, err, msg

    # State
    state = State(model)

    # Runlogr state
    runlogrstate, err, msg = runlogr.init(
            os.path.join(model.dir_temp, '..', 'runlog.ini'))
    if err:
        return None, err, msg

    state.states.runlogr = runlogrstate

    # Debug config
    _D.OBJECT(
            __name__,
            "App model",
            state.model
            )

    # Description for reporting
    state.set_description("Aeroback")

    # Descriptors for reporting
    state.set_descriptor('Configuration', '')

    # Stats for reporting
    state.set_stats('Stats:', '')

    return state, err, msg


#-----------------------------------------------------------------------
# Validate state
#-----------------------------------------------------------------------
def _validate_state(state, params):
    return 0, None


#-----------------------------------------------------------------------
# Execute app
#-----------------------------------------------------------------------
def _execute_config(state):
    # Find all config files
    cfgs = []
    for root, subfolders, files in os.walk(state.model.dir_config):
        if root.find('EXAMPLES') != -1:
            continue
        for f in files:
            # Skip inactive files
            if f.startswith('OFF'):
                continue
            # Skip notify config files
            if f.startswith('notify-'):
                continue
            # Add file to list if has matching extension
            if f.endswith('.ini'):
                cfgs.append(os.path.join(root, f))

    if not cfgs:
        return 1, "No valid configs found in {}".format(state.model.dir_config)

    # Parse found config files
    config_names = []
    for f in cfgs:
        params, err, msg = jobconfr.parse(f)
        if err == 0:
            state.jobs.append(params)
            config_names.append(os.path.basename(f))

            '''
            _D.DEBUG(
                    __name__,
                    "CONFIG",
                    'params', params
                    )
            '''

        elif err == 1:  # Error processing config, do nothing
            _D.ERROR(
                    __name__,
                    "Config parsing error(s)",
                    'msg', msg
                    )

        elif err == 2:  # Config doesn't match this machine, do nothing
            _D.DEBUG(
                    __name__,
                    "Skipping not matching config",
                    'msg', msg
                    )

    if not state.jobs:
        return 1, "No configuration files were parsed"

    # Descriptor reporting
    state.set_descriptor('Configuration', config_names)
    return 0, None


#-----------------------------------------------------------------------
# Execute backup type
#-----------------------------------------------------------------------
def _exec_backup_type(state, storstate, params, dir_temp):
    '''
    _D.DEBUG(
            __name__,
            "Backup",
            'params', params
            )
    '''

    # Import and execute corresponding backupr type
    try:
        t = params['type']
        if t == 'db_mongo' or t == 'db_mysql':
            modname = 'feedr_db'
        elif t == 'dir_compress':
            modname = 'feedr_dir_compress'
        elif t == 'dir_increment':
            modname = 'feedr_dir_increment'

        if not modname:
            return 1, "Feeder not found for type:{}".format(t)

        # Import module
        backupr = importlib.import_module(
                    ".{}".format(modname),
                    'aeroback.app')

        # Backuper init
        backrstate, err, msg = backupr.init(
                state.model.date_str,
                state.model.date_int,
                dir_temp,
                storstate,
                params)
        if err:
            backrstate.add_msg_error("Error in init")
            return 1, "Error in feeder init: {}".format(msg)

        # Backuper execute
        err, msg = backupr.execute(backrstate)
        if err:
            backrstate.add_msg_error("Error in execute")
            return 1, "Error in feeder execute: {}".format(msg)

        # Backuper cleanup
        backupr.cleanup(backrstate)

    except Exception:
        # In case diagnostics function throws up
        try:
            _D.EXCEPTION(
                    __name__,
                    "Exception executing backup"
                    )
            # Log in state
            backrstate.add_msg_error("Exception")

        except:
            import sys
            import traceback
            traceback.print_exc(file=sys.stdout)
            return 0, None

    # Build backup summary only if
    # at least 1 file was transferred
    # or errors/warnings present
    if backrstate.total_stored_files or backrstate.get_msgs_warning() or backrstate.get_msgs_error():
        # Increase global file counter
        state.total_stored_files += backrstate.total_stored_files
        # Add summary for this backup
        _D.SUMMARY(
                backrstate.get_description(),
                backrstate.get_descriptors(),
                backrstate.get_stats(),
                backrstate.get_msgs_info(),
                backrstate.get_msgs_warning(),
                backrstate.get_msgs_error()
                )
    return 0, None


#-----------------------------------------------------------------------
# Execute job
#-----------------------------------------------------------------------
def _time_to_run(last_run, now, period):
    if not last_run:
        return True
    if not period:
        return True
    period = datetime.timedelta(minutes = period)
    return now > last_run + period


#-----------------------------------------------------------------------
# Execute job
#-----------------------------------------------------------------------
def _exec_job(state, job, job_n, jobs_count):
    # Init & exec each active storage
    err, msg = context.set_param('gsutil', job['gsutil'])
    if err:
        return 1, msg

    # Report errors and keep working
    # allow the job run on healthy storages
    job['storstates'] = []
    for storparams in job['storages']:
        if storparams['active']:

            # Create temp storager directory
            dir_temp = tempfile.mkdtemp(dir = state.model.dir_temp)

            # Init storager
            storstate, err, msg = storager.init(
                    state.model.date_str,
                    state.model.date_int,
                    dir_temp,
                    storparams
                    )
            if err:
                _D.ERROR(
                        __name__,
                        "Skipping storage due to error in init",
                        'msg', msg
                        )
                continue

            # Exec storager
            err, msg = storager.execute(storstate)
            if err:
                _D.ERROR(
                        __name__,
                        "Skipping storage due to error in exec",
                        'msg', msg
                        )
                continue

            # Add to list of storagers states
            job['storstates'].append(storstate)

    # Any storagers configured ?
    if not job['storstates']:
        return 1, "No storagers configured, aborting job"

    # ... do backup jobs ...

    # Run each backup type for each storage
    # Report errors and keep working
    for backup in job['backups']:
        if backup['active']:

            # Check previous backup finished
            section_name = "{}:{}".format(backup['type'], backup['dirstorage'])
            running = runlogr.get_section_item(
                    state.states.runlogr, section_name, 'running_bool')
            if running:
                msg = "Previous run of the backup is still marked as running. If you believe that's not the case then manually change in section [{}] paramter 'running' to False in file: {}".format(runlogr.get_filepath(state.states.runlogr))
                state.add_msg_error(msg)
                _D.ERROR(__name__, "Another instance may still be running", 'msg', msg)
                continue

            # Check if time to run
            # _time_to_run(last_run, now, period):
            if not _time_to_run(
                    runlogr.get_section_item(
                        state.states.runlogr, section_name, 'last_run_time'),
                    state.model.date,
                    backup.get('frequency', None)):
                # Time hasn't come yet, skip this backup
                continue

            # Update runlog with backup type
            runlogr.set_section(
                    state.states.runlogr,
                    section_name,
                    {'last_run_time': state.model.date, 'running_bool': True})

            # Run backup on each storage
            for storstate in job['storstates']:
                # Create unique temp directory inside dir_temp
                dir_temp = tempfile.mkdtemp(dir = state.model.dir_temp)
                # Execute
                err, msg = _exec_backup_type(state, storstate, backup, dir_temp)
                # Delete temp directory
                fsutil.remove_dir_tree(dir_temp)

                if err:
                    _D.ERROR(
                            __name__,
                            "Error executing backup",
                            'msg', msg,
                            'params', backup
                            )
                    continue

            # Update runlog with app finish
            runlogr.set_section(
                    state.states.runlogr,
                    section_name,
                    {'running_bool': False})

    # ... done backup jobs ...

    # Add storage stats to reporting
    for storstate in job['storstates']:
        cat = 'Job {}/{} uploaded'.format(job_n, jobs_count)
        state.set_descriptor_category(
                cat,
                storstate.model.atype,
                fmtutil.byte_size(storager.get_stored_stats(storstate)))

    # Cleanup storagers
    # Delete temp directory
    for storstate in job['storstates']:
        storager.cleanup(storstate)
        fsutil.remove_dir_tree(storstate.model.dir_temp)

    return 0, None


#-----------------------------------------------------------------------
# Validate jobs
#-----------------------------------------------------------------------
def _validate_jobs(jobs):
    '''
    Check no overlaps happening:
    - dirstorage must be unique for each backup
    '''

    dirstorages = {}
    msgs = []

    for job in jobs:
        backups = job.get('backups', None)
        if not backups:
            return 1, "No active backups found. Check your configuration."
        for backup in job['backups']:
            if backup['active']:
                this = backup['name']
                ds = backup['dirstorage']
                # Already used by another backup ?
                other = dirstorages.get(ds, None)
                if other:
                    msgs.append(
                        "Error in \"{}\": Storage dir \"{}\" already used by backup \"{}\"".format(
                            this, ds, other))
                else:
                    dirstorages[ds] = this

    if msgs:
        return 1, msgs
    else:
        return 0, None


#-----------------------------------------------------------------------
# Execute logic
#-----------------------------------------------------------------------
def _execute(state):
    # Read backup config files
    err, msg = _execute_config(state)
    if err:
        _D.ERROR(
                __name__,
                "Error reading job config",
                'msg', msg
                )
        return 0, None

    # If no matching jobs then finish
    if not state.jobs:
        _D.WARNING(
                __name__,
                "No matching backup jobs found, exiting"
                )
        return 0, None

    # Check jobs do not step on each other
    err, msg = _validate_jobs(state.jobs)
    if err:
        _D.ERROR(
                __name__,
                "Error validating jobs",
                'msg', msg
                )
        return 0, None

    # Empty temp directory before executing jobs
    fsutil.empty_dir(state.model.dir_temp)

    # Execute each job
    i = 0
    for job in state.jobs:
        i += 1
        err, msg = _exec_job(state, job, i, len(state.jobs))
        if err:
            _D.ERROR(
                    __name__,
                    "Error executing job",
                    'msg', msg
                    )
    # Done
    return 0, None


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):
    '''Execute state'''

    # Debug config
    _D.DEBUG(
            __name__,
            "App execute"
            )

    # Execute runlogr
    err, msg = runlogr.execute(state.states.runlogr)
    if err:
        _D.ERROR(__name__, "Error executing runlogr", 'msg', msg)
        return 0, None

    # Check if last run completed
    running = runlogr.get_section_item(state.states.runlogr, 'app', 'running_bool')
    if running:
        msg = "Oops, exiting. Another instance of Aeroback is still marked as running. If you believe that's not the case then manually change in section [app] paramter 'running' to False in file: {}".format(runlogr.get_filepath(state.states.runlogr))
        state.add_msg_error(msg)
        _D.ERROR(__name__, "Another instance may still be running", 'msg', msg)
        return 0, None

    # Update runlog with app start
    runlogr.set_section(
            state.states.runlogr,
            'app',
            {'last_run_time': state.model.date, 'running_bool': True})

    # Execute main logic inside try-catch because
    # we need to mark execution as finished
    # regardless of exception
    try:
        err, msg = _execute(state)
    except Exception as e:
        # Update runlog with app finish
        runlogr.set_section(
                state.states.runlogr,
                'app',
                {'running_bool': False})
        raise e

    # Update runlog with app finish
    runlogr.set_section(
            state.states.runlogr,
            'app',
            {'running_bool': False})

    return 0, None


#-----------------------------------------------------------------------
# Report needed ?
#-----------------------------------------------------------------------
def report_needed(state):
    # If any errors happened then report
    if _D.count_exceptions() or _D.count_errors() or _D.count_warnings():
        return True

    # If some files were stored then report
    if state.total_stored_files:
        return True

    # Otherwise don't report
    return False


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''
    _D.DEBUG(
            __name__,
            "App cleanup"
            )

    # Report execution time
    duration = datetime.datetime.today() - state.model.date
    duration = int(duration.total_seconds())
    state.set_stats('Execution time, h:m:s', str(datetime.timedelta(seconds = duration)))
    '''
    # Alternative method, very cool
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print "%d:%02d:%02d" % (h, m, s)
    '''

    # Errors and warnings summary
    count = _D.count_exceptions()
    if count > 0:
        state.add_msg_error("Exception(s) count: {}".format(count))
    count = _D.count_errors()
    if count > 0:
        state.add_msg_error("Error(s) count: {}".format(count))
    count = _D.count_warnings()
    if count > 0:
        state.add_msg_warning("Warning(s) count: {}".format(count))

    # Build backup summary
    _D.SUMMARY(
            state.get_description(),
            state.get_descriptors(),
            state.get_stats(),
            state.get_msgs_info(),
            state.get_msgs_warning(),
            state.get_msgs_error()
            )
