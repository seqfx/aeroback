import os
import sys
import time
from datetime import datetime

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D
import aeroback.diagnostics.htmlr as htmlr

import coreconfr
import logconfr
import logcleanr

import aeroback.context.context as context
import aeroback.email.emailconfr as emailconfr
import aeroback.email.emailr as emailr

import aeroback.app.app_backup as app

import aeroback.util.fs as fsutil

'''
Core module:
- app running parameters
- app config
- set up debugging
- app start

Required modules:
    -

Children modules:
    - diagr
    - htmlr
'''


#-----------------------------------------------------------------------
# States for other modules
#-----------------------------------------------------------------------
class States(object):

    def __init__(self):
        self.diagr = None
        self.htmlr = None
        self.emailr = None

    def debug_vars(self):
        return [
                'diagr', self.diagr,
                'htmlr', self.htmlr,
                'emailr', self.emailr
                ]


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self, argv, dir_app, config_filepath):
        super(Model, self).__init__()
        self.argv = argv
        self.dir_app = dir_app
        self.config_filepath = config_filepath
        self.params = {}

    def debug_vars(self):
        return [
                'argv', self.argv,
                'dir_app', self.dir_app,
                'config', self.config_filepath,
                'params', self.params
                ]


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model

        self.states = States()

        # App info
        self.name = None
        self.version = None

        # Time stamp
        self.datetime = None
        self.date_int = None

        # Logging
        self.log_output = None
        self.log_filename_tpl = None
        self.log_filename = None
        self.log_history_size = None

        # Directories
        self.dir_resources = None
        self.dir_config = None
        self.dir_work = None
        self.dir_log = None
        self.dir_diagnostics = None
        self.dir_temp = None

        # Params
        self.params = {}

    def debug_vars(self):
        return [
                'app', self.name,
                'version', self.version,
                'date', self.datetime,
                'dir_resources', self.dir_resources,
                'dir_config', self.dir_config,
                'dir_work', self.dir_work,
                'dir_log', self.dir_log,
                'dir_diagnostics', self.dir_diagnostics,
                'dir_temp', self.dir_temp,
                'params', self.params
                ]


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _(state):
    pass


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(argv, config_filename):
    # Arguments
    if not argv:
        return None, 1, "Arguments must be provided"

    # App directory
    dir_app = os.path.dirname(os.path.realpath(sys.argv[0]))
    if not os.path.exists(dir_app):
        return None, 1, "App directory not found on disk: {}".format(dir_app)

    # Model: config file
    config_filepath = os.path.join(dir_app, config_filename)
    if not os.path.exists(config_filepath):
        return None, 1, "Config file not found on disk: {}".format(config_filepath)

    model = Model(argv, dir_app, config_filepath)

    # Global -dry option
    if '-dry' in argv:
        model.params['-dry'] = True
    else:
        model.params['-dry'] = False

    return model, 0, None


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model):
    state = State(model)

    # Time stamp
    state.datetime = datetime.now()
    state.date_int = int(time.mktime(state.datetime.timetuple()))

    return state, 0, None


#-----------------------------------------------------------------------
# Validate state
#-----------------------------------------------------------------------
def _validate_state(state):
    # App info
    if not state.name:
        return 1, "Application name must be provided"
    if not state.version:
        return 1, "Application version must be provided"

    # Logging
    if not state.log_output:
        return 1, "Logging output mode must be provided"
    if not state.log_filename_tpl:
        return 1, "Logging file name template must be provided"
    if not state.log_history_size:
        return 1, "Logging history size must be provided"

    # Resources dir
    if not os.path.exists(state.dir_resources):
        return 1, "Resource directory not found: {}".format(state.dir_resources)

    # Config dir
    if not os.path.exists(state.dir_config):
        return 1, "Config directory not found: {}".format(state.dir_config)

    # Work dir
    err, msg = fsutil.ensure_dir(state.dir_work)
    if err:
        return err, msg

    # Log dir
    err, msg = fsutil.ensure_dir(state.dir_log)
    if err:
        return err, msg

    # Diagnostics dir
    err, msg = fsutil.ensure_dir(state.dir_diagnostics)
    if err:
        return err, msg

    # Temp dir
    err, msg = fsutil.ensure_dir(state.dir_temp)
    if err:
        return err, msg

    return 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(argv, config_filename):
    ''' Initialize model and state'''

    # Create model
    model, err, msg = _init_model(argv, config_filename)
    if err:
        return None, err, msg

    # Init global context
    context.init(model.params)

    # Create state
    return _init_state(model)


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):
    '''Execute state'''

    # State: parse config file, validate state
    err, msg = coreconfr.parse(state, state.model.config_filepath)
    if err:
        return err, msg

    err, msg = _validate_state(state)
    if err:
        return err, msg

    # Configure global logging
    state.log_filename = state.log_filename_tpl.format(state.datetime.strftime('%Y-%m-%d_%H-%M-%S'))
    err, msg = logconfr.configure(state.log_output, state.dir_log, state.log_filename)
    if err:
        return err, msg

    # Configure global diagnostics HTML output
    htmlrstate, err, msg = htmlr.init(
            os.path.join(state.dir_resources, 'diag'),
            state.dir_diagnostics,
            state.log_filename
            )
    if err:
        return err, msg

    err, msg = htmlr.execute(htmlrstate)
    if err:
        return err, msg

    state.states.htmlr = htmlrstate

    # Configure global diagnostics
    diagrstate, err, msg = _D.init(htmlrstate)
    if err:
        return err, msg

    err, msg = _D.execute(diagrstate)
    if err:
        return err, msg

    state.states.diagr = diagrstate

    # >>> From here onwards we can use _D.XXXX <<<

    # Debug core
    _D.OBJECT(
            __name__,
            "Core model",
            state.model
            )

    _D.OBJECT(
            __name__,
            "Core state",
            state
            )

    # Configure email notification
    emailrparams, err, msg = emailconfr.parse(os.path.join(state.dir_config, 'notify-email.ini'))
    if err:
        return err, msg

    # Configure emailer
    emailrstate, err, msg = emailr.init(emailrparams)
    if err:
        return err, msg

    state.states.emailr = emailrstate
    state.params['emailr'] = emailrparams

    # Done
    return 0, None


