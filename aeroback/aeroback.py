#!/usr/bin/python

import sys
import traceback
import logging

#-----------------------------------------------------------------------
import aeroback.constants.corestr as corestr
import aeroback.core.core as core


#-----------------------------------------------------------------------
# Main error wrapper
#-----------------------------------------------------------------------
def core_run():
    try:
        # Errors: non recoverable

        # Init
        state, err, msg = core.init(
                argv = sys.argv,
                config_filename = 'core.ini'
                )
        if err:
            out = [
                    corestr._ICON_EXCEPTION_UNCHECKED,
                    '-' * 60,
                    "[Core]: Failure to initialize",
                    "\tError code: {}".format(err),
                    "\tMessage: {}".format(msg),
                    '-' * 60
                    ]
            raise Exception('\n'.join(out))

        # Execute
        err, msg = core.execute(state)
        if err:
            out = [
                    corestr._ICON_EXCEPTION_UNCHECKED,
                    '-' * 60,
                    "[Core]: Failure to execute",
                    "\tError code: {}".format(err),
                    "\tMessage: {}".format(msg),
                    '-' * 60
                    ]
            raise Exception('\n'.join(out))

        # Execute app
        core.execute_app(state)

        # Clean
        core.cleanup(state)

        # Finished clean
        logging.warning(corestr._ICON_APP_FINISHED)

    except:
        # Critical exception happened
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        traceback.print_exc(file=sys.stdout)


#-----------------------------------------------------------------------
# MAIN
#
if __name__ == '__main__':
    sys.exit(core_run())
