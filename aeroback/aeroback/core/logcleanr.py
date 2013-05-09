import os

#-----------------------------------------------------------------------
import aeroback.util.fs as fsutil

"""
Cleans log directory of old logs
"""


#-------------------------------------------------------------------
# Constructor
#-------------------------------------------------------------------
def clean(dir_log, current, filename_tpl, history_size):

    # Validate file template
    if filename_tpl.find('{}') == -1:
        return 1, "File template must have '{}' timestamp placeholder"

    # Validate history
    if history_size < 1:
        history_size = 1

    # Find files in log directory
    (recent, older) = fsutil.find_files_grouped(
                                path = dir_log,
                                file_template = filename_tpl,
                                date_sort = -1,
                                head_count = history_size
                                )

    # Delete older logs
    current = os.path.join(dir_log, current)
    for fdate, f in older:
        if f != current:
            os.remove(f)

    return 0, None
