import os

#-----------------------------------------------------------------------
import aeroback.diagnostics.diagnostics as _D

import aeroback.context.context as context
import aeroback.util.cmd as cmdutil


#-----------------------------------------------------------------------
# Execute storage command
#-----------------------------------------------------------------------
def exec_command(invocation):
    # Access app context to check for dry run parameter
    dry_run, err, msg = context.get_param('-dry')
    if err:
        _D.ERROR(
                __name__,
                "Error obtaining context parameter",
                'key', '-dry',
                'msg', msg
                )
        return "Error", 1, "Error obtaining context parameter '{}': {}".format('-dry', msg)

    # Do dry run, and return
    if dry_run:
        _D.WARNING(
                __name__,
                "gsutil DRY RUN",
                'cmd', invocation
                )
        return "Dry run", 0, None

    # Get optional gsutil path from app model
    filepath, err, msg = context.get_param('gsutil')
    if err:
        _D.ERROR(
                __name__,
                "Error obtaining context parameter",
                'key', 'gsutil',
                'msg', msg
                )
        return "Error", 1, "Error obtaining context parameter '{}': {}".format('-dry', msg)

    # Use filepath if provided
    if filepath:
        invocation[0] = os.path.join(filepath, invocation[0])

    # Call subprocess
    return cmdutil.call_cmd(invocation)


#-----------------------------------------------------------------------
# Copy local ---> storage
#-----------------------------------------------------------------------
def copy_local_to_storage(path, url):
    # Invocation
    invocation = ['gsutil',
            'cp',
            path,
            url]

    # Execute
    return exec_command(invocation)


#-----------------------------------------------------------------------
# Copy storage ---> local
#-----------------------------------------------------------------------
def copy_storage_to_local(url, path):
    # Invocation
    invocation = ['gsutil',
            'cp',
            url,
            path]

    # Execute
    return exec_command(invocation)


#-----------------------------------------------------------------------
# Remove from storage
#-----------------------------------------------------------------------
def remove_from_storage(url):
    # Invocation
    invocation = ['gsutil',
            'rm',
            url]

    # Execute
    return exec_command(invocation)
