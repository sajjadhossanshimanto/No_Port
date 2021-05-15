from clint.network import *
from requests import post as _post


def post(*args, **kwargs):
    net_check.wait()
    return _post(*args, **kwargs).text
