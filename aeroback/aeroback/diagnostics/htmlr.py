import os.path
import sys
import string

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.util.fs as fsutil

'''
HTML renderer module:
- HTML color formatting
- writing output to HTML file
'''


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self, dir_resource, dir_work, filename):
        super(Model, self).__init__()
        self.dir_resource = dir_resource
        self.dir_work = dir_work
        self.filename = filename


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model
        self.active = None

        # Filenames for different temp files
        self.all_filename = None
        self.warn_filename = None
        self.err_filename = None
        self.log_filename = None

        # Full filepaths
        self.all_filepath = None
        self.warn_filepath = None
        self.err_filepath = None
        self.log_filepath = None

        # Temp file
        self.all_file_handle = None
        self.warn_file_handle = None
        self.err_file_handle = None

        # Template fragments
        self.DOC_S = None
        self.DOC_E = None

        self.SUMM_STATS_S = None
        self.SUMM_STATS_LI = None
        self.SUMM_STATS_E = None

        self.SUMM_ERRS = None
        self.SUMM_WARNS = None
        self.SUMM_LOGS = None

        self.UNIT_S = None
        self.UNIT = None
        self.UNIT_E = None

        self.VAR_S = None
        self.VAR_E = None
        self.VAR_LI = None

        self.TRACE_LI = None

        # Counts
        self.err_count = 0
        self.warn_count = 0

        # Summary
        self.summaries = []

    def debug_vars(self):
        return [
                'state', 'htmlr'
                ]


#-----------------------------------------------------------------------
# Open unit type
#-----------------------------------------------------------------------
def _open_unit(state, fh, atype, href, module, msg):
    fh.write(
            state.UNIT_S.safe_substitute(
                {
                    'atype': atype,
                    'href': href,
                    'module': module,
                    'msg': msg
                }
                )
            )


def _open_unit_all(state, fh, atype, module, msg, href_id):
    if href_id:
        href = "<div><a name=\"{0}-{1}\"></a><a href=\"#{0}-{1}-back\">back</a></div>".format(atype, href_id)
    else:
        href = ''

    _open_unit(state, fh, atype, href, module, msg)


def _open_unit_warn_err(state, fh, atype, module, msg, href_id):
    if href_id:
        href = "<div><a name=\"{0}-{1}-back\"></a><a href=\"#{0}-{1}\">{0}-{1}</a></div>".format(atype, href_id)
    else:
        href = ''

    _open_unit(state, fh, atype, href, module, msg)


#-----------------------------------------------------------------------
# Open unit
#-----------------------------------------------------------------------
def open_unit(state, atype, module, msg):
    if not state.active:
        return

    if atype is 'debug':
        _open_unit_all(state, state.all_file_handle, 'debug', module, msg, None)

    elif atype is 'warning':
        state.warn_count += 1
        _open_unit_all(state, state.all_file_handle, 'warning', module, msg, state.warn_count)
        _open_unit_warn_err(state, state.warn_file_handle, 'warning', module, msg, state.warn_count)

    elif atype is 'error':
        state.err_count += 1
        _open_unit_all(state, state.all_file_handle, 'error', module, msg, state.err_count)
        _open_unit_warn_err(state, state.err_file_handle, 'error', module, msg, state.err_count)

    else:
        _open_unit(state, state.all_file_handle, 'debug', module, msg)


#-----------------------------------------------------------------------
# Close unit type
#-----------------------------------------------------------------------
def _close_unit(state, fh):
    fh.write(
        state.UNIT_E.safe_substitute(
            {}
            )
        )


#-----------------------------------------------------------------------
# Close unit
#-----------------------------------------------------------------------
def close_unit(state, atype):
    if not state.active:
        return

    if atype is 'debug':
        _close_unit(state, state.all_file_handle)

    elif atype is 'warning':
        _close_unit(state, state.all_file_handle)
        _close_unit(state, state.warn_file_handle)

    elif atype is 'error':
        _close_unit(state, state.all_file_handle)
        _close_unit(state, state.err_file_handle)

    else:
        _close_unit(state, state.all_file_handle)


#-----------------------------------------------------------------------
# Add var formatted as out
#-----------------------------------------------------------------------
def _add_var(state, atype, out):
    # Save to all.log
    for line in out:
        state.all_file_handle.write(line)

    # Save to additional logs
    if atype is 'warning':
        for line in out:
            state.warn_file_handle.write(line)

    elif atype is 'error':
        for line in out:
            state.err_file_handle.write(line)


