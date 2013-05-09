#import os
#import sys
#import time
#from datetime import datetime

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State

import aeroback.diagnostics.diagnostics as _D

'''
Abstract module sample:
- use as a template

Required modules:
    -

Children modules:
    -
'''


#-----------------------------------------------------------------------
# States for other modules
#-----------------------------------------------------------------------
class States(object):

    def __init__(self):
        self.module = None

    def debug_vars(self):
        return [
                'module', self.module
                ]


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self):
        super(Model, self).__init__()

    def debug_vars(self):
        return [
                'me', self.__class__
                ]


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model
        self.states = States()

    def debug_vars(self):
        return [
                'me', self.__class__
                ]


#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
def _(state):
    pass


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model():
    return Model(), 0, None
    #return Model(), 1, "Don't like this model"


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model):
    state = State(model)
    return state, 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init():
    ''' Initialize model and state'''
    _D.DEBUG(
            __name__,
            "Module init"
            )
    #raise Exception("Module: TEST Exception")

    model, err, msg = _init_model()
    if err:
        return None, err, msg

    return _init_state(model)


#-----------------------------------------------------------------------
# Validate state
#-----------------------------------------------------------------------
def _validate_state(state):
    return 0, None


#-----------------------------------------------------------------------
# Execute app
#-----------------------------------------------------------------------
def _execute(state):
    #raise Exception("Module: TEST Exception")
    return 0, None


#-----------------------------------------------------------------------
# Execute module
#-----------------------------------------------------------------------
def execute(state):
    '''Execute state'''
    _D.DEBUG(
            __name__,
            "Module execute"
            )
    err, msg = _execute(state)
    return err, msg


#-----------------------------------------------------------------------
# Cleanup module
#-----------------------------------------------------------------------
def cleanup(state):
    '''Cleanup state'''
    _D.DEBUG(
            __name__,
            "Module cleanup"
            )

    #raise Exception("Module: TEST Exception")
    pass
