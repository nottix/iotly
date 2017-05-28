import yaml
import json

def load_config():
    """Loading configuration file"""

    stream=file('/home/pi/iotly/conf.yaml','r')
    config=yaml.load(stream)
    print('config '+json.dumps(config))
    return config
