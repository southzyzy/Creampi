from gpiozero import Button
from signal import pause
import os
import datetime
import time
import multiprocessing
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from gpiozero import LED

buttonRoom1 = Button(13, pull_up=False)
buttonRoom2 = Button(26, pull_up=False)
feedbackLED = LED(16)

def blink():
  for i in range(3):
    feedbackLED.on()
    sleep(0.5)
    feedbackLED.off()
    sleep(0.5)
  
def ringBell(roomNumber):
  try:
    blinkLED = multiprocessing.Process(target=blink)
    blinkLED.start()
    # to ring the bell, send 'ring' to room/#/bell/ringstatus
    if roomNumber == '1':
      link = "room/%s/bell/ringstatus"%(str(roomNumber))
      my_rpi.publish(link,"ring",1)
      print 'sent \'ring\' to %s'%(link)
    if roomNumber == '2':
      link = "room/%s/bell/ringstatus"%(str(roomNumber))
      my_rpi.publish(link,"ring",1)
      print 'sent \'ring\' to %s'%(link)
      
  except:
    ringBell(roomNumber)

def dingdongRoom1():
  print 'Dingdong room 1'
  ringBell('1')

def dingdongRoom2():
  print 'Dingdong room 2'
  ringBell('2')

#========= need to change this portion ===========
host = "avvcljufnth68.iot.us-west-2.amazonaws.com"
rootCAPath = "zy_rootca.pem"
certificatePath = "zy_certificate.pem.crt"
privateKeyPath = "zy_private.pem.key"
#=================================================

my_rpi = AWSIoTMQTTClient("doorbellSender")
my_rpi.configureEndpoint(host,8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1) #Infinite offline Publish Queueing

my_rpi.configureDrainingFrequency(2) # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10) #10 sec
my_rpi.configureMQTTOperationTimeout(60) # 5 sec

# Connect and subscribe to AWS IOT
my_rpi.connect()

print 'Connected and waiting..'
  
buttonRoom1.when_pressed=dingdongRoom1
buttonRoom2.when_pressed=dingdongRoom2

pause()