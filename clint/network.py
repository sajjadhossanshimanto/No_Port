#%%
import json
from json.decoder import JSONDecodeError
from socket import create_connection, gethostbyname, gethostname
from threading import Thread, Event
import ntplib
from time import sleep
from requests import get as _get
import sys


compiled=getattr(sys, "frozen", False) # check if app is being compiled by cx_freeze

class Net_Error(Exception):
    pass# recured by bucket

#%%
class net_manager:
    def __init__(self, ):
        self.connection = Event()
        self.connection.clear()
        self.core = Thread(target=self.is_connected, daemon=True, name="Net_manager")
        
        # self.start()
    
    def is_connected(self):
        while 1:
            try:
                create_connection(("www.google.com", 80))
            except:
                self.connection.clear()
            else:
                self.connection.set()
            sleep(.5)

    def start(self):
        if self.running:
            return #already running
        
        self.core.start()

    @property
    def running(self):
        return self.core.is_alive()

    def wait(self):
        if not self.running:
            self.start()
            sleep(3)# let the connection to be set

        if not compiled and not self.connection.is_set():
            raise Net_Error('Can\'t connect to the internet....0_o')

        self.connection.wait()
net_check=net_manager()

#%%
def ip():
    net_check.wait()
    return gethostbyname(gethostname())

def get(*args, **kwargs):
    net_check.wait()
    return _get(*args, **kwargs)


ntp_c=ntplib.NTPClient()
def net_time():
    ntp_lists=[
        "time.google.com",
        "time1.google.com",
        "time2.google.com",
        "time3.google.com",
        "time4.google.com",

        "time.cloudflare.com",
        
        "time.facebook.com",
        "time1.facebook.com",
        "time2.facebook.com",
        "time3.facebook.com",
        "time4.facebook.com",
        "time5.facebook.com",

        "time.windows.com"
    ]
    for remo_ser in ntp_lists:
        try:
            remote=ntp_c.request(remo_ser)
            return int(remote.tx_time)
        except Exception as e:
            print(e.with_traceback())
    

if __name__=="__main__":
    import time
    # from logger import log
    # safe_disk=net_manager()
    counter=0
    while 1:
        net_time()
        counter+=1
        print(counter)
        sleep(2)
    # log.info(net_time())
#%%
"kd".splitlines()