#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model

"""
Context, globally accessible environment information:
    - params -- contains parsed command line params
"""


#-----------------------------------------------------------------------
# Global
#-----------------------------------------------------------------------
_model = None


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self, params):
        super(Model, self).__init__()
        self.params = params

    def debug_vars(self):
        return [
                'params', self.params
                ]


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(params):
    global _model
    _model = Model(params)
    return _model


#-----------------------------------------------------------------------
# Get param
#-----------------------------------------------------------------------
def get_param(key):
    global _model
    if _model:
        return _model.params.get(key, None), 0, None
    else:
        return None, 1, "Context failed to initialize"

#-----------------------------------------------------------------------
# Set param
#-----------------------------------------------------------------------
def set_param(key, value):
    global _model
    if _model:
        _model.params[key] = value
        return 0, None
    else:
        return 1, "Context failed to initialize"
