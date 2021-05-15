import socket
from rpyc import connect



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

# p=check_server()
# print(p)

address = ('localhost', 6000)
try:
    conn=connect(*address)
except:
    print(False)
else:
    print(True)