

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
