#%%
import atexit
import os
import sys
import threading
from msvcrt import getch
from traceback import format_exception

from logger import log, report_file


def on_exception(etype, value, tb):
    full_tb=format_exception(etype, value, tb)
    
    # log.error(full_tb[-4].strip(" \n"))
    # log.critical(full_tb[-1].strip(" \n"))
    log.critical(f"{etype}: {value}")
    log.debug("".join(full_tb))
    log.warning('exiting on exception.')
    
    atexit._run_exitfuncs()
    log.info(f'debugging log saved to "{report_file}"')
    log.warn('all services stoped. press any key to exit.')
    getch()
    os._exit(1)

def thread_exception(args):
    log.info(f'exception in {args.thread}')
    on_exception(args.exc_type, args.exc_value, args.exc_traceback)

sys.excepthook=on_exception
threading.excepthook=thread_exception

#%%
from io import StringIO
from time import sleep

from server.bucket_running import is_bucket_runnnig
from server.drive import drive, drive_file, source_drive, validate_cred
from server.startup import is_admin, script_path, task_startup
from server.util import data_store, validate_command_syntax

#%%
validate_cred()

'''
in secure mode no token is provided to the clint.
all commands are available but those who
requires drive access for reporting schecudle their uploads
also clint status is unknown( online or offline )
clints list is shown from previous cache

reenabling secuire mode will clear the token
'''

# if not is_bucket_runnnig():
#     log.info("bucket is not running.")
#     task_startup()
#     if not is_admin():
#         log.info('reruning with admin permetion.')
#         sys.exit()
#     os.startfile(f"server/{script_path}")

# ensure command and token file is shared to source # must do
for file in [data_store.var.token_file, data_store.var.command_file]:
    with drive_file(file) as f:
        f.make_public()

# validate command file
with drive_file(data_store.var.command_file) as f:
    s=StringIO(super(drive_file, f).read())
    validate_command_syntax(s)
    s.seek(0)
    f.rewrite(s.read())

# ensure empty bin
if source_drive.trashed_files() or drive.trashed_files():
    log.warning('Trash bins are not empty, some functions may not work properly.')
    sleep(.25)# let the user to watch this warning


#%%
from server.tui import home_page  # inits curses handler

home_page.show()

