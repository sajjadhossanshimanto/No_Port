from os import mkdir
import sys
from os.path import basename
import logging
from logging.handlers import RotatingFileHandler
import curses
import __main__

# from server.util import data_store

log_folder="debugging"
class CursesHandler(logging.StreamHandler):
    def __init__(self, window) -> None:
        self.window=window
        self.window.chgat(-1, curses.A_REVERSE)
        super().__init__()

    def emit(self, record):
        try:
            msg = self.format(record)

            self.window.clear()
            self.window.addstr(msg, curses.A_REVERSE)
            self.window.chgat(-1, curses.A_REVERSE)
            self.window.refresh()
            
        except (KeyboardInterrupt, SystemExit):
            raise
        except AttributeError:
            pass
        except:
            self.handleError(record)


# name=data_store.var.name
name='no port'
log = logging.getLogger(name)
log.setLevel(logging.DEBUG)
log.disabled = getattr(sys, "frozen", False) # if compiled

try:
    mkdir(log_folder)
except:
    pass
file_name=basename(__main__.__file__)
file_name=file_name[:file_name.rfind('.')]
file_name+='.log'

c_handler = logging.StreamHandler()
c_handler.setLevel(logging.INFO)
f_handler = RotatingFileHandler(f'{log_folder}/{file_name}', backupCount=4)
f_handler.setLevel(logging.DEBUG)


c_format = logging.Formatter('[%(filename)s] %(levelname)s -- %(message)s')
c_handler.setFormatter(c_format)
f_format = logging.Formatter('%(asctime)s - %(filename)s - %(lineno)s - %(levelname)s - %(message)s - %(pathname)s')
f_handler.setFormatter(f_format)

log.addHandler(c_handler)
log.addHandler(f_handler)


def add_curses_handler(window):
    window.scrollok(True)
    window.idlok(True)
    
    _handler=CursesHandler(window)
    _handler.setLevel(logging.INFO)
    _handler.setFormatter(c_format)

    log.addHandler(_handler)


print()
if __name__=="__main__":
    # import os
    # path=os.fspath('virus.log')
    # path=os.path.abspath(path)
    # print(log.handlers[-1].baseFilename)
    print(log.handlers[-1].baseFilename)
    # print(log.handlers[-1].baseFilename)


    # for i in log.handlers:
    #     print(type(i))
    
    log.info('lsdkjflksd')