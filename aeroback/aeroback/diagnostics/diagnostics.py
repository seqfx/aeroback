import sys
import traceback
import logging

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import xtermr
import htmlr


#-----------------------------------------------------------------------
# Module variables
_state = None


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self, htmlrstate):
        super(Model, self).__init__()
        self.htmlrstate = htmlrstate


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model

        self.count_exc = 0
        self.count_err = 0
        self.count_warn = 0

    def debug_vars(self):
        return [
                'state', 'diagnostics'
                ]


#-----------------------------------------------------------------------
# Get statistics
#-----------------------------------------------------------------------
def count_exceptions():
    if _state:
        return _state.count_exc
    else:
        return -1


#-----------------------------------------------------------------------
def count_errors():
    if _state:
        return _state.count_err
    else:
        return -1


#-----------------------------------------------------------------------
def count_warnings():
    if _state:
        return _state.count_warn
    else:
        return -1


#-----------------------------------------------------------------------
def _append_var(atype, out, label, value):
    xtermr.add_var(out, label, value)
    if _state:
        htmlr.add_var(_state.model.htmlrstate, atype, label, value)


#-----------------------------------------------------------------------
# Builders
#-----------------------------------------------------------------------
def _build(atype, class_name, comment, *args):
    out = []

    # Header
    if class_name:
        xtermr.add_class_name(out, class_name)

    # Xterm add title
    xtermr.add_title(atype, out, comment)

    # HTMLr open unit
    if _state:
        htmlr.open_unit(_state.model.htmlrstate, atype, class_name, comment)

    # Variables
    count = len(args) / 2
    i = 0
    j = 0
    while j < count:
        # Append variable
        _append_var(atype, out, args[i], args[i + 1])
        i += 2
        j += 1

    # Output to logger
    logging.debug('\n'.join(out))

    # HTMLr close unit
    if _state:
        htmlr.close_unit(_state.model.htmlrstate, atype)


#-----------------------------------------------------------------------
def _build_object(class_name, comment, obj):
    atype = 'debug'
    out = []

    # Header
    if class_name:
        xtermr.add_class_name(out, class_name)

    # Xterm add title
    xtermr.add_title(atype, out, comment)

    # HTMLr open unit
    if _state:
        htmlr.open_unit(_state.model.htmlrstate, atype, class_name, comment)

    # Variables
    debug_vars = getattr(obj, 'debug_vars', None)
    if callable(debug_vars):
        args = obj.debug_vars()
        if args:
            count = len(args) / 2
            i = 0
            j = 0
            while j < count:
                # Append variable
                _append_var(atype, out, args[i], args[i + 1])
                i += 2
                j += 1
    else:
        _append_var(atype, out, 'warning', 'This object needs to implement debug_vars()')

    # Output to logger
    logging.debug('\n'.join(out))

    # HTMLr close unit
    if _state:
        htmlr.close_unit(_state.model.htmlrstate, atype)


#-----------------------------------------------------------------------
def _build_exception(class_name, comment):
    atype = 'error'
    out = []

    # Header
    if class_name:
        xtermr.add_class_name(out, class_name)

    # Xterm add title
    xtermr.add_title(atype, out, comment)

    # HTMLr open unit
    if _state:
        htmlr.open_unit(_state.model.htmlrstate, atype, class_name, comment)

    # Get exception info
    (exc_type, exc_value, exc_traceback) = sys.exc_info()

    # Exception type and value
    if exc_type:
        exc_type = exc_type.__name__
    else:
        exc_type = 'None'

    if not exc_value:
        exc_value = 'None'

    _append_var(atype, out, 'exc', exc_type)
    _append_var(atype, out, 'msg', exc_value)

    # Stack trace
    xtermr.add_stack_trace_separator(out)
    tb = traceback.extract_tb(exc_traceback)
    tb.reverse()
    for t in tb:
        t_file = t[0]
        t_line = t[1]
        t_func = t[2]
        t_text = t[3]
        xtermr.add_stack_trace_entry(out, t_file, t_line, t_func, t_text)
        if _state:
            htmlr.add_stack_trace_entry(_state.model.htmlrstate, t_file, t_line, t_func, t_text)

    # Output to logger
    logging.debug('\n'.join(out))

    # HTMLr close unit
    if _state:
        htmlr.close_unit(_state.model.htmlrstate, atype)


#-----------------------------------------------------------------------
def _build_summary(title, descriptors, stats, infos, warnings, errors):
    # XTERMr
    '''
    out = []
    xtermr.add_summary_stats(out, title, *args)
    logging.debug('\n'.join(out))
    '''

    # HTMLr
    if _state:
        htmlr.add_summary(_state.model.htmlrstate,
                title, descriptors, stats, infos, warnings, errors)


#-----------------------------------------------------------------------
# OBJECT
#-----------------------------------------------------------------------
def OBJECT(class_name, comment, obj):
    _build_object(class_name, comment, obj)


#-----------------------------------------------------------------------
# DEBUG
#-----------------------------------------------------------------------
def DEBUG(class_name, comment, *args):
    _build('debug', class_name, comment, *args)


#-----------------------------------------------------------------------
# WARNING
#-----------------------------------------------------------------------
def WARNING(class_name, comment, *args):
    _state.count_warn += 1
    _build('warning', class_name, comment, *args)


#-----------------------------------------------------------------------
# ERROR
#-----------------------------------------------------------------------
def ERROR(class_name, comment, *args):
    _state.count_err += 1
    _build('error', class_name, comment, *args)


#-----------------------------------------------------------------------
# EXCEPTION
#-----------------------------------------------------------------------
def EXCEPTION(class_name, comment):
    _state.count_exc += 1
    _build_exception(class_name, comment)


#-----------------------------------------------------------------------
# SUMMARY
#-----------------------------------------------------------------------
def SUMMARY(title, descriptors, stats, infos, warnings, errors):
    '''
    title - string
    descriptors - dict
    stats - dict
    infos - list
    warnings - list
    errors - list
    '''
    _build_summary(title, descriptors, stats, infos, warnings, errors)


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(htmlrstate):
    # HTMLr state
    if not htmlrstate:
        return None, 1, "HTMLr state must be provided"

    return Model(htmlrstate), 0, None


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model):
    return State(model), 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(htmlrstate):
    ''' Initialize model and state'''

    model, err, msg = _init_model(htmlrstate)
    if err:
        return None, err, msg

    global _state
    _state, err, msg = _init_state(model)
    return _state, err, msg


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):
    '''Execute state'''
    err = 0
    msg = None
    try:
        pass

    except Exception:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        err = 1
        msg = "{}: Error in execute: {}".format(__name__, exc_value)

    finally:
        return err, msg


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''
    pass


#-----------------------------------------------------------------------
# Fall back logging config: print to screen
#-----------------------------------------------------------------------
'''
print "LOG DEFAULT CONFIG >>>>> SCREEN"
logging.basicConfig(
        level = logging.DEBUG,
        format = '%(message)s'
        )
'''
