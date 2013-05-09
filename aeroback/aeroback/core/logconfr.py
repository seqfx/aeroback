import os
import logging
import logging.config

#-----------------------------------------------------------------------

"""Configures logging.
The different levels of logging, from highest urgency
to lowest urgency, are:

    CRITICAL
    ERROR
    WARNING
    INFO
    DEBUG

You can use the tail -f logfile.txt command to show a
file as it is being written to. The -f stands for "follow".

"""


#-------------------------------------------------------------------
# Output to screen
#-------------------------------------------------------------------
def _config_screen(fmt, _):
    print "LOG >>>>> SCREEN"
    logging.basicConfig(
            level = logging.DEBUG,
            format = fmt
            )
    #logger = logging.getLogger()
    return 0, None


#-------------------------------------------------------------------
# Output to file
#-------------------------------------------------------------------
def _config_file(fmt, filepath):
    print "LOG >>>>> " + filepath

    logging.basicConfig(
            filename = filepath,
            level = logging.DEBUG,
            format = fmt
            )
    #logger = logging.getLogger()
    return 0, None


#-------------------------------------------------------------------
# Output to screen + file
#-------------------------------------------------------------------
def _config_screen_file(fmt, filepath):
    print "LOG >>>>> " + filepath

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(fmt)

    fh = logging.FileHandler(filepath)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return 0, None


#-------------------------------------------------------------------
# Output configured by external .cfg file
#-------------------------------------------------------------------
def _config_external(fmt, filepath):
    print "LOG >>>>> EXTERNAL CFG - NOT IMPLEMENTED YET"
    return 0, None
    '''
    logger = logging.getLogger()
    logging.config.fileConfig('logging.cfg')
    logger = logging.getLogger('aeroback')
    '''


#-------------------------------------------------------------------
# Output
#-------------------------------------------------------------------
def _get_config(o):
    return {
            'screen': _config_screen,
            'file': _config_file,
            'screen+file': _config_screen_file,
            'external': _config_external
            }.get(o, _config_screen)


#-------------------------------------------------------------------
# Config
#-------------------------------------------------------------------
def configure(output, dir_log, filename):
    # Find output mode
    config_func = _get_config(output)

    # Validate filename
    if not dir_log:
        return 1, "Logging directory must be provided"
    elif not os.path.exists(dir_log):
        return 1, "Logging directory does not exist: {}". format(dir_log)

    # Validate filename
    if not filename:
        return 1, "Filename must be provided"

    filepath = os.path.join(dir_log, filename)

    # Logging format
    log_format = '%(message)s'

    return config_func(log_format, filepath)
