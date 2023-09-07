from datetime import datetime
import logging
import os
import pickle

import re
from tkinter import simpledialog

from app import App
from mistake import Keylock, Repeat, Skip
from setting_handler import Setting_Handler, SETTINGS_PATH


def main():
    logging.basicConfig(level=logging.DEBUG)
    
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)
    if os.path.isfile(SETTINGS_PATH):
        logging.info('loading settings from file')
        with open(SETTINGS_PATH, 'rb') as file:
            settings = pickle.load(file)
    else:
        settings = Setting_Handler()
    app = App(settings)
    app.mainloop()

    
if __name__ == '__main__':
    main()