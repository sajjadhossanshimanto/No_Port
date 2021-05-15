from time import sleep
from threading import Thread

import tracemalloc
tracemalloc.start()
def momo():
    while 1:
        current, peak = tracemalloc.get_traced_memory()
        print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")
        sleep(1)
Thread(target=momo, daemon=True).start()






tracemalloc.stop()