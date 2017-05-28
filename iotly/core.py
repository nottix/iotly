# -*- coding: utf-8 -*-
import config
import mqtt_handler as MqttHandler
import sensors as Sensors
#from . import iotly
import logging
import traceback
import time

log = logging.getLogger('core')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

def start_iotly():
    """Starting..."""
    conf = config.load_config()

    mqttInstance = MqttHandler.MqttHandler(conf)
    mqttInstance.start()

    sensors = Sensors.Sensors(conf, mqttInstance)
    sensors.start()

    try:
        log.info("Ready.")
        while 1:
            time.sleep(100)
    except KeyboardInterrupt:
        mqttInstance.stop()
        sensors.stop()
        log.info("Quit")