#-----------------------------------------------------------------------
# Add var None
#-----------------------------------------------------------------------
def _add_var_none(state, atype, label):
    # Build
    out = []
    out.append(
            state.VAR_S.safe_substitute(
                {
                    'label': label,
                    'value': '<span style="color: red;">None</span>'
                }
            )
            )

    # Close
    out.append(
            state.VAR_E.safe_substitute(
                {}
            )
            )

    # Output result
    _add_var(state, atype, out)


#-----------------------------------------------------------------------
# Add var simple
#-----------------------------------------------------------------------
def _add_var_simple(state, atype, label, value):
    # Build
    out = []
    out.append(
            state.VAR_S.safe_substitute(
                {
                    'label': label,
                    'value': str(value)
                }
            )
            )

    # Close
    out.append(
            state.VAR_E.safe_substitute(
                {}
            )
            )

    # Output result
    _add_var(state, atype, out)


#-----------------------------------------------------------------------
# Add var list
#-----------------------------------------------------------------------
def _add_var_list(state, atype, label, values):
    out = []

    # Label
    out.append(
            state.VAR_S.safe_substitute(
                {
                    'label': label,
                    'value': '[...]'
                }
            )
            )

    # List values
    i = 0
    for v in values:
        out.append(
                state.VAR_LI.safe_substitute(
                    {
                        'label': str(i),
                        'value': str(v)
                        # 'value': add_var(state, atype, str(i), v)
                    }
                )
                )
        i += 1

    # Close
    out.append(
            state.VAR_E.safe_substitute(
                {}
            )
            )

    # Output result
    _add_var(state, atype, out)


#-----------------------------------------------------------------------
# Add var dictionary
#-----------------------------------------------------------------------
def _add_var_dictionary(state, atype, label, values):
    out = []

    # Label
    out.append(
            state.VAR_S.safe_substitute(
                {
                    'label': label,
                    'value': '[...]'
                }
            )
            )

    # List values
    for k in values.keys():
        v = values[k]
        out.append(
                state.VAR_LI.safe_substitute(
                    {
                        'label': str(k),
                        'value': str(v)
                        # 'value': add_var(state, atype, k, v)
                    }
                )
                )

    # Close
    out.append(
            state.VAR_E.safe_substitute(
                {}
            )
            )

    # Output result
    _add_var(state, atype, out)


#-----------------------------------------------------------------------
# Add var...
#-----------------------------------------------------------------------
def add_var(state, atype, label, value):
    if not state.active:
        return

    # Value is None ?
    if value is None:
        _add_var_none(state, atype, label)
        return

    # Has debug_vars() function ?
    debug_vars = getattr(value, 'debug_vars', None)
    if callable(debug_vars):
        add_var(state, atype, label, '<hr />')
        # Dig deeper
        args = value.debug_vars()
        if args:
            count = len(args) / 2
            i = 0
            j = 0
            while j < count:
                add_var(state, atype, args[i], args[i + 1])
                i += 2
                j += 1
        return

    # List or tuple ?
    if isinstance(value, (list, tuple)):
        _add_var_list(state, atype, label, value)

    # Dictionary ?
    elif isinstance(value, dict):
        _add_var_dictionary(state, atype, label, value)

    # All others...
    else:
        _add_var_simple(state, atype, label, value)


#-----------------------------------------------------------------------
# Add stack trace item
#-----------------------------------------------------------------------
def add_stack_trace_entry(state, t_file, t_line, t_func, t_text):
    if not state.active:
        return

    state.all_file_handle.write(
            state.TRACE_LI.safe_substitute(
                {
                    'file': t_file,
                    'function': t_func,
                    'line': t_line,
                    'text': t_text
                }
            )
            )


#-----------------------------------------------------------------------
# Add summary stats
#-----------------------------------------------------------------------
def add_summary(state, title, descriptors, stats, infos, warnings, errors):
    '''
    title - string
    descriptors - dict
    stats - dict
    infos - list
    warnings - list
    errors - list
    '''
    if not state.active:
        return

    state.summaries.append(
                {
                    'title': title,
                    'descriptors': descriptors,
                    'stats': stats,
                    'infos': infos,
                    'warnings': warnings,
                    'errors': errors
                }
            )


