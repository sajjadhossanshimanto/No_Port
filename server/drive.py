#%%
from os.path import dirname, join, split
from time import sleep
import sys
from .network import post
from datetime import datetime
from urllib.parse import quote
import json
import os

from server.util import data_store
from logger import log
from clint.drive import Online, drive_explorer as DE, Drive

from clint.util import formated_str
try:
    from setting import (client_secret, client_id, host_rtoken, source_rtoken, host_email)
except ImportError:
    raise Exception("Unsecure modification was made to setting")



secure_mod=True
name=data_store.var.name
bf_name=data_store.var.backup_folder_name
# del data_store

#%%
class Drive_server(Drive):
    client_id:str = client_id
    client_secret:str = client_secret
    refresh_token:str = host_rtoken
    
    timer=lambda s,token: int(token.get("expires_in"))

    def __init__(self):
        super().__init__()
        del self.token_url

    def start(self):
        if self.running:
            return
        self.engine.start()

        self.permited.wait()# wait for the engine to create google drive instance
        self.drive.auth.Authorize()
        self.service=self.drive.auth.service

    def sick_token(self):
        refresh_url = "https://oauth2.googleapis.com/token"
        while not (self.client_id and self.client_secret and self.refresh_token):
            sleep(5)

        data = {
            "grant_type":"refresh_token",
            "client_id":quote(self.client_id),
            "client_secret":quote(self.client_secret),
            "refresh_token":quote(self.refresh_token)
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = post(refresh_url, headers=headers, data=data)
        return json.loads(response)

#%%
error_des={
    'Bad Request':"wrong refresh_token provided",
    "The OAuth client was not found.":"wrong client_id provided",
    'Unauthorized':"wrong client_secret provided",
}
class drive_explorer(DE):
    def __init__(self, prefix=name):
        '''each time you create a drive explorer instance creates a Drive_server instance 
            which leads to start a new 'drive' thread'''
        self.drive = Drive_server()
        self.prefix = prefix
        
    def exists(self, path):
        '''last modified file is given the most priority'''
        file_lst = super().exists(path)
        return sorted(file_lst,
            key=lambda x:datetime.fromisoformat((x["modifiedDate"].rstrip('Z'))),
            reverse=True
        )

    def list_folder(self, path, files_only=False):
        '''
            list all files and folders in the "path"
            path:str = relative_path
        '''
        path=join(self.prefix, path)
        _id = self.get_folder_id(path)
        _q_str=f"'{_id}' in parents and trashed=false" + " and mimeType='application/octet-stream'" if files_only else ""
        file_list = self.drive.ListFile({'q': _q_str}).GetList()
        return list(set(map(lambda x:x['title'], file_list)))

    def list_files(self, path):
        return self.list_folder(path, files_only=True)

    def copy_file(self, origin_file_id, copy_to):
        """Copy an existing file. this,,
            do not add "name" prefix
            do not overwrite previous file
            creates onother file of same name.
        """
        root, title=split(copy_to)
        root_id=self.get_folder_id(root)
        copied_file = {'title': title, "parents":[{"id":root_id}]}
        
        self.drive.start()# just in case copy_to is in root # for debugging
        return self.drive.service.files().copy(
            fileId=origin_file_id, body=copied_file
        ).execute()
    
    def get_file(self, path):
        path=join(self.prefix, path)
        return super().get_file(path)

drive = drive_explorer()
drive.drive.engine.name="host drive"

source_drive = drive_explorer('')
source_drive.drive.refresh_token=source_rtoken
source_drive.drive.engine.name="suorce drive"


# %%
class drive_file(Online):
    def __init__(self, path):
        '''for now drive_file is only allowed for host drive'''
        self.file = drive.get_file(path)
    
    def read(self):
        data=super().read()
        jtype=json.loads(data)
        return jtype if not isinstance(jtype, str) else data# if data is str

    def write(self, data):
        data = formated_str(data)
        return super().write(data)

    def rewrite(self, data):
        data = formated_str(data)
        self.file.SetContentString(data)
        self.file.Upload()

    def delete(self):
        self.file.Delete()# permanent delete


def backup(file_path):
    '''only applyable on host drive'''
    ori_file=drive.get_file(file_path)
    ori_file_id=ori_file['id']

    root, file = split(file_path)
    root = join(root, bf_name)
    file = join(root, file)
    
    drive.copy_file(ori_file_id, file)
    ori_file.Delete()# permanent delete
    log.info(f'file: {file_path} backuped')

def move_file(file_path):
    '''move files from source drive to host'''
    file=source_drive.get_file(file_path)
    file.InsertPermission({
        'type' : 'user',
        'value': host_email,
        "role" : "writer",
    })

    dst=join(name, file_path)
    # if previously a file exists of the path backup it to old first
    if drive.exists(dst):
        backup(dst)

    drive.copy_file(file['id'], dst)
    file.Delete()
    log.info(f'file:"{file_path}" moved from source to host drive')


def validate_cred():
    tokens=[]
    tokens.append(drive.drive.sick_token())
    tokens.append(source_drive.drive.sick_token())
    
    for token in tokens:
        if hasattr(token, "error"):
            log.error(error_des.get(token.get("error_description")), f"Unknown error -- {token['error_description']}")
            log.critical('wrong creadintials..!')
            sys.exit()
    log.info('all creadintial validated')



#%%
{
    'access_token': 'ya29.A0AfH6SMAg5HBLUiQqlRKpVkp8O_6J7fiIsdq_-hCL3pPCB5r7DwkNEIQmhG-idxZ9d1KPMXPiUXpWnl4NTGMlxNtiXLgK6gPZrKyLZBqn_WBOXcSaDrq_DJcLf3mWMSDhjFdnAed8W6h5rH0qYvQoaH9D25VR',
    'expires_in': 3599,
    'scope': 'https://www.googleapis.com/auth/drive',
    'token_type': 'Bearer'
}
# https://gist.github.com/whatnick/666e03d25286852235750d269ed0eda8


# wrong refresh_token
{
    'error': 'invalid_grant',
    'error_description': 'Bad Request'
}
# wrong client_id
{
    'error': 'invalid_client',
    'error_description': 'The OAuth client was not found.'
}
# wrong client_secret
{
    'error': 'invalid_client',
    'error_description': 'Unauthorized'
}



#%%
# multi-clint can create files at the same time
# but can't write to a same file
# one token is enoung to create multiple drive obj
# from threading import Event, Thread

# bomb=Event()
# bomb.clear()

# #%%
# token = get_access_token()
# def test(sec):
#     drive = connect(token)
#     # bomb.wait()
#     file1 = drive.CreateFile({'title':sec,"parents":[{'id':"1HHzCjNB3nojlM513ml-gx4p-3re1cp--"}]})
#     file1.Upload()

# #%%
# for i in range(10):
#     Thread(target=test, args=[i], name=str(i)).start()
