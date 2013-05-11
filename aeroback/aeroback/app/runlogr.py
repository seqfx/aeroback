import os
import ConfigParser
from datetime import datetime

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

#import aeroback.diagnostics.diagnostics as _D

'''
Run logger logs:
- last time app was run
- last time each of modules run
- finished or still running

Required modules:
    -

Children modules:
    -
'''


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self):
        super(Model, self).__init__()

        self.filepath = None
        self.time_fmt = None

    def debug_vars(self):
        return [
                'filepath', self.filepath,
                'time_fmt', self.time_fmt
                ]


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model

    def debug_vars(self):
        return [
                ]


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(filepath):
    model = Model()
    model.filepath = os.path.normpath(filepath)
    model.time_fmt = "%a %b %d %H:%M:%S %Y"
    return model, 0, None


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model):
    state = State(model)
    return state, 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(filepath):
    ''' Initialize model and state'''

    model, err, msg = _init_model(filepath)
    if err:
        return State(None), err, msg

    return _init_state(model)


#-----------------------------------------------------------------------
# Get parser
#-----------------------------------------------------------------------
def _get_parser(filepath):
    """
    Creates parser. Connects it to file if file exists
    """
    parser = ConfigParser.SafeConfigParser()

    # Open file if it exists
    if os.path.exists(filepath):
        parser.read(filepath)

    return parser


#-----------------------------------------------------------------------
# Encode item
#-----------------------------------------------------------------------
def _encode_item(state, key, value):
    """
    Encodes value to string according to key suffix:
        xxx<bool> ---> str(value)
        xxx<time> ---> strftime(value)
        all others ---> str(value)
    """
    if key.endswith('<bool>'):
        return key[:len(key) - len('<bool>')], str(value)

    if key.endswith('<time>'):
        return key[:len(key) - len('<time>')], value.strftime(state.model.time_fmt)

    return key, str(value)


#-----------------------------------------------------------------------
# Decome item name
#-----------------------------------------------------------------------
def _decode_item_name(key):
    """
    Decodes key name by removing its suffix:
        xxx<bool> ---> xxx
        xxx<time> ---> xxx
        all others ---> key
    """
    if key.endswith('<bool>'):
        return key[:len(key) - len('<bool>')]

    if key.endswith('<time>'):
        return key[:len(key) - len('<time>')]

    return key


#-----------------------------------------------------------------------
# Decode item
#-----------------------------------------------------------------------
def _decode_item(state, key, value):
    if not value:
        return None

    if key.endswith('<bool>'):
        if value.lower() == 'true':
            return True
        else:
            return False

    if key.endswith('<time>'):
        return datetime.strptime(value, state.model.time_fmt)

    return value


#-----------------------------------------------------------------------
# Get section item
#-----------------------------------------------------------------------
def get_section_item(state, section_name, key):
    parser = _get_parser(state.model.filepath)
    if not parser.has_section(section_name):
        return None
    value = parser.get(section_name, _decode_item_name(key))
    return _decode_item(state, key, value)


#-----------------------------------------------------------------------
# Set section
#-----------------------------------------------------------------------
def set_section(state, section_name, items):
    """
    Set section from items dictionary:
    - Get parser
    - If section present modify it; or
    - Add new section
    - Write and close file.
    """
    parser = _get_parser(state.model.filepath)

    # Add section if doesn't exist
    if not parser.has_section(section_name):
        parser.add_section(section_name)

    # Set key-values for this section
    for k in items:
        key, value = _encode_item(state, k, items[k])
        parser.set(section_name, key, str(value))

    # Write file
    with open(state.model.filepath, 'w') as f:
        parser.write(f)

    return 0, None


#-----------------------------------------------------------------------
# Get filepath
#-----------------------------------------------------------------------
def get_filepath(state):
    return state.model.filepath


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):
    '''Execute state'''
    err = 0
    msg = None
    return err, msg


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''
    pass