#-----------------------------------------------------------------------
# Build summary stats
#-----------------------------------------------------------------------
def _flatten_data(arg):

    # Dictionary ?
    if isinstance(arg, dict):
        out = []
        for key in arg:
            out.append("<span style='color:gray'>{} =</span> {}".format(key, arg[key]))
        return ', '.join(out)

    # List or tuple ?
    if isinstance(arg, (list, tuple)):
        out = []
        for v in arg:
            out.append(v)
        return ', '.join(out)

    else:
        return str(arg)


#-----------------------------------------------------------------------
def _build_summary(state, fh, summary):
    # Title
    fh.write(
            state.SUMM_STATS_S.safe_substitute(
                {
                    'title': summary['title']
                }
                )
            )

    # Descriptors, {}
    data = summary['descriptors']
    for key in data:
        fh.write(
                state.SUMM_STATS_LI.safe_substitute(
                    {
                        'atype': 'neutral',
                        'label': key,
                        'value': _flatten_data(data[key])
                    }
                    )
                )

    # Stats, {}
    data = summary['stats']
    for key in data:
        fh.write(
                state.SUMM_STATS_LI.safe_substitute(
                    {
                        'atype': 'yellow',
                        'label': key,
                        'value': _flatten_data(data[key])
                    }
                    )
                )

    # Infos, []
    data = summary['infos']
    for val in data:
        fh.write(
                state.SUMM_STATS_LI.safe_substitute(
                    {
                        'atype': 'lblue',
                        'label': 'Info',
                        'value': val
                    }
                    )
                )

    # Warnings, []
    data = summary['warnings']
    for val in data:
        fh.write(
                state.SUMM_STATS_LI.safe_substitute(
                    {
                        'atype': 'orange',
                        'label': 'Warning',
                        'value': val
                    }
                    )
                )

    # Errors, []
    data = summary['errors']
    for val in data:
        fh.write(
                state.SUMM_STATS_LI.safe_substitute(
                    {
                        'atype': 'red',
                        'label': 'Error',
                        'value': val
                    }
                    )
                )

    # Summary end
    fh.write(
            state.SUMM_STATS_E.safe_substitute(
                {}
                )
            )


def _build_add_summary_stats(state, fh):
    state.summaries.reverse()
    for summary in state.summaries:
        _build_summary(state, fh, summary)

    '''
        # Summ items
        data = summary['data']
        i = 0
        while (i + 1) < len(data):

            label = data[i]
            if not label:
                label = '&nbsp;'

            value = data[i + 1]

            if value is 'OK':
                atype = 'green'

            elif value is 'WARNING':
                atype = 'orange'

            elif value is 'ERROR':
                atype = 'red'

            elif value is 'None':
                atype = 'inverse'

            elif not value:
                atype = 'clear'
                value = '&nbsp;'

            else:
                atype = 'neutral'

            fh.write(
                    state.SUMM_STATS_LI.safe_substitute(
                        {
                            'atype': atype,
                            'label': label,
                            'value': value
                        }
                        )
                    )
            i += 2
    '''


#-----------------------------------------------------------------------
# Open HTML file for writing
#-----------------------------------------------------------------------
def _open_output(state):
    # Open in append mode
    state.all_file_handle = open(state.all_filepath, 'a')
    state.warn_file_handle = open(state.warn_filepath, 'a')
    state.err_file_handle = open(state.err_filepath, 'a')


#-----------------------------------------------------------------------
# Close opened HTML file
#-----------------------------------------------------------------------
def _close_output(state):
    if state.all_file_handle:
        state.all_file_handle.close()
        state.all_file_handle = None

    if state.warn_file_handle:
        state.warn_file_handle.close()
        state.warn_file_handle = None

    if state.err_file_handle:
        state.err_file_handle.close()
        state.err_file_handle = None


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _read_template(path, filename):
    tpl = "Template not found"
    with open(os.path.join(path, filename), 'r') as f:
        tpl = f.read()
    return string.Template(tpl)


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _read_templates(state):
    dir_resource = state.model.dir_resource

    # Doc
    state.DOC_S = _read_template(dir_resource, 'doc-start.html')
    state.DOC_E = _read_template(dir_resource, 'doc-end.html')

    # Summary stats
    state.SUMM_STATS_S = _read_template(dir_resource, 'summary-stats-start.html')
    state.SUMM_STATS_LI = _read_template(dir_resource, 'summary-stats-item.html')
    state.SUMM_STATS_E = _read_template(dir_resource, 'summary-stats-end.html')

    # Summary errors
    state.SUMM_ERRS = _read_template(dir_resource, 'summary-errors.html')

    # Summary warnings
    state.SUMM_WARNS = _read_template(dir_resource, 'summary-warnings.html')

    # Summary logs
    state.SUMM_LOGS = _read_template(dir_resource, 'summary-logs.html')

    # Unit
    state.UNIT_S = _read_template(dir_resource, 'unit-start.html')
    state.UNIT = _read_template(dir_resource, 'unit.html')
    state.UNIT_E = _read_template(dir_resource, 'unit-end.html')

    # Var
    state.VAR_S = _read_template(dir_resource, 'var-start.html')
    state.VAR_LI = _read_template(dir_resource, 'var-list-item.html')
    state.VAR_E = _read_template(dir_resource, 'var-end.html')

    # Stack trace list item
    state.TRACE_LI = _read_template(dir_resource, 'trace-item.html')


