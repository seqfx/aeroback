

#-----------------------------------------------------------------------
# Parse size in bytes, K, M
#-----------------------------------------------------------------------
def bytesize(s):
    """Parses strings like 100, 10k, 100M. Returns count in bytes"""

    # All digits, simple case
    if s.isdigit():
        return int(s)

    # Parse string
    size = s[0:len(s) - 1]
    measure = s[-1:len(s)]

    if measure == 'k' or measure == 'K':
        return 1000 * int(size)
    elif measure == 'm' or measure == 'M':
        return 1000000 * int(size)
    elif measure == 'g' or measure == 'G':
        return 1000000000 * int(size)
    else:
        return -1


#-----------------------------------------------------------------------
# Parse time in minutes and hours
#-----------------------------------------------------------------------
def hours_minutes(s):
    """Parses strings like 15, 1h00, 1h, 0h30"""

    # All digits means minutes
    if s.isdigit():
        try:
            return int(s)
        except:
            return None, 1, "Wrong time supplied: '{}'. Examples of accepted values: 1h15, 15, 3h".format(s)

    # If 'h|H' separator is present
    idx = s.find('h')
    if idx == -1:
        idx = s.find('H')
        if idx == -1:
            return None, 1, "Wrong time supplied: '{}'. Examples of accepted values: 1h15, 15, 3h".format(s)

    try:
        hours = s[:idx]
        mins = s[idx + 1:]

        if hours:
            hours = abs(int(hours))
        else:
            hours = 0

        if mins:
            mins = abs(int(mins))
        else:
            mins = 0

        return hours * 60 + mins, 0, None
    except:
        return None, 1, "Wrong time supplied: '{}'. Examples of accepted values: 1h15, 15, 3h".format(s)


#-------------------------------------------------------------------
# Split comma separated list
#-------------------------------------------------------------------
def split_csv_lexer(source, whitespaces=None):
    """
    Split comma separated value list via lexer
    """
    import shlex
    lexer = shlex.shlex(source)

    if whitespaces:
        lexer.whitespace += whitespaces
    else:
        lexer.whitespace += ','

    lexer.whitespace_split = True
    return list(lexer)
