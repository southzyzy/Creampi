# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
import re
import multiprocessing
import subprocess

def instructionsforroom(roomNumber,send):
  try:
    #========= need to change this portion ===========
    host = "avvcljufnth68.iot.us-west-2.amazonaws.com"
    rootCAPath = "zy_rootca.pem"
    certificatePath = "zy_certificate.pem.crt"
    privateKeyPath = "zy_private.pem.key"
    #=================================================

    my_rpi = AWSIoTMQTTClient("DecisionMaker")
    my_rpi.configureEndpoint(host,8883)
    my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    my_rpi.configureOfflinePublishQueueing(-1) #Infinite offline Publish Queueing

    my_rpi.configureDrainingFrequency(2) # Draining: 2 Hz
    my_rpi.configureConnectDisconnectTimeout(10) #10 sec
    my_rpi.configureMQTTOperationTimeout(20) # 5 sec

    # Connect and subscribe to AWS IOT
    my_rpi.connect()
  except:
    instructionsforroom(roomNumber,send)
  
  # current avg is 158-163
  if (send == 'on'):
    #Publish to the same topic in a loop forever
    link = "room/%s/light/status"%(str(roomNumber))
    my_rpi.publish(link,"on",1)
    print 'sent on to %s'%(link)
    return
  elif send =='off':
    #Publish to the same topic in a loop forever
    link = "room/%s/light/status"%(str(roomNumber))
    my_rpi.publish(link,"off",1)
    print 'sent off to %s'%(link)
    return
  else:
    pass
  my_rpi.disconnect()
    
# Custom MQTT message callback
def customCallback(client, userdata, message):
  print("Received a new message: ")
  print(message.payload)
  print("from topic:")
  print(message.topic)
  print("------------\n\n")
  
  roomNumber = re.search('room\/([^\/]*).+', message.topic)
  #print roomNumber.group(1)

  # room1 = '0000000073e32a48'
  # room2 = '000000003d7762f1'
  
  f = open("lightThreshold.txt","r")
  data = f.readlines()
  for i in data:
    fileLine = re.search('([^\-]*)-(.+)', i)
    piSN = fileLine.group(1)
    lightThreshold = fileLine.group(2)
    if piSN == '0000000073e32a48':
      if (int(float(message.payload)) < lightThreshold):
        instructionsforroom(roomNumber.group(1),'on')
      else:
        instructionsforroom(roomNumber.group(1),'off') 
    if piSN == '000000003d7762f1':
      if (int(float(message.payload)) < lightThreshold):
        instructionsforroom(roomNumber.group(1),'on')
      else:
        instructionsforroom(roomNumber.group(1),'off')     
  
while True:
  try:
    host = "avvcljufnth68.iot.us-west-2.amazonaws.com"
    rootCAPath = "zy_rootca.pem"
    certificatePath = "zy_certificate.pem.crt"
    privateKeyPath = "zy_private.pem.key"

    my_rpi = AWSIoTMQTTClient("subtolight")
    my_rpi.configureEndpoint(host,8883)
    my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    my_rpi.configureOfflinePublishQueueing(-1) #Infinite offline Publish Queueing

    my_rpi.configureDrainingFrequency(2) # Draining: 2 Hz
    my_rpi.configureConnectDisconnectTimeout(10) #10 sec
    my_rpi.configureMQTTOperationTimeout(60) # 60 sec

    # Connect and subscribe to AWS IOT
    my_rpi.connect()
    
    while True:
      my_rpi.subscribe("room/+/sensors/light",1,customCallback)
      #my_rpi.subscribe("room/1/sensors/light",1,customCallback)
      #my_rpi.subscribe("room/2/sensors/light",1,customCallback)
  except:
    my_rpi.disconnect()
    #pass

