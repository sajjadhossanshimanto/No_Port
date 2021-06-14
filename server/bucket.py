#%%
import os
os.chdir(os.path.dirname(__file__))# need for relative imports

import ctypes
import sys
from queue import Queue
from threading import Thread
from time import sleep

import win32process
from plyer import notification
from rpyc import Service
from rpyc.utils.server import ThreadedServer


if "clint" not in sys.modules:
    sys.path[0]+= "/../"
    __import__('clint')
    __import__('server')

from server.network import net_time
from server.drive import source_drive
from server.util import data_store
from server.bucket_running import is_bucket_runnnig

port=data_store.var.bucket_port
interval_m=data_store.var.safety_interval# interval in minutes
del data_store
if is_bucket_runnnig():
    sys.exit()

interval_s=interval_m*60# interval in sec
tokens = Queue()
print(f'safety interval sated to {interval_m} minutes')


def invesible():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        ctypes.windll.kernel32.CloseHandle(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        os.system('taskkill /PID ' + str(pid) + ' /f')
# invesible()

def get_token():
    return source_drive.drive.sick_token()
    
def prepare(token):
    return {
        "access_token":token["access_token"],
        "expiry":net_time()+token['expires_in']
    }

#%%
class MYService(Service):
    def on_connect(self, conn):
        print('one new connection established')

    def on_disconnect(self, conn):
        print('disconnect')
    
    exposed_tokens=tokens
    exposed_interval=interval_s

    @classmethod
    @property
    def exposed_left_size(self):
        return tokens.maxsize-tokens.qsize()

    def exposed_get(self):
        '''it doesn't check either to wait not. just return a token from the queue.'''
        return tokens.get_nowait()

def token_manager():
    token = get_token()
    expiry = int(token["expires_in"])
    tokens.maxsize=expiry//interval_s
    del expiry, token

    knocked=False
    while 1:
        print(f"need more {MYService.exposed_left_size*interval_m} minutes")
        if tokens.full():
            tokens.get()
            if not knocked:
                notification.notify(
                    title="No port",
                    message="You are ready to fire..🔥",
                    timeout=3
                )
                knocked=True
        
        tokens.put(prepare(get_token()))
        # sleep(interval_s)
        sleep(interval_s if tokens.full() else 2)


Thread(target=token_manager, daemon=True, name='token producer.').start()
ThreadedServer(MYService, port=port, protocol_config={
    'allow_public_attrs': True,
}).start()
