import threading
import paho.mqtt.client as mqtt
import time
import threading
import sys
import json
import logging
import traceback

log = logging.getLogger('MqttHandler')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

class MqttHandler (threading.Thread):
    config = None
    mqttBroker = 'localhost'
    mqttPort = 1883

    def __init__(self, config):
        threading.Thread.__init__(self)

        self.config = config
        self.mqttBroker = config['mqtt']['address']
        self.channels = []

        self.connect()

    def connect(self):
        retry = True
        while (retry == True):
          try:
            self.client = mqtt.Client(self.config['name'], clean_session=False)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
	    self.client.username_pw_set(self.config['mqtt']['username'], self.config['mqtt']['password'])
            self.client.connect(self.mqttBroker, self.mqttPort, 60)

            retry = False
          except Exception as err:
            log.exception(err)
            retry = True
            time.sleep(2)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
      log.info("Connected with result code "+str(rc))

      # Subscribing in on_connect() means that if we lose the connection and
      # reconnect then subscriptions will be renewed.
#      self.client.subscribe("$SYS/#")
      for ch in self.channels:
         log.info("Subscribing to "+ch)
         self.client.subscribe(ch, qos=1)

      self.client.publish(self.config['domain']+"/"+self.config['name']+"/ready", "1", 0, True)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
      log.info(msg.topic+" "+str(msg.payload))
      if (self.commandsHandler):
          self.commandsHandler.handleCommands(msg)

    def stop(self):
        self.isRunning = False
        self.client.disconnect()

    def run(self):
        log.info("Connecting to " + self.mqttBroker)

#        self.connect()
        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.client.loop_forever()

        log.info("Exiting")
