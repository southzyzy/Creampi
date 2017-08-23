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

# ======= define the pi number =======
pinumber = "pi1"
# ====================================

adc = MCP3008(channel=0)
DHTpin = 17
roomlight = LED(13)

def publishData():
  try:
    while True:
      Timestamp,Pi_SN,ARM_Status,GPU_Status,Humidity,Light,Pi_Temp,Temperature = getdata()
      # ========= need to change this portion ===========
      host = "avvcljufnth68.iot.us-west-2.amazonaws.com"
      rootCAPath = "stanley_rootca.pem"
      certificatePath = "stanley_certificate.pem.crt"
      privateKeyPath = "stanley_private.pem.key"
      # =================================================
      
      my_rpi = AWSIoTMQTTClient(pinumber)
      my_rpi.configureEndpoint(host,8883)
      my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

      my_rpi.configureOfflinePublishQueueing(-1) #Infinite offline Publish Queueing

      my_rpi.configureDrainingFrequency(2) # Draining: 2 Hz
      my_rpi.configureConnectDisconnectTimeout(10) #10 sec
      my_rpi.configureMQTTOperationTimeout(60) # 60 sec
      
      my_rpi.connect()

      # Publish to the same topic in a loop forever
      my_rpi.publish("room/2/sensors/light",str(Light),1)
      print 'light value published to room/2/sensors/light'
      time.sleep(15)
  except:
    publishData()
    
def getdata():
  proc = subprocess.Popen(["vcgencmd measure_temp"], stdout=subprocess.PIPE, shell=True)
  (temp, err) = proc.communicate()
  proc1 = subprocess.Popen(["vcgencmd get_mem arm"], stdout=subprocess.PIPE, shell=True)
  (arm, err) = proc1.communicate()
  proc2 = subprocess.Popen(["vcgencmd get_mem gpu"], stdout=subprocess.PIPE, shell=True)
  (gpu, err) = proc2.communicate()
  proc3 = subprocess.Popen(["lsusb"], stdout=subprocess.PIPE, shell=True)
  (cam, err) = proc3.communicate()
  
  datestring = datetime.datetime.now().date()
  timestring = time.strftime("%H:%M:%S", time.localtime())
  
  Timestamp = str(datestring)+' '+str(timestring)
  Pi_SN = getserial()
  ARM_Status = re.search('.+?=(.+)?M', arm)
  GPU_Status = re.search('.+?=(.+)?M', gpu)
  Humidity, Temperature = Adafruit_DHT.read_retry(11,DHTpin)
  Light = round(1024-(adc.value*1024))
  Pi_Temp = re.search('.+?=(.+)?\'C', temp)
  
  return Timestamp,Pi_SN,ARM_Status.group(1),GPU_Status.group(1),Humidity,Light,Pi_Temp.group(1),Temperature
    
def getserial():
  # Extract serial from cpuinfo file
  global cpuserial
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000"
  return cpuserial

def inserttodb():
  while True:
    Timestamp,Pi_SN,ARM_Status,GPU_Status,Humidity,Light,Pi_Temp,Temperature = getdata()
    AWS_ACCESS_KEY_ID = 'AKIAIMPG2I3WRWDTWYQA'
    AWS_SECRET_ACCESS_KEY = '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'
    REGION = 'us-west-2'
    TABLE_NAME = 'Pilogs'

    conn = dynamodb2.connect_to_region(REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    table = Table(
      TABLE_NAME,
      connection=conn
    )

    results = table.scan()

    datestring = datetime.datetime.now().date()
    timestring = time.strftime("%H:%M:%S", time.localtime())
    datetime1 = str(datestring)+' '+str(timestring)

    Pi_SN = Pi_SN
    Timestamp = Timestamp
    ARM_Status = ARM_Status+'M'
    GPU_Status = GPU_Status+'M'
    Humidity = Humidity
    Light = Light
    Pi_Temp = Pi_Temp
    Temperature = Temperature
    if Temperature == None or Humidity == None:
      print 'some information is not valid'
      # for dynamo_item in results:
    else:  
      response = table.put_item(
        {
          'Pi_SN':Pi_SN,
          'Timestamp':Timestamp,
          'ARM_Status':ARM_Status,
          'GPU_Status':GPU_Status,
          'Humidity':Humidity,
          'Light':Light,
          'Pi_Temp':Pi_Temp,
          'Temperature':Temperature,
        }
      )
      print 'all values inserted into the dynamoDB'
      conn.close()
      time.sleep(15)    
     
first = multiprocessing.Process(target=publishData)
first.start()
second = multiprocessing.Process(target=inserttodb)
second.start()
