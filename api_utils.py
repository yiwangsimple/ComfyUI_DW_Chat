import os
import configparser

def load_api_key(key_name):
    config = configparser.ConfigParser()
    ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'api_key.ini')
    if os.path.exists(ini_path):
        config.read(ini_path)
        return config.get('API_KEYS', key_name, fallback=None)
    return None