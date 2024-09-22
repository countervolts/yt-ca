import os
from config import *

def save_download_path(download_path):
    config_lines = []
    if os.path.exists('config.py'):
        with open('config.py', 'r') as config_file:
            config_lines = config_file.readlines()
    
    with open('config.py', 'w') as config_file:
        path_written = False
        for line in config_lines:
            if line.startswith("DOWNLOAD_PATH"):
                config_file.write(f"DOWNLOAD_PATH = '{download_path}'\n")
                path_written = True
            else:
                config_file.write(line)
        
        if not path_written:
            config_file.write(f"DOWNLOAD_PATH = '{download_path}'\n")