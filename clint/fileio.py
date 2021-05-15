#%%
from threading import Lock, RLock
import os
from os.path import normpath
from .util import formated_str
from logger import log


d={}
dlock=RLock()# accure while editing dict:d
class fileio:
    def __init__(self, path, mode) -> None:
        log.info(f'new fileio: {path}')
        self.path = normpath(path)
        self.mode = mode
        
        self.lock = self.opener()
        self.lock.acquire()
        self.file = open(self.path, self.mode)

    def opener(self) -> Lock:
        with dlock:
            if not d.get(self.path):
                d[self.path]=Lock()
            return d[self.path]

    def __enter__(self):
        log.debug('with blog entered')
        return self
    
    def read(self):
        log.debug('data reading from file')
        return self.file.read()

    def write(self, _s):
        log.debug('data writting to file')
        _s = formated_str(_s)
        self.file.write(_s)

    def delete(self):
        log.debug('deliting file')
        self.file.close()
        
        os.remove(self.path)
        with dlock:
            d.pop(self.path)

    def __exit__(self, *args):
        log.debug('exiting fileio')

        self.file.close()
        try:
            self.lock.release()
        # incase lock is already realeased by delete and again called by __exit__
        except RuntimeError:
            pass
    
        del self

# %%
