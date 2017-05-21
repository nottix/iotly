#!/usr/bin/python

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import Adafruit_DHT
import time
import threading
import sys
import logging
#from systemd import journal

log = logging.getLogger('iotly')
#log.addHandler(journal.JournalHandler())
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

MQTT_BROKER="192.168.1.78"
MQTT_PORT=1883

retry = True
while (retry == True):
  try:
    client = mqtt.Client()
    retry = False
  except Exception:
    log.error("Error")
    retry = True
    time.sleep(2)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
  log.info("Connected with result code "+str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("$SYS/#")
  client.publish("hass/rasp1/ready", "1", 0, True)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
  log.info(msg.topic+" "+str(msg.payload))

def mqtt_sender():

  client.on_connect = on_connect
  client.on_message = on_message

  client.connect(MQTT_BROKER, MQTT_PORT, 60)

  # Blocking call that processes network traffic, dispatches callbacks and
  # handles reconnecting.
  # Other loop*() functions are available that give a threaded interface and a
  # manual interface.
  client.loop_forever()


GPIO.setmode(GPIO.BCM)
PIR_PIN = 7
GPIO.setup(PIR_PIN, GPIO.IN)

def MOTION(PIR_PIN):
  if GPIO.input(PIR_PIN):
    log.info("Motion Detected!")
    client.publish("studio/sensors/pir", "1", 0, True)
  else:
    log.info("No more motion")
    client.publish("studio/sensors/pir", "0", 0, True)

MQ5_PIN = 17
GPIO.setup(MQ5_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def combGas(MQ5_PIN):
  if GPIO.input(MQ5_PIN):
    log.info("Combustible Gas Detected!")
    client.publish("studio/sensors/cgas", "1", 0, True)
  else:
    log.info("No more Combustible Gas")
    client.publish("studio/sensors/cgas", "0", 0, True)



SENSOR = Adafruit_DHT.AM2302
DHT_PIN = 4
humidity = "-"
temperature = "-"
def fetch_am2302():

  humidity, temperature = Adafruit_DHT.read_retry(SENSOR, DHT_PIN)

  if humidity is not None and temperature is not None:
    log.info('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))
  else:
    log.info('Failed to get reading. Try again!')

  if humidity is not None:
    humidity = '{0:0.1f}'.format(humidity)
    client.publish("studio/sensors/humidity", humidity, 0, True)

  if temperature is not None:
    temperature = '{0:0.1f}'.format(temperature)
    client.publish("studio/sensors/temperature", temperature, 0, True)

def sender():
  while 1:
    fetch_am2302()
    MOTION(PIR_PIN)
    combGas(MQ5_PIN)

    time.sleep(30)

try:
  GPIO.add_event_detect(PIR_PIN, GPIO.BOTH, callback=MOTION)
  GPIO.add_event_detect(MQ5_PIN, GPIO.BOTH, callback=combGas)

#  GPIO.add_event_detect(PIR_PIN, GPIO.FALLING, callback=AWAY)

  t = threading.Thread(target=mqtt_sender)
  t.daemon = True
  t.start()

  t2 = threading.Thread(target=sender)
  t2.daemon = True
  t2.start()

  log.info("Starting (CTRL+C to exit)")
  time.sleep(1)
  log.info("Ready")

  while 1:
    time.sleep(100)
except KeyboardInterrupt:
  log.info("Quit")
  GPIO.cleanup()
