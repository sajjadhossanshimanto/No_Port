from requests import post as _post

from clint.network import *


def post(*args, **kwargs):
    net_check.wait()
    return _post(*args, **kwargs).text
