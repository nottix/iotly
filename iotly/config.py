import yaml
import json

def load_config():
    """Loading configuration file"""

    stream=file('config.yaml','r')
    config=yaml.load(stream)
    print('config '+json.dumps(config))
    return config
