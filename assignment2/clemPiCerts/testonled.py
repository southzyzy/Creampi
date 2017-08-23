import os
import boto
import datetime
import time
from boto import dynamodb2
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex
import multiprocessing
import subprocess
from signal import pause
from gpiozero import MCP3008
import Adafruit_DHT
import re
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from gpiozero import LED

roomlight = LED(13)

def customCallback(client, userdata, message):  
  print(message.payload)
  if message.payload == 'on':
    print 'ok i on the lights'
    roomlight.on()
  else:
    print 'ok i off the lights'
    roomlight.off()
  return
    
def receiveinfo():
  try:
    host = "avvcljufnth68.iot.us-west-2.amazonaws.com"
    rootCAPath = "clem_rootca.pem"
    certificatePath = "clem_certificate.pem.crt"
    privateKeyPath = "clem_private.pem.key"

    my_rpi = AWSIoTMQTTClient("listenforled")
    my_rpi.configureEndpoint(host,8883)
    my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    my_rpi.configureOfflinePublishQueueing(-1) #Infinite offline Publish Queueing

    my_rpi.configureDrainingFrequency(2) # Draining: 2 Hz
    my_rpi.configureConnectDisconnectTimeout(10) #10 sec
    my_rpi.configureMQTTOperationTimeout(60) # 60 sec

    # Connect and subscribe to AWS IOT
    my_rpi.connect()
    while True:
      my_rpi.subscribe("room/1/light/status",1,customCallback)
  except:
    return
    
while True:
  receiveinfo()