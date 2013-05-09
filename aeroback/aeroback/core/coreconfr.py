import os

#-----------------------------------------------------------------------
import aeroback.util.conf as confutil

#-----------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------
_model = {
        'app': [
            'name',
            'version'
            ],
        'logging': [
            'output',
            'file',
            'history_size'
            ],
        'config': [
            'dir'
            ],
        'resources': [
            'dir'
            ],
        'work': [
            'dir',
            'dir_log',
            'dir_diagnostics',
            'dir_temp'
            ],
        }


#-----------------------------------------------------------------------
# Build path
#-----------------------------------------------------------------------
def _build_path(*args):
    return os.path.normpath(os.path.join(*args))


#-----------------------------------------------------------------------
# Parse config file
#-----------------------------------------------------------------------
def parse(state, filepath):
    # Check file is present
    if not os.path.exists(filepath):
        return 1, "Config file not found: {}".format(filepath)

    # Load config file
    parser, err, msg = confutil.config_parser_improved(filepath)
    if err:
        return err, msg

    # Check config matches model
    global _model
    err, msg = parser.validate(_model)
    if err:
        return err, '\n'.join(["Error parsing {}".format(filepath), msg])

    # Fill in state:

    # App info
    state.name = parser.get('app', 'name')
    state.version = parser.get('app', 'version')

    # Logging
    state.log_output = parser.get('logging', 'output')
    state.log_filename_tpl = parser.get('logging', 'file')
    state.log_history_size = parser.getint('logging', 'history_size')

    # Resources
    state.dir_resources = _build_path(state.model.dir_app, parser.get('resources', 'dir'))

    # Configuration
    state.dir_config = _build_path(state.model.dir_app, parser.get('config', 'dir'))

    # Work and its subdirs: log, diag, temp
    state.dir_work = _build_path(state.model.dir_app, parser.get('work', 'dir'))
    state.dir_log = _build_path(state.dir_work, parser.get('work', 'dir_log'))
    state.dir_diagnostics = _build_path(state.dir_work, parser.get('work', 'dir_diagnostics'))
    state.dir_temp = _build_path(state.dir_work, parser.get('work', 'dir_temp'))

    # Done
    return 0, None
