import os
import sys
import shutil
import re
from stat import S_ISREG, ST_MTIME, ST_MODE

#-----------------------------------------------------------------------


#-----------------------------------------------------------------------
# Ensure directory exists on disk
#-----------------------------------------------------------------------
def ensure_dir(path):
    '''
    Makes sure given directory exists.
    Returns:
        0 - OK
        1 - error
    '''
    if not os.path.exists(path):
        os.makedirs(path)
        if not os.path.exists(path):
            return 1, "{}: Ensure Dir: can not create dir: {}".format(__name__, path)

    if not os.access(path, os.W_OK):
        return 1, "{}: Ensure Dir: dir is not writable: {}".format(__name__, path)

    return 0, None


#-----------------------------------------------------------------------
# Path to list
#-----------------------------------------------------------------------
def path_to_list(path):
    """
    Returns list with:
    [0] - drive
    [1] - list of folders
    """

    drive, path_and_files = os.path.splitdrive(path)
    folders = []
    while True:
        path, folder = os.path.split(path)

        if folder:
            folders.append(folder)
        else:
            break

    folders.reverse()
    return drive, folders


#-----------------------------------------------------------------------
# Split to body/tail
#-----------------------------------------------------------------------
def path_to_body_tail(path):
    """
    /a/b/c --> /a/b, c
    /a --> /, a
    / --> /, None
    """
    if not path:
        return '', ''

    path = os.path.normpath(path)
    folder = os.path.basename(path)
    l = len(folder)
    parent = os.path.normpath(path[:len(path) - l])

    return parent, folder


#-----------------------------------------------------------------------
# Class: File Finder
#-----------------------------------------------------------------------
class FileFinder:
    """
    Find files matching certain criteria
    """

    #-------------------------------------------------------------------
    def __init__(self, filetpl):
        if not filetpl:
            self.pattern = None
            return

        parts = filetpl.split('{}')
        esc = []
        i = 0
        count = len(parts)
        while i < count:
            esc.append(re.escape(parts[i]))
            i += 1
            if i != count:
                esc.append('.*')

        self.pattern = ''.join(esc)

    #-------------------------------------------------------------------
    def matches(self, filename):
        """Does file name match pattern ?"""

        if re.findall(self.pattern, filename):
            return True
        else:
            return False

    #-------------------------------------------------------------------
    def find(self, path):
        """Find files in given path that match template.
        """

        # List of filenames
        if self.pattern:
            entries = []
            for f in os.listdir(path):
                if self.matches(f):
                    entries.append(os.path.join(path, f))
        else:
            entries = (os.path.join(path, fn) for fn in os.listdir(path))

        # List of (file, file stats) tuples
        entries = ((os.stat(f), f) for f in entries)

        # Leave only regular files, insert creation date
        # NOTE: on Windows `ST_CTIME` is a creation date
        #       but on Unix it could be something else
        # NOTE: use `ST_MTIME` to sort by a modification date
        entries = ((stat[ST_MTIME], f) for stat, f in entries if S_ISREG(stat[ST_MODE]))
        return entries

    #-------------------------------------------------------------------
    def find_into_groups(self, path, date_sort=1, head_count=5):
        """Find and split into two groups
        Sort can be: +1 ascendant, -1 descendant, 0 none
        Head count: >0 split into to, <=0 return all in head
        """

        entries = self.find(path)

        if date_sort == 1:
            entries = sorted(entries)
        elif date_sort == -1:
            entries = sorted(entries, reverse=True)

        if len(entries) <= head_count or head_count <= 0:
            return (entries, [])
        else:
            return (entries[0:head_count], entries[head_count:len(entries)])


#-----------------------------------------------------------------------
# Find files by given template
#-----------------------------------------------------------------------
def find_files(file_template, path):
    return FileFinder(file_template).find(path)


#-----------------------------------------------------------------------
# Find files by given template and split into groups by date
#-----------------------------------------------------------------------
def find_files_grouped(path, file_template, date_sort=1, head_count=5):
    return FileFinder(file_template).find_into_groups(path, date_sort, head_count)


#-----------------------------------------------------------------------
# Error handler: Directory tree remover
#-----------------------------------------------------------------------
def _on_remove_dir_tree_error(function, path, excinfo):
    import aeroback.reporting.debugr as _D
    _D.WARNING(
            __name__,
            "Warning: error removing directory tree",
            'path', path,
            'msg', excinfo
            )


#-----------------------------------------------------------------------
# Directory tree remover
#-----------------------------------------------------------------------
def remove_dir_tree(path):
    '''
    Removes whole directory tree.
    Returns:
        0 - OK
        1 - Error
    '''

    err = 0
    msg = None

    if not path:
        return err, msg

    try:
        if os.path.exists(path):
            shutil.rmtree(
                    path,
                    onerror = _on_remove_dir_tree_error
                    )

    except Exception:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        err = 1
        msg = "{}: Error removing dir tree: {}, exc = {}".format(__name__, path, exc_value)

    finally:
        return err, msg


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def remove_file(path):
    '''
    Removes single file
    Returns:
        0 - OK
        1 - Error
    '''

    err = 0
    msg = None

    if not path:
        return err, msg

    try:
        if os.path.exists(path):
            os.remove(path)

    except Exception:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        err = 1
        msg = "{}: Error removing file: {}, exc = {}".format(__name__, path, exc_value)

    finally:
        return 1, "{}: {}".format(exc_type, exc_value)


#-----------------------------------------------------------------------
# Directory contents cleaner
#-----------------------------------------------------------------------
def empty_dir(path):
    '''
    Empties directory.
    Returns:
        0 - OK
        1 - Error
    '''

    if not os.path.exists(path):
        return 0, None

    err = 0
    msgs = []
    for f in os.listdir(path):
        filepath = os.path.join(path, f)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
            elif os.path.isdir(filepath):
                e, m = remove_dir_tree(filepath)
                if e:
                    err = 1
                    msgs.append(m)

        except Exception:
            (exc_type, exc_value, exc_traceback) = sys.exc_info()
            err = 1
            msgs.append("{}: Error deleting file: {}, exc = {}".format(__name__, filepath, exc_value))

    return err, '\n'.join(msgs)
