from queue import Queue, Empty
import logging
from threading import Thread
from collections import defaultdict


class EventEngine:
    def __init__(self):
        self._active = False
        self._queue = Queue()
        self._thread = Thread(target=self._run)
        self._handlers = defaultdict(list)

    def _run(self):
        while self._active == True:
            try:
                event = self._queue.get(block=True, timeout=1)
                # handle events if only handlers are registered.
                # each event can possible be passed into multiple handlers e.g. orders -> order manager/ positions
                if event.type in self._handlers:
                    [handler(event) for handler in self._handlers[event.type]]
            except Empty:
                pass
            except Exception as e:
                # log event
                pass

    def start(self, timer=True):
        self._active = True
        self._thread.start()

    def stop(self):
        self._active = False
        self._thread.join()

    def put(self, event):
        self._queue.put(event)

    def register_handler(self, type_, handler):
        if handler not in self._handlers[type_]:
            self._handlers[type_].append(handler)

    def unregister_handler(self, type_, handler):
        pass
