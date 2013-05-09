import urllib


#-----------------------------------------------------------------------
# Encode string into URL
#-----------------------------------------------------------------------
def encode(s):
    return urllib.pathname2url(s)


#-----------------------------------------------------------------------
# Build url out of paths
#-----------------------------------------------------------------------
def url_build(scheme, *paths):
    """ Create clean encoded URL.
    Honors '..'
    """

    # Split all into bits
    folders = []
    for p in paths:
        if not p:
            continue
        pps = p.split('/')
        for pp in pps:
            if pp == '.':
                continue
            if pp == '..':
                folders.pop()
                continue
            if pp:
                folders.append(pp)
                '''
                if pp != '*':
                    folders.append(encode(pp))
                else:
                    folders.append(pp)
                '''

    url = []

    url.append("{}://".format(scheme))
    url.append('/'.join(folders))
    return url


#-----------------------------------------------------------------------
# Append
#-----------------------------------------------------------------------
def append(url, folder):
    """ Append folder to URL
    """

    if url[1]:
        url.append("/{}".format(folder))
    else:
        url.append("{}".format(folder))
