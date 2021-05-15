import os
import sys
from os.path import join, splitdrive
from msvcrt import getch
import ctypes


script_path = 'start_bucket.bat'
bucket = "bucket.py"
bucket = os.path.abspath(bucket)

start_dir=join(os.environ['ProgramData'], r"Microsoft\Windows\Start Menu\Programs\StartUp")# shell:common startup
script_path=join(start_dir, script_path)


def confarm_script():
    script=f'"{sys.executable}" "{bucket}"'

    with open(script_path, 'w') as f:
        f.write(script)
        print(f.read())

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if is_admin():
    if len(sys.argv)>1 and sys.argv[1]=="remove":
        os.remove(script_path)
    else:
        print('running')
        confarm_script()
    
    print(script_path)
    getch()
else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)