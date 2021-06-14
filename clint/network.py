#%%
import sys
from socket import create_connection, gaierror, gethostbyname, gethostname
from threading import Event, Thread
from time import sleep, time

import ntplib
from requests import get as _get

from logger import log

compiled=getattr(sys, "frozen", False) # check if app is being compiled by cx_freeze


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
            except gaierror:# server refuse due to several request
                self.connection.clear()
                sleep(2)
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
            log.warning('waiting for network.')
            log.info('please check your net connection.')
            log.debug("network may not available or server refused to connect")
            self.connection.wait()
            log.info('net is back')

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
# @lru_cache
def time_diff():
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
            net_check.wait()
            remote=ntp_c.request(remo_ser)
        except ntplib.NTPException:# server refuse or net failure
            pass
        else:
            log.debug(f'time server: {remo_ser}')
            return int(remote.tx_time)-time()
    raise Exception('no ntp server responded.')

# def net_time():
#     # but what is the user manually fix the time diff
#     return time()+time_diff()

class current_time:
    def __get__(self, obj, obj_type=None):
        if obj.counter>=5:# refresh every 5 times
            diff=time_diff()
            if int(diff)!=int(obj.diff):
                log.warning(f'local clock time changed. {diff-obj.diff} sec')
            obj.diff=diff
            obj.counter=0

        obj.counter+=1
        return obj.diff+time()

class Timer:
    time=current_time()
    def __init__(self) -> None:
        self.diff=time_diff()
        self.counter=0
    
    def __call__(self):
        return self.time

net_time=Timer()

if __name__=="__main__":
    # import time
    # from logger import log
    # safe_disk=net_manager()
    counter=0
    while 1:
        print(net_time())
        counter+=1
        print(counter)
        sleep(2)
    # log.info(net_time())
