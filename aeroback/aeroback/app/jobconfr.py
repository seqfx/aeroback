import os
import re

#-----------------------------------------------------------------------
#import aeroback.diagnostics.diagnostics as _D
import aeroback.util.conf as confutil
import aeroback.util.parse as parseutil

"""
Configures backup job.
"""

#-----------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------
_model = {
        'identity': ['dir', 'gsutil']
        }
_model_storage = [
        'active',
        'bucket',
        'dirstorage'
        ]
_model_backup_db_mongo = [
        'description',
        'active',
        'dirstorage',
        'history',
        'user',
        'password',
        'host'
        ]
_model_backup_db_mysql = [
        'description',
        'active',
        'dirstorage',
        'history',
        'user',
        'password',
        'host'
        ]
_model_backup_dir_compress = [
        'description',
        'active',
        'dirstorage',
        'history',
        'dirs'
        ]
_model_backup_dir_increment = [
        'description',
        'active',
        'dirstorage',
        'dir',
        'maxupload',
        'includes',
        'excludes'
        ]


#-------------------------------------------------------------------
# Extract type from section name
#-------------------------------------------------------------------
def _get_section_type(section):
    '''
    Extract section type from forms like this:

    * storage_abc
    * storage_abc_0
        ---> storage_abc

    * backup_dir_incremental
    * backup_dir_incremental_
    * backup_dir_incremental_0
        ---> backup_dir_incremental
    '''

    # Try as 'storage'
    pattern = r'storage\_[a-zA-Z0-9]+'
    match = re.search(pattern, section)
    if match:
        return section[match.start(): match.end()]

    # Try as 'backup'
    pattern = r'backup\_[a-zA-Z0-9]+\_[a-zA-Z0-9]+'
    match = re.search(pattern, section)
    if match:
        return section[match.start(): match.end()]
    else:
        return None


#-------------------------------------------------------------------
# Extract type from section name
#-------------------------------------------------------------------
def _remove_prefix(prefix, string):
    '''
    Remove prefix iff string starts with it,
    otherwise leave string untouched
    '''
    if string.find(prefix) == 0:
        return string[len(prefix) + 1:]
    else:
        return string


#-------------------------------------------------------------------
# Add to parameters - list element
#-------------------------------------------------------------------
def _add_to_list(params, key, value):
    if not params.get(key, None):
        params[key] = []

    params[key].append(value)


#-------------------------------------------------------------------
# Parse storage
#-------------------------------------------------------------------
def _add_storage(parser, params, section_key, section_type):
    '''
    Input:
        section_key = 'storage'
        section_type = 'storage_amazons3'
    '''

    storage = {}

    t = _remove_prefix(section_key, section_type)
    if t == 'amazons3':
        storage['scheme'] = 's3'
    elif t == 'googlestorage':
        storage['scheme'] = 'gs'

    storage['type'] = t
    storage['active'] = parser.getboolean(section_type, 'active')
    storage['bucket'] = parser.get(section_type, 'bucket')
    storage['dirstorage'] = parser.get(section_type, 'dirstorage')

    _add_to_list(params, 'storages', storage)


#-------------------------------------------------------------------
# Find sections by prefix
#-------------------------------------------------------------------
def _find_sections(parser, section_base):
    """
    Return section base names as list:
        [ name1, name2, name3, ... ]
    """
    sections = []
    for s in parser.sections():
        if s.startswith(section_base):
            sections.append(s)
    return sections


def _find_sections_groups(parser, section_base):
    """
    Return sections as dictionary:
        { section_name : [0, 1, 2] }
    """
    sections = {}
    for s in parser.sections_groups():
        if s.startswith(section_base):
            sections.append(s)
    return sections


#-------------------------------------------------------------------
# Parse storage types
#-------------------------------------------------------------------
def _parse_storages(parser, params):
    section_key = 'storage'

    # Find all sections starting with 'storage'
    sections = _find_sections(parser, section_key)

    # Parse each subsection
    for s in sections:
        # Check model
        err, msg = parser.validate_section(_model_storage, s)
        if err:
            return 1, msg

        # Normalize storage type and call relevant parser
        # Section type: storage_amazons3, storage_googlestorage, ...
        section_type = _get_section_type(s)
        if not section_type:
            return 1, "Storage section name does not follow convention storage_type[_suffix]: {}".format(s)

        # Parse and add to params
        _add_storage(parser, params, section_key, section_type)

    return 0, None


#-------------------------------------------------------------------
# Get optional frequency
#-------------------------------------------------------------------
def _optional_frequency(parser, name, sid, backup):
    if not parser.has_option(name, 'frequency', sid):
        return 0, None
    freq = parser.get(name, 'frequency', sid)
    if not freq:
        return 0, None
    mins, err, msg = parseutil.hours_minutes(freq)
    if err:
        return err, msg
    else:
        backup['frequency'] = mins
        return 0, None


#-------------------------------------------------------------------
# Parse backup types
#-------------------------------------------------------------------
def _add_backup_db_mongo(parser, params, atype, name, sid):
    '''
    Adds backup:
        - atype = backup
        - name = backup_db_mongo
        - sid = 0|1|2|...
    '''
    backup = {}
    backup['name'] = name
    backup['type'] = _remove_prefix(atype, name)
    backup['description'] = parser.get(name, 'description', sid)
    backup['active'] = parser.getboolean(name, 'active', sid)
    backup['dirstorage'] = parser.get(name, 'dirstorage', sid)
    backup['history'] = parser.getint(name, 'history', sid)
    backup['user'] = parser.get(name, 'user', sid)
    backup['password'] = parser.get(name, 'password', sid)
    backup['host'] = parser.get(name, 'host', sid)

    # Optional: frequency
    err, msg = _optional_frequency(parser, name, sid, backup)
    if err:
        return err, msg

    _add_to_list(params, 'backups', backup)
    return 0, None


