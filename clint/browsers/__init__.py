from .config.constant import constant
from .config.users import get_username_winapi, set_env_variables

# def user_impersonation():
constant.is_current_user = True
constant.username = get_username_winapi()
if not constant.username.endswith('$'):
    constant.finalResults = {'User': constant.username}
    set_env_variables(user=constant.username)
