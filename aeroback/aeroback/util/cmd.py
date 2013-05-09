import sys
import subprocess

#-----------------------------------------------------------------------
import aeroback.diagnostics.diagnostics as _D


#-----------------------------------------------------------------------
# Call subprocess
#-----------------------------------------------------------------------
def call_cmd(args, shell = False):
    """
    Invokes process.
    Returns:
        result - string returned from command, or error
        err - 0 = OK, 1 = ERROR, 2 = WARNING
        msg - error details
    """

    '''
    _D.DEBUG(
            __name__,
            "call_cmd",
            'args', args
            )
    '''
    print 'CMD:', args

    try:
        result = subprocess.check_output(
                args,
                stderr = subprocess.STDOUT,
                shell = shell)

        return result, 0, None

    except subprocess.CalledProcessError as e:
        return e.returncode, 1, e.output

    except (OSError, ValueError, RuntimeError) as e:
        #traceback.print_exc(file=sys.stdout)
        return "Exception invoking cmd", 1, str(e)

    except:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        return "Exception invoking cmd", 1, "{}: {}".format(exc_type, exc_value)


#-----------------------------------------------------------------------
# Call subprocess and raise if exception
#-----------------------------------------------------------------------
def call_cmd_raise(args):
    result, err, msg = call_cmd(args)
    if err:
        raise Exception(
                "Error invoking cmd:",
                ' '.join(args),
                "{}".format(msg)
                )


#-----------------------------------------------------------------------
def call_cmd_old(args, hx):
    _D.DEBUG(
            __name__,
            "call_cmd",
            'args', args
            )
    try:
        return subprocess.check_output(
                args,
                stderr = subprocess.STDOUT,
                shell = False)

    except subprocess.CalledProcessError as e:
        # Process returned non-zero value
        hx.err_add("Process returned error = {}".format(str(e.returncode)), ' '.join(args), e.output)

    except (OSError, ValueError, RuntimeError) as e:
        # Some other exception
        #traceback.print_exc(file=sys.stdout)
        hx.err_add("Exception invoking cmd", ' '.join(args), str(e))

    except:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        hx.err_add("Exception invoking cmd", exc_type, exc_value)

    finally:
        _D.DEBUG(
                __name__,
                "call_cmd result",
                'hx', hx
                )


#-----------------------------------------------------------------------
# Sample
#-----------------------------------------------------------------------
class A:
    """
    Sample class
    """

    #-------------------------------------------------------------------
    def __init__(self, hx):
        self.hx = hx

    #-------------------------------------------------------------------
    def a(self, path):
        pass

    #-------------------------------------------------------------------
    def on_err(self, a, b, c):
        self.hx.warn_add("Can't '{}'".format(a), "exc", c)