#-----------------------------------------------------------------------
# Build add errors
#-----------------------------------------------------------------------
def _build_add_errors(state, fh):
    if not state.err_count:
        return

    # Errors summary
    fh.write(
            state.SUMM_ERRS.safe_substitute(
                {'count': state.err_count}
                )
            )

    # Add all errors
    with open(state.err_filepath, 'r') as ff:
        for line in ff:
            fh.write(line)


#-----------------------------------------------------------------------
# Build add errors
#-----------------------------------------------------------------------
def _build_add_warnings(state, fh):
    if not state.warn_count:
        return

    # Warnings summary
    fh.write(
            state.SUMM_WARNS.safe_substitute(
                {'count': state.warn_count}
                )
            )

    # Add all errors
    with open(state.warn_filepath, 'r') as ff:
        for line in ff:
            fh.write(line)


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(dir_resource, dir_work, filename):

    # Resource directory
    if not os.path.exists(dir_resource):
        return None, 1, "HTML Diags Resource directory does not exist: {}".format(dir_resource)

    # Working dir
    if not os.path.exists(dir_work):
        return None, 1, "HTML Diags Work directory does not exist: {}".format(dir_work)

    err, msg = fsutil.empty_dir(dir_work)
    if err:
        return None, err, "Diagnostic directory cannot be emptied: {}".format(msg)

    err, msg = fsutil.ensure_dir(dir_work)
    if err:
        return None, err, msg

    # HTML log filename
    if not filename:
        return None, 1, "HTML log filename must be provided"

    return Model(dir_resource, dir_work, filename), 0, None


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model):
    state = State(model)
    filename = model.filename
    dir_work = model.dir_work

    state.all_filename = "{}.all.html".format(filename)
    state.warn_filename = "{}.warn.html".format(filename)
    state.err_filename = "{}.err.html".format(filename)
    state.log_filename = "{}.html".format(filename)

    state.all_filepath = os.path.join(dir_work, state.all_filename)
    state.warn_filepath = os.path.join(dir_work, state.warn_filename)
    state.err_filepath = os.path.join(dir_work, state.err_filename)
    state.log_filepath = os.path.join(dir_work, state.log_filename)

    return state, 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(dir_resource, dir_work, filename):
    ''' Initialize model and state'''

    model, err, msg = _init_model(dir_resource, dir_work, filename)
    if err:
        return None, err, msg

    return _init_state(model)


#-----------------------------------------------------------------------
# Execute
#-----------------------------------------------------------------------
def execute(state):
    # Load all templates and open file for writing
    err = 0
    msg = None
    try:
        _read_templates(state)
        _open_output(state)
        state.active = True

    except Exception:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        err = 1
        msg = "{}: Error in execute: {}".format(__name__, exc_value)

    finally:
        return err, msg


#-----------------------------------------------------------------------
# Cleanup
#-----------------------------------------------------------------------
def cleanup(state):
    state.active = False

    # Close for writing and open for reading
    _close_output(state)

    # Open log in append mode
    with open(state.log_filepath, 'a') as f:

        # Doc start
        f.write(
                state.DOC_S.safe_substitute(
                    {}
                    )
                )

        # Summary stats
        _build_add_summary_stats(state, f)

        # Add all errors
        _build_add_errors(state, f)

        # Add all warnings
        _build_add_warnings(state, f)

        # Summary logs
        f.write(
                state.SUMM_LOGS.safe_substitute(
                    {}
                    )
                )

        # Add all log messages
        with open(state.all_filepath, 'r') as ff:
            for line in ff:
                f.write(line)

        # Doc end
        f.write(
                state.DOC_E.safe_substitute(
                    {}
                    )
                )
