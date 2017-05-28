#!/usr/bin/python

import RPi.GPIO as GPIO
import Adafruit_MCP3008
import Adafruit_DHT
import time
import threading
import sys
import logging
import traceback
import json
import os

log = logging.getLogger('Sensors')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

class Sensors (threading.Thread):
    config = None
    isRunning = True

    def __init__(self, config, mqtt):
        threading.Thread.__init__(self)

        self.config = config
        self.mqtt = mqtt
        self.mqtt.commandsHandler = self
        self.client = mqtt.client

        self.prepare()

    def stop(self):
        self.isRunning = False

    def prepare(self):
        self.client.subscribe(self.config['domain']+"/"+self.config['name']+"/admin")

        GPIO.setmode(GPIO.BCM)
        self.adc = Adafruit_MCP3008.MCP3008(clk=self.config['adc']['clk'], cs=self.config['adc']['cs'], miso=self.config['adc']['miso'], mosi=self.config['adc']['mosi'])

        items = self.config['sensors']
        self.pins = {}
        self.chs = {}
        self.names = {}
        self.topics = []
        for sensor in items:
            log.info('Configuring sensor type \''+sensor['type']+'\' with name '+sensor['name'])

            self.names[sensor['name']] = sensor
            if (sensor['type'] == 'am2302'):
                GPIO.setup(sensor['pin'], GPIO.IN)
                self.pins[sensor['pin']] = sensor
            elif (sensor['type'] == 'din'):
                GPIO.setup(sensor['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.add_event_detect(sensor['pin'], GPIO.BOTH, callback=self.eventCallback)
                self.pins[sensor['pin']] = sensor
            elif (sensor['type'] == 'switch'):
                GPIO.setup(sensor['pin'], GPIO.OUT)
                self.client.subscribe(self.config['domain']+"/"+self.config['name']+"/commands/"+sensor['name'])
                self.topics.append(self.config['domain']+"/"+self.config['name']+"/commands/"+sensor['name'])
                self.pins[sensor['pin']] = sensor
            elif (sensor['type'] == 'ain'):
                self.chs[sensor['ch']] = sensor

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

    def fetchAdcChannel(self, channel):
        sensor = self.chs[channel]
        value = self.adc.read_adc(int(channel))
        # Print the ADC value.
        log.info("Value of "+sensor['name']+" is "+str(value))
        self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+sensor['name'], value, 0, True)

    def setSwitchState(self, name, state):
        sensor = self.names[name]
        log.info("Switching state on "+sensor['name']+ " to "+state)
        if int(state) == 1:
            GPIO.output(sensor['pin'], int(state))
            self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+sensor['name'], "1", 0, True)
        elif int(state) == 0:
            GPIO.output(sensor['pin'], int(state))
            self.client.publish(self.config['domain']+"/"+self.config['name']+"/sensors/"+sensor['name'], "0", 0, True)

    def handleCommands(self, command):
        log.info("Handling command "+command.topic+" "+str(command.payload))
        if (command.topic == self.config['domain']+"/"+self.config['name']+"/admin"):
            log.info("Managing admin commands")
            if (command.payload == 'reboot'):
                os.system("reboot")
        else:
            for topic in self.topics:
                if (topic == command.topic):
                    name = topic.split('/')[-1]
                    sensor = self.names[name]
                    if (sensor['type'] == 'switch'):
                        self.setSwitchState(name, command.payload)

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
                    elif (sensor['type'] == 'ain'):
                        self.fetchAdcChannel(sensor['ch'])

                time.sleep(self.config['period'])

                log.info("Fetching...")
            except Exception as err:
                log.exception(err)
