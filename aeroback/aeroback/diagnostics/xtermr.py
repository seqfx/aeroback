# ANSI XT color formatting


#-----------------------------------------------------------------------
# Terminal styles
#-----------------------------------------------------------------------
class XT:
    WHITE = '\033[37m'
    CYAN = '\033[36m'
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CLEAR = '\033[0m'

    UNDERLINE = '\033[4m'
    UNDERLINE_WHITE = '\033[4m\033[37m'
    UNDERLINE_BOLD_WHITE = '\033[4m\033[1m\033[37m'

    BOLD = '\033[1m'
    BOLD_CYAN = '\033[1m\033[36m'
    BOLD_PURPLE = '\033[1m\033[95m'
    BOLD_YELLOW = '\033[1m\033[93m'
    BOLD_RED = '\033[1m\033[91m'

    INVERSE_WHITE = '\033[7m\033[37m'
    INVERSE_PURPLE = '\033[7m\033[95m'
    INVERSE_BLUE = '\033[7m\033[94m'
    INVERSE_GREEN = '\033[7m\033[92m'
    INVERSE_YELLOW = '\033[7m\033[93m'

    def disable(self):
        self.HEADER = ''
        self.BLUE = ''
        self.GREEN = ''
        self.YELLOW = ''
        self.RED = ''
        self.CLEAR = ''


#-----------------------------------------------------------------------
# Variables
_sep = '_' * 100
_sep_bold = '|' + '=' * 99
_sep_border = '|' + '_' * 99


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def add_class_name(out, class_name):
    out.append("{}{}{}".format(
        XT.UNDERLINE,
        class_name,
        XT.CLEAR))


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _add_title_debug(out, msg):
    out.append("{}{}{}".format(
        XT.YELLOW,
        msg,
        XT.CLEAR))


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _add_title_warning(out, msg):
    out.append("{}{}{}".format(
        XT.INVERSE_YELLOW,
        msg,
        XT.CLEAR))


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _add_title_error(out, msg):
    out.append("{}{}{}".format(
        XT.BOLD_RED,
        msg,
        XT.CLEAR))


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _add_title_summary(out, msg):
    out.append("{}{}{}".format(
        XT.INVERSE_YELLOW,
        msg,
        XT.CLEAR))


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def add_title(atype, out, msg):
    if atype is 'debug':
        _add_title_debug(out, msg)

    elif atype is 'warning':
        _add_title_warning(out, msg)

    elif atype is 'error':
        _add_title_error(out, msg)

    elif atype is 'summary':
        _add_title_summary(out, msg)

    else:
        _add_title_debug(out, msg)


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _color_label(label):
    if label is 'TODO':
        return XT.INVERSE_GREEN
    if label is 'NOTE':
        return XT.INVERSE_GREEN
    else:
        return XT.GREEN


#-----------------------------------------------------------------------
# Add var
#-----------------------------------------------------------------------
def add_var(out, label, value, indent = 1):

    color_value = XT.WHITE
    TT = '\t' * indent

    # Value is None ?
    if value is None:
        out.append("*{}{}{} = {}{}{}".format(
            TT,
            _color_label(label),
            label,
            XT.INVERSE_WHITE,
            'None',
            XT.CLEAR
            ))
        return

    # Has debug_vars function ?
    debug_vars = getattr(value, 'debug_vars', None)
    if callable(debug_vars):
        # Label
        out.append("*{}{}{} = {}{}".format(
            TT,
            _color_label(label),
            label,
            '_' * 60,
            XT.CLEAR,
            ))
        # Dig deeper
        args = value.debug_vars()
        if args:
            count = len(args) / 2
            i = 0
            j = 0
            while j < count:
                add_var(out, args[i], args[i + 1], indent + 1)
                i += 2
                j += 1
        return

    # List or tuple ?
    if isinstance(value, (list, tuple)):
        out.append("*{}{}{} = [...]{}".format(
            TT,
            _color_label(label),
            label,
            XT.CLEAR,
            ))
        i = 0
        # For each value
        for e in value:
            add_var(out, i, e, indent + 1)
            '''
            out.append("*{}\t{}{} = {}{}{}{}".format(
                TT,
                _color_label(label),
                i,
                XT.CLEAR,
                color_value,
                e,
                XT.CLEAR
                ))
            '''
            i += 1

    # Dictionary ?
    elif isinstance(value, dict):
        out.append("*{}{}{} = {{...}}{}".format(
            TT,
            _color_label(label),
            label,
            XT.CLEAR,
            ))
        i = 0
        for k in value.keys():
            v = value[k]
            add_var(out, k, v, indent + 1)
            '''
            out.append("*{}\t{}{} = {}{}{}{}".format(
                TT,
                _color_label(label),
                k,
                XT.CLEAR,
                color_value,
                v,
                XT.CLEAR
                ))
            '''
            i += 1

    # All others...
    else:
        out.append("*{}{}{} = {}{}{}".format(
            TT,
            _color_label(label),
            label,
            color_value,
            value,
            XT.CLEAR
            ))


#-----------------------------------------------------------------------
# Stack trace
#-----------------------------------------------------------------------
def add_stack_trace_separator(out):
    out.append("")


def add_stack_trace_entry(out, t_file, t_line, t_func, t_text):
    out.append("\t{}{}{}".format(XT.PURPLE, t_file, XT.CLEAR))
    out.append("\t\t{}{}{}".format(XT.BLUE, t_func, XT.CLEAR))
    out.append("\t\t\t{} : {}{}{}".format(t_line, XT.WHITE, t_text, XT.CLEAR))
    out.append("")


#-----------------------------------------------------------------------
# Summary stats
#-----------------------------------------------------------------------
def add_summary_stats(out, title, *args):
    add_title('summary', out, title)
    i = 0
    while (i + 1) < len(args):
        add_var(out, args[i], args[i + 1])
        i += 2


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def add_color_test(out):
    out.append('| {}COLOR'.format(XT.PURPLE))
    out.append('| {}COLOR'.format(XT.BLUE))
    out.append('| {}COLOR'.format(XT.GREEN))
    out.append('| {}COLOR'.format(XT.YELLOW))
    out.append('| {}COLOR'.format(XT.RED))
    out.append('| {}COLOR'.format(XT.CLEAR))


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def to_string(out):
    return '\n'.join(out)
