from itertools import chain
from .chromium_based import chromium_browsers
from .mozilla import firefox
from .ucbrowser import uc
from .ie import internet_explorer

def run():
    browsers=[firefox, uc, internet_explorer]
    for i in chain(browsers, chromium_browsers):
        pas = i.run()
        if pas:
            yield pas

