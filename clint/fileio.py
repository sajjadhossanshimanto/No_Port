#%%
import os
from os.path import normpath
from threading import Lock, RLock

from clint.crypto import decrypt_aes, encrypt, encrypt_aes
from clint.util import formated_str
from logger import log

#%%
d={}
dlock=RLock()# acquire while editing dict:d
length_of_name_ln=3# maximun 3 digists

def opener(path) -> Lock:
    with dlock:
        if not d.get(path):
            d[path]=Lock()
        return d[path]

class Fileio:
    def __init__(self, store_path, mode, report_name:str="") -> None:
        log.info(f'new fileio: {store_path} ({report_name})')
        self.path = normpath(store_path)
        self.mode = mode+"b"
        
        self.lock = opener(self.path)
        self.lock.acquire()
        self.file = open(self.path, self.mode)
        
        # encrypt and write report_name to the file
        if mode=="w":
            content_ln = str(len(report_name))
            assert len(content_ln)<=length_of_name_ln
            content_ln = content_ln.zfill(length_of_name_ln)
            content_ln = content_ln.encode('utf-8')# to byte

            self.file.write(content_ln)
            self.file.write(encrypt_aes(report_name))

    def __enter__(self):
        log.debug('with blog entered')
        return self
    
    @property
    def report_name(self):
        '''decreapt name'''
        name_ln=self.read(length_of_name_ln)
        name = decrypt_aes(self, int(name_ln))
        return name

    def read(self, size=-1):
        log.debug('data reading from file')
        return self.file.read(size)

    def write(self, _s):
        log.debug('data writting to file')
        _s = formated_str(_s)
        _s = _s.encode('utf-8')# to bytes
        self.file.write(encrypt(_s))

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