def _add_backup_db_mysql(parser, params, atype, name, sid):
    backup = {}
    backup['name'] = name
    backup['type'] = _remove_prefix(atype, name)
    backup['description'] = parser.get(name, 'description', sid)
    backup['active'] = parser.getboolean(name, 'active', sid)
    backup['dirstorage'] = parser.get(name, 'dirstorage', sid)
    backup['history'] = parser.getint(name, 'history', sid)
    backup['user'] = parser.get(name, 'user', sid)
    backup['password'] = parser.get(name, 'password', sid)
    backup['host'] = parser.get(name, 'host', sid)

    # Optional: frequency
    err, msg = _optional_frequency(parser, name, sid, backup)
    if err:
        return err, msg

    _add_to_list(params, 'backups', backup)
    return 0, None


def _add_backup_dir_compress(parser, params, atype, name, sid):
    backup = {}
    backup['name'] = name
    backup['type'] = _remove_prefix(atype, name)
    backup['description'] = parser.get(name, 'description', sid)
    backup['active'] = parser.getboolean(name, 'active', sid)
    backup['dirstorage'] = parser.get(name, 'dirstorage', sid)
    backup['history'] = parser.getint(name, 'history', sid)
    backup['dirs'] = parseutil.split_csv_lexer(parser.get(name, 'dirs', sid), '\n')

    # Optional: frequency
    err, msg = _optional_frequency(parser, name, sid, backup)
    if err:
        return err, msg

    _add_to_list(params, 'backups', backup)
    return 0, None


def _add_backup_dir_increment(parser, params, atype, name, sid):
    backup = {}
    backup['name'] = name
    backup['type'] = _remove_prefix(atype, name)
    backup['description'] = parser.get(name, 'description', sid)
    backup['active'] = parser.getboolean(name, 'active', sid)
    backup['dirstorage'] = parser.get(name, 'dirstorage', sid)
    backup['dir'] = parser.get(name, 'dir', sid)
    backup['maxupload'] = parseutil.bytesize(parser.get(name, 'maxupload', sid))
    backup['includes'] = parseutil.split_csv_lexer(parser.get(name, 'includes', sid), '\n')
    backup['excludes'] = parseutil.split_csv_lexer(parser.get(name, 'excludes', sid), '\n')

    # Optional: frequency
    err, msg = _optional_frequency(parser, name, sid, backup)
    if err:
        return err, msg

    _add_to_list(params, 'backups', backup)
    return 0, None


#-------------------------------------------------------------------
# Parse backup type
#-------------------------------------------------------------------
def _parse_backup(parser, params, section_type, section_name, section_id):
    '''
    section_type = backup
    section_name = backup_mongo, backup_dircompress, backup_dircincrement, ...
    section_id = 0|1|2|...
    '''
    # Find section model
    pmodel = {
        'backup_db_mongo': _model_backup_db_mongo,
        'backup_db_mysql': _model_backup_db_mysql,
        'backup_dir_compress': _model_backup_dir_compress,
        'backup_dir_increment': _model_backup_dir_increment
    }.get(section_name, None)

    if not pmodel:
        return 1, "No support implemented for backup: {}".format(section_name)

    # Check model
    err, msg = parser.validate_section(pmodel, section_name, section_id)
    if err:
        return 1, msg

    # Find parsing function
    pfunc = {
        'backup_db_mongo': _add_backup_db_mongo,
        'backup_db_mysql': _add_backup_db_mysql,
        'backup_dir_compress': _add_backup_dir_compress,
        'backup_dir_increment': _add_backup_dir_increment
    }.get(section_name, None)

    if not pfunc:
        return 1, "No parser implemented for backup: {}".format(section_name)

    err, msg = pfunc(parser, params, section_type, section_name, section_id)
    return err, msg


#-------------------------------------------------------------------
# Parse backup types
#-------------------------------------------------------------------
def _parse_backups(parser, params):
    section_key = 'backup'

    # Find all sections starting with 'backup'
    sgs = parser.section_groups()

    msgs = []
    for sname in sgs:
        if sname.startswith(section_key):
            for sid in sgs[sname]:
                err, msg = _parse_backup(parser, params, section_key, sname, sid)
                if err:
                    msgs.append(msg)

    if msgs:
        return 1, msgs

    return 0, None


#-----------------------------------------------------------------------
# Parse
#-----------------------------------------------------------------------
def parse(filepath):
    '''
    Parse backup config file. Returns:
        - err = 0 - OK
        - err = 1 - ERROR
        - err = 2 - WARNING: config doesn't match this machine
    '''

    # Check file is present
    if not os.path.exists(filepath):
        return None, 1, "Config file not found: {}".format(filepath)

    # Load config from filename
    parser, err, msg = confutil.config_parser_improved(filepath)
    if err:
        return None, err, msg

    # Check config matches model
    global _model
    err, msg = parser.validate(_model)
    if err:
        return None, err, '\n'.join(["Error parsing {}".format(filepath), msg])

    params = {}

    # Identity directory matches this machine ?
    id_dir = parser.get('identity', 'dir')
    if os.path.exists(id_dir):
        params['identity_dir'] = id_dir
    else:
        return None, 2, "This machine doesn't match: {}".format(id_dir)

    # Identity gsutil path
    params['gsutil'] = parser.get('identity', 'gsutil')

    err = 0
    msgs = []

    # Parse storage types
    err, msg = _parse_storages(parser, params)
    if err:
        msgs.append(msg)

    # Parse backup types
    err, msg = _parse_backups(parser, params)
    if err:
        msgs.append(msg)

    if msgs:
        err = 1

    return params, err, msgs
