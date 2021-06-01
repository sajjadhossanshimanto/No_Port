#%%
import sys
import threading
from traceback import format_exception
import os
import atexit

def on_exception(etype, value, tb):
    log.critical(f'{etype}: {value}')
    log.debug("".join(format_exception(etype, value, tb)))
    log.warning('exiting on exception.')
    
    atexit._run_exitfuncs()
    os._exit(1)

def thread_exception(args):
    log.info(f'exception in {args.thread}')
    on_exception(args.exc_type, args.exc_value, args.exc_traceback)

sys.excepthook=on_exception
threading.excepthook=thread_exception


from logger import log
from server.drive import drive_file, move_file, source_drive, source_file, validate_cred
from server.util import data_store
from server.tui import home_page

# from iamlaizy import reload_me
# reload_me()

#%%
validate_cred()

'''
in secure mode no token is provided to the clint.
all commands are available but those who
requires drive access for reporting shecudle their uploads
also clint status is unknown( online or offline )
clints list is shown from previous cache

reenabling secuire mode will clear the token
'''

# address = ('localhost', data_store.var.bucket_port)
# try:
#     conn = Client(address, authkey=data_store.var.authkey)
# except ConnectionRefusedError:
#     # use os.startfile to start bucket 
#     # but for that bucket needs to convert to exe
#     os.startfile("start_bucket.vbs")

# ensure command and token file is shared to source # must do
# validate command file
# ensure empty bin


home_page.show()

