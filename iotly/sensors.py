#!/usr/bin/python

import RPi.GPIO as GPIO
import Adafruit_DHT
import time
import threading
import sys
import logging
import traceback
import json

log = logging.getLogger('Sensors')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

class Sensors (threading.Thread):
    config = None
    isRunning = True

    def __init__(self, config, client):
        threading.Thread.__init__(self)

        self.config = config
        self.client = client

        self.prepare()

    def stop(self):
        self.isRunning = False

    def prepare(self):
        GPIO.setmode(GPIO.BCM)

        items = self.config['sensors']
        self.pins = {}
        for sensor in items:
            log.info('Configuring sensor type \''+sensor['type']+'\' with name '+sensor['name'])

            if (sensor['type'] == 'am2302'):
                GPIO.setup(sensor['pin'], GPIO.IN)
                self.pins[sensor['pin']] = sensor
            elif (sensor['type'] == 'din'):
                GPIO.setup(sensor['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.add_event_detect(sensor['pin'], GPIO.BOTH, callback=self.eventCallback)
                self.pins[sensor['pin']] = sensor
            elif (sensor['type'] == 'switch'):
                GPIO.setup(sensor['pin'], GPIO.OUT)
                self.pins[sensor['pin']] = sensor

    def eventCallback(self, pin):
        sensor = self.pins[pin]
        if GPIO.input(pin):
            log.info("Signal detected on "+sensor['name'])
            self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+sensor['name'], "1", 0, True)
        else:
            log.info("No more signal on "+sensor['name'])
            self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+sensor['name'], "0", 0, True)

    def fetchSwitchStatus(self, pin):
        sensor = self.pins[pin]
        if GPIO.input(pin):
            log.info("Signal detected on "+sensor['name'])
            self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+sensor['name'], "1", 0, True)
        else:
            log.info("No more signal on "+sensor['name'])
            self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+sensor['name'], "0", 0, True)

    def fetch_am2302(self, name, pin):
        humidity=None
        temperature=None

        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, pin)

        if humidity is not None and temperature is not None:
            log.info('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))
        else:
            log.info('Failed to get reading. Try again!')

        data = {}

        if humidity is not None:
            humidity = '{0:0.1f}'.format(humidity)
            data['humidity'] = humidity
            #client.publish(self.config['domain']+"/sensors/"+sensor['name'], humidity, 0, True)

        if temperature is not None:
            temperature = '{0:0.1f}'.format(temperature)
            data['temperature'] = temperature
            #client.publish("studio/sensors/temperature", temperature, 0, True)

        self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+name, json.dumps(data), 0, True)

    def run(self):
        while (self.isRunning):
            try:

                items = self.config['sensors']
                for sensor in items:
                    if (sensor['type'] == 'am2302'):
                        self.fetch_am2302(sensor['name'], sensor['pin'])
                    elif (sensor['type'] == 'din'):
                        self.eventCallback(sensor['pin'])
                    #    GPIO.setup(sensor['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                    #    GPIO.add_event_detect(sensor['pin'], GPIO.BOTH, callback=self.eventCallback)
                    elif (sensor['type'] == 'switch'):
                        self.fetchSwitchStatus(sensor['pin'])

                time.sleep(self.config['period'])

                log.info("Fetching...")
            except Exception as err:
                log.exception(err)
