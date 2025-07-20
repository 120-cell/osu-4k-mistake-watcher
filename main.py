
import logging
import os
import pickle

from app import App
from setting_handler import Setting_Handler, SETTINGS_PATH


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)
    settings = Setting_Handler(SETTINGS_PATH)
    app = App(settings)
    app.mainloop()

    
if __name__ == '__main__':
    main()