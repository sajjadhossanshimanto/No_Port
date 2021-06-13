import socket
from rpyc import connect
from server.util import data_store


def check_server(address:str="localhost", port:int=6000) -> bool:
    '''check if rechable'''
    port = int(port)
    # Create a TCP socket
    s = socket.socket()
    try:
        s.connect((address, port))
        return True
    except socket.error:
        return False
    finally:
        s.close()

def is_bucket_runnnig():
    address = ('localhost', 6000)
    try:
        conn=connect(*address)
    except:
        return False
    else:
        return True

if __name__=="__main__":
    print(is_bucket_runnnig())
