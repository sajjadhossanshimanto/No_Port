#%%
from clint.network import Net_Error
from logger import log
log.debug('\n\n\n\nnew start..')

from server.util import data_store
import os
from multiprocessing import Process
from server.drive import validate_cred
from multiprocessing.connection import Client
from tui import home_page
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

home_page.show()
