from collections import OrderedDict
#-----------------------------------------------------------------------


#-----------------------------------------------------------------------
# A_State
#-----------------------------------------------------------------------
class A_State(object):
    '''
    Abstract state
    '''

    #-------------------------------------------------------------------
    # Constructor
    #-------------------------------------------------------------------
    def __init__(self):

        # Description
        self.description = ''

        # Descriptors
        self._descriptors = OrderedDict()

        # Statistics of performance, etc.
        self._stats = OrderedDict()

        # Messages that state accumulates though lifetime
        self._messages_info = []
        self._messages_warning = []
        self._messages_error = []

    #===================================================================
    # Description
    #===================================================================
    #-------------------------------------------------------------------
    # Add
    #-------------------------------------------------------------------
    def set_description(self, value):
        self._description = value

    #-------------------------------------------------------------------
    # Get
    #-------------------------------------------------------------------
    def get_description(self):
        return self._description

    #===================================================================
    # Descriptors
    #===================================================================
    #-------------------------------------------------------------------
    # Add message info
    #-------------------------------------------------------------------
    def set_descriptor(self, key, value):
        self._descriptors[key] = value

    def set_descriptor_category(self, cat_key, key, value):
        cat = self._descriptors.get(cat_key, None)

        if cat:
            cat[key] = value
        else:
            self._descriptors[cat_key] = OrderedDict([(key, value)])

    #-------------------------------------------------------------------
    # Get descriptors
    #-------------------------------------------------------------------
    def get_descriptors(self):
        return self._descriptors

    #===================================================================
    # Statistics
    #===================================================================
    #-------------------------------------------------------------------
    # Set statistics entry
    #-------------------------------------------------------------------
    def set_stats(self, key, value):
        self._stats[key] = value

    def set_stats_category(self, cat_key, key, value):
        cat = self._stats.get(cat_key, None)

        if cat:
            cat[key] = value
        else:
            self._stats[cat_key] = OrderedDict([(key, value)])

    #-------------------------------------------------------------------
    # Get statistics
    #-------------------------------------------------------------------
    def get_stats(self):
        return self._stats

    #-------------------------------------------------------------------
    # Increment statistics numeric entry
    #-------------------------------------------------------------------
    def increment_stats_value(self, key, value):
        if key in self._stats:
            old_value = self._stats[key]
            self._stats[key] = old_value + value

    #===================================================================
    # Messages
    #===================================================================
    #-------------------------------------------------------------------
    # Add message info
    #-------------------------------------------------------------------
    def add_msg_info(self, text):
        self._messages_info.append(text)

    #-------------------------------------------------------------------
    # Add message warning
    #-------------------------------------------------------------------
    def add_msg_warning(self, text):
        self._messages_warning.append(text)

    #-------------------------------------------------------------------
    # Add message error
    #-------------------------------------------------------------------
    def add_msg_error(self, text):
        self._messages_error.append(text)

    #-------------------------------------------------------------------
    # Get messages info
    #-------------------------------------------------------------------
    def get_msgs_info(self):
        return self._messages_info

    #-------------------------------------------------------------------
    # Get messages warning
    #-------------------------------------------------------------------
    def get_msgs_warning(self):
        return self._messages_warning

    #-------------------------------------------------------------------
    # Get messages error
    #-------------------------------------------------------------------
    def get_msgs_error(self):
        return self._messages_error
