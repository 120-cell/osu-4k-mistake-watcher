
import logging
import os
import pickle

from app import App
from setting_handler import Setting_Handler, SETTINGS_PATH


def main():
    logging.basicConfig(level=logging.DEBUG)
    
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)
    try:
        logging.info('loading settings from file')
        with open(SETTINGS_PATH, 'rb') as file:
            settings = pickle.load(file)
    except FileNotFoundError:
        settings = Setting_Handler()
        
    app = App(settings)
    app.mainloop()

    
if __name__ == '__main__':
    main()