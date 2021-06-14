import csv
import ctypes
import os
import sys
from io import StringIO
from msvcrt import getch
from subprocess import getoutput

from logger import log

script_path = 'start_bucket.vbs'
bucket = "bucket.py"

script_path = os.path.abspath(script_path)
task_name = f"\\bucket_startup"

def confarm_script():
    # if not exists(script_path):
    script=f'''
Set WshShell = CreateObject("WScript.Shell")
wshShell.CurrentDirectory = "{os.getcwd()}"
WshShell.Run """{sys.executable}"" ""{bucket}""", 0
Set WshShell = Nothing
'''
    with open(script_path, 'w') as f:
        f.write(script)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def status():
    tasks = getoutput("schtasks /Query /fo csv")
    tasks = StringIO(tasks)
    for row in csv.DictReader(tasks):
        if row["TaskName"]==task_name:
            return row["Status"]=="Disabled" and False or True

def task_startup():
    if is_admin():
        stat=status()
        if len(sys.argv)>1 and sys.argv[1]=="remove":
            os.system(f'SCHTASKS /CHANGE /TN "{task_name}" /DISABLE')
            log.info(f'Disabled startup Schedule "{task_name}"')
        else:
            if stat is None:
                confarm_script()
                log.info(f'Scheduling "{task_name}" at startup')
                os.system(f'SCHTASKS /CREATE /SC ONLOGON /TN "{task_name}" /TR "{script_path}"')
            elif stat is False:
                log.info(f'Renabeling startup Schedule "{task_name}"')
                os.system(f'SCHTASKS /CHANGE /TN "{task_name}" /ENABLE')
        
        print('job done', flush=True)
        getch()
    else:
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

if __name__=="__main__":
    task_startup()