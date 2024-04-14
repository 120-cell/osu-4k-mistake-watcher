
import keyboard as kb
import mouse
import logging
from queue import Queue
from _queue import Empty


MOUSE_BUTTON_NAMES = {'left': 'Button-1', 
                      'right':'Button-2', 
                      'middle':'Button-3', 
                      'x':'Button-X',
                      'x2':'Button-X2'}


def workaround_read_event(suppress=False):
    queue = Queue(maxsize=1)
    kb_hooked = kb.hook(queue.put, suppress=suppress)
            
    mouse_hooked = mouse.hook(lambda event: queue.put(event) if isinstance(event, mouse.ButtonEvent) else None)
    try:
        event = queue.get(timeout=3)
        return event
    except Empty:
        logging.info('key binding timed out')
    finally:
        kb.unhook(kb_hooked)
        mouse.unhook_all()


def on_mouse_button(button, callback):
    def handler(event):
        if isinstance(event, mouse.ButtonEvent):
            if event.event_type and event.button == button:
                callback(event)
    mouse._listener.add_handler(handler)
    return handler


def hook_scan_code(scan_code, callback, suppress=False):
    """
    Hooks key up and key down events for a single key. Returns the event handler
    created. To remove a hooked key use `unhook_key(key)` or
    `unhook_key(handler)`.

    Note: this function shares state with hotkeys, so `clear_all_hotkeys`
    affects it as well.
    """
    kb._listener.start_if_necessary()
    store = kb._listener.blocking_keys if suppress else kb._listener.nonblocking_keys
    store[scan_code].append(callback)

    def remove_():
        del kb._hooks[callback]
        del kb._hooks[remove_]
        store[scan_code].remove(callback)
    kb._hooks[callback] = kb._hooks[remove_] = remove_
    return remove_
