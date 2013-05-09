import os

#-----------------------------------------------------------------------
import aeroback.util.conf as confutil
import aeroback.util.parse as parseutil

"""
Configures email.
"""

#-----------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------
_model = {
        'identities': [
            'dirs'
            ]
        }

_model_email = [
        'active',
        'smtp_server',
        'smtp_port',
        'user',
        'password',
        'from',
        'to',
        'subject'
        ]


#-----------------------------------------------------------------------
# Validate params
#-----------------------------------------------------------------------
def _validate(params):
    if not params:
        return None, 1, "Email config parse resulted in empty params"

    err = 0
    msgs = []

    global _model_email
    for key in _model_email:
        if not params.get(key, None):
            err = 1
            msgs.append(key)

    if err:
        msgs.insert(0, "Missing params: ")

    return params, err, ', '.join(msgs)


#-----------------------------------------------------------------------
# Parse email section
#-----------------------------------------------------------------------
def _parse_email_section(parser, id_dir, params):
    # First check if default '*' entry exists
    s = "email:{}".format(id_dir)
    if not parser.has_section(s):
        return

    global _model_email

    # Validate section
    err, msg = parser.validate_section(_model_email, s)
    if err:
        return 1, msg

    # Get each not empty key
    for key in _model_email:
        value = parser.get(s, key)
        if value:
            params[key] = value

    return 0, None


#-------------------------------------------------------------------
# Parse config file
#-------------------------------------------------------------------
def parse(filepath):
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
        return err, '\n'.join(["Error parsing {}".format(filepath), msg])

    # Get machine identities and find the first matching
    id_dirs = parser.get('identities', 'dirs')
    id_dirs = parseutil.split_csv_lexer(id_dirs)
    id_dir = None
    for d in id_dirs:
        if os.path.exists(d):
            id_dir = d
            break
    if not id_dir:
        return None, 1, """No matching identifying directories found,
make sure to add this machine's identifying directory into file {},
section 'identities'""".format(filepath)

    params = {}

    # First try to parse default '*' email section
    _parse_email_section(parser, '*', params)

    # Secondly, overlay possible section that matches identity
    _parse_email_section(parser, id_dir, params)

    # Validate params
    return _validate(params)