#-----------------------------------------------------------------------
# Execute app
#-----------------------------------------------------------------------
def execute_app(state):
    err = 0
    msg = None
    try:
        # Init app
        appstate, err, msg = app.init(
                    {
                        'datetime': state.datetime,
                        'date_int': state.date_int,
                        'dir_config': state.dir_config,
                        'dir_temp': state.dir_temp
                    }
                )
        if err:
            _D.ERROR(
                    __name__,
                    "App failed to initialize, aborted",
                    'msg', msg
                    )
            return err, msg

        # Execute app
        err, msg = app.execute(appstate)
        if err:
            _D.ERROR(
                    __name__,
                    "App executed with error",
                    'msg', msg
                    )

        # Cleanup app
        app.cleanup(appstate)

    except Exception:
        # In case diagnostics function throws up
        try:
            _D.EXCEPTION(
                    __name__,
                    "App exception"
                    )
        except:
            import traceback
            traceback.print_exc(file=sys.stdout)

    finally:
        return err, msg


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''

    _D.DEBUG(__name__, "Core cleanup")

    # Clean up log files
    err, msg = logcleanr.clean(
            dir_log = state.dir_log,
            current = state.log_filename,
            filename_tpl = state.log_filename_tpl,
            history_size = state.log_history_size)

    # Cleanup diagnostics
    diagrstate = state.states.diagr
    if diagrstate:
        _D.cleanup(diagrstate)

    # Cleanup diagnostics HTML log
    htmlrstate = state.states.htmlr
    if htmlrstate:

        # Close HTML log
        htmlr.cleanup(htmlrstate)
        # >>> _D.XXXX calls after this point WILL NOT be saved to emailed log <<<

        # Email HTML log
        emailrstate = state.states.emailr
        emailrparams = state.params.get('emailr', None)
        if emailrstate and emailrparams:

            # Subject
            stats = []
            stats.append(emailrparams['subject'])
            stats.append('|')

            if diagrstate.count_err == 0 and diagrstate.count_warn == 0 and diagrstate.count_exc == 0:
                stats.append("OK")
            else:
                if diagrstate.count_err > 0:
                    stats.append("ERR={}".format(diagrstate.count_err))

                if diagrstate.count_exc > 0:
                    stats.append("EXC={}".format(diagrstate.count_exc))

                if diagrstate.count_warn > 0:
                    stats.append("WARN={}".format(diagrstate.count_warn))

            stats.append('|')
            stats.append(state.datetime.strftime('%H:%M, %a, %d %b %Y'))
            subject = ' '.join(stats)

            # Read message
            with open(htmlrstate.log_filepath) as f:
                messages = {
                        'text/html': f.read()
                        }

            # Attachments: none
            attachments = None

            # Send email
            err, msg = emailr.execute(
                    emailrstate,
                    emailrparams.get('from', None),
                    emailrparams.get('to', None),
                    subject,
                    messages,
                    attachments
                    )
            if err:
                _D.ERROR(
                        __name__,
                        "Error in emailer",
                        'msg', msg
                        )

            emailr.cleanup(emailrstate)

    # Summary of app errors and warnings
    _D.DEBUG(
            __name__,
            "App execution summary",
            'errors', diagrstate.count_err,
            'exceptions', diagrstate.count_exc,
            'warnings', diagrstate.count_warn
            )

    # Done
    return
