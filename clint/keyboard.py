from typing import Callable, Dict
from logger import log
from pynput.keyboard import HotKey, Listener


class MHotKey(HotKey):
    def press(self, key):
        if key in self._keys and key not in self._state:
            self._state.add(key)
            if self._state == self._keys:
                return self._on_activate()

class BrowserHotKeys(Listener):
    def __init__(self, hotkeys:Dict, log_to:Callable, *args, **kwargs):
        self.log_to = log_to
        self._hotkeys = [
            MHotKey(HotKey.parse(key), value)
            for key, value in hotkeys.items()]
        super(BrowserHotKeys, self).__init__(
            on_press=self._on_press,
            on_release=self._on_release,
            *args,
            **kwargs)

    def _on_press(self, key):
        clip = ""
        for hotkey in self._hotkeys:
            try:
                clip+=hotkey.press(self.canonical(key))
            except:
                pass
            
            if clip:
                break
        
        self.log_to(clip, key)

    def _on_release(self, key):
        for hotkey in self._hotkeys:
            hotkey.release(self.canonical(key))


if __name__=="__main__":
    def fun():
        return "paste"
    def ff(c, k):
        print(c,k)
        
    with BrowserHotKeys({"<ctrl>+v":fun, "<shift>+<insert>":fun}, ff) as listener:
        listener.join()
