import os, re
import boto, json
import boto3
from pygame import mixer
from rpi_lcd import LCD
from time import sleep
from datetime import date
from boto import dynamodb2
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex

from flask import Flask, render_template, jsonify, request, redirect, flash, session, abort

lcd = LCD()

# ==================== Connection to Dynaomo db ===================== #  
AWS_ACCESS_KEY_ID = '<your_aws_access_key>'
AWS_SECRET_ACCESS_KEY = '<your_aws_secret_key>'
REGION = 'us-west-2'
TABLE_NAME = 'Pilogs'

# ------ get the latest entry in the database ------- #
def getLatestData():    
    conn = dynamodb2.connect_to_region(REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY) # connect to AWS Dynamo db
    table = Table(TABLE_NAME,connection=conn) # get data database table Pilogs
    results = table.scan() # get all the data from db and store in results

    latest_data = {} # create an empty dictionary 

    for dynamo_items in results: # dynamo_items = <boto.dynamodb2.items.Item object at 0x73a97b10>
        dict1 = dict(dynamo_items) # store dynao_items in a dictionary and store it in dict1
        latest_data[dict1['Pi_SN']] = {} # create a nested dictionary with Pi_SN as the key
        
        # Insert into the nested dictionary such that it will be like: {'Pi_SN': {'Timestamp':value, 'Pi_Temp':value ... } }
        for key, value in dict1.items():                
            if 'Timestamp' in key:
                latest_data[dict1['Pi_SN']][key] = value # append the value of timestamp into the nested dictionary
            elif 'Pi_Temp' in key:            
                latest_data[dict1['Pi_SN']][key] = value # append the value of Pi_Temp into the nested dictionary
            elif 'ARM_Status' in key:
                latest_data[dict1['Pi_SN']][key] = value # append the value of ARM_Status into the nested dictionary
            elif 'GPU_Status' in key:
                latest_data[dict1['Pi_SN']][key] = value # append the value of GPU_Status into the nested dictionary
            elif 'Light' in key:
                latest_data[dict1['Pi_SN']][key] = str(value) # append the value of Light into the nested dictionary
            elif 'Temperature' in key:
                latest_data[dict1['Pi_SN']][key] = str(value) # append the value of Temperature into the nested dictionary
            elif 'Humidity' in key:
                latest_data[dict1['Pi_SN']][key] = str(value) # append the value of Humidity into the nested dictionary
    # return the nested dictionary 
    return latest_data

# ------ get the all Light, Temperature and Humidity entry in the database ------- #
def getData(column):
    conn = dynamodb2.connect_to_region(REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY) # connect to AWS Dynamo db
    table = Table(TABLE_NAME,connection=conn) # get data database table Pilogs
    results = table.scan() # get all the data from db and store in results

    data = {} # create an empty dictionary 

    for dynamo_items in results:        
        dict1 = dict(dynamo_items) # dynamo_items = <boto.dynamodb2.items.Item object at 0x7630d0f0>        
        data[dict1['Timestamp']] = {} # create a nested dictionary with Timestamp as the key
        
        # Insert into the nested dictionary such that it will be like: {'Timestamp': {'Pi_SN':value, 'Light':value ... } }
        for key, value in dict1.items():        
            if 'Pi_SN' in key:
                data[dict1['Timestamp']][key] = value # append the value of Pi_SN into the nested dictionary
            elif column in key:
                data[dict1['Timestamp']][key] = str(value) # append the value of column('Light', 'Temperature', 'Humidity') into the nested dictionary

    # return the nested dictiionary 
    return data 

# ==================== Controlling of LCD and output Sound ============================= #

def polly(message, voicename):
    # connect the polly to be communicating with AWS
    polly = boto3.client('polly', region_name='us-west-2', aws_access_key_id='<your_aws_access_key>',aws_secret_access_key='<your_aws_secret_key>')
    # specify the voice and output the voice text
    if message == '':
        message = "Hello! My name is " + voicename + '.......'
    spoken_text = polly.synthesize_speech(Text=message, OutputFormat='mp3', VoiceId=voicename)

    lcd.text(message,1)

    #write the audio file, and open for playing the mp3
    with open('/home/pi/output.mp3', 'wb') as f:
        f.write(spoken_text['AudioStream'].read())
        f.close()

    mixer.init()
    mixer.music.load('/home/pi/output.mp3') # prepare the mp3 file
    mixer.music.play() # play the mp3

    # check if the music player is working
    while mixer.music.get_busy() == True:
        pass
    
    mixer.quit()
    lcd.clear() # clear the LCD screen

def writetofile(serial, threshold):
    file = open("/home/pi/Desktop/IOT/assignment/CreamPi/zyPiCerts/lightThreshold.txt", "a")
    values = serial + '-' + threshold + '\n'
    file.write(values)
    file.close()

# ==================== Web Application ============================= #

app = Flask(__name__)


@app.route('/')
def index():
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        data = getLatestData() # get the lastest entry for each Raspberry Pi and store in data
        templateData = {
            'data': data, # return and pass the data to index.html
        }    
        return render_template('index.html', **templateData)

@app.route('/login', methods=['POST'])
def login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        flash('Invalid Username or Password!')
    return redirect('/')

@app.route("/logout")
def logout():    
    session['logged_in'] = False    
    return index()

@app.route('/control')
def control():
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        data = getLatestData() # get the lastest entry for each Raspberry Pi and store in data
        templateData = {
            'data': data, # return and pass the data to index.html
        }
        return render_template('control.html', **templateData) # direct page to control.html


@app.route("/awspolly", methods=['GET','POST'])
def awspolly():
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        if request.method == 'POST':
            message = request.form['message'] # get the message from the template control.html
            voicename = request.form['voicename']
            polly(message, voicename)# pass the message to the prolly function, where it will output the text message in voice
        return redirect('control')

@app.route("/threshold", methods=['GET','POST'])
def threshold():
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        if request.method == 'POST':
            threshold = request.form['threshold']
            serial = request.form['room']
            writetofile(serial, threshold)    
        return render_template('index.html')

@app.route('/camera')
def camera():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('camera.html') # direct page to camera.html

@app.route('/selectRoom/<roomNo>')
def selectRoom(roomNo): # this function allow user to select which room they would like to view
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:        
        data = getLatestData() # get the latest data from db
        global rmTemp, rmHum # call the global variable such that it can be called in the future
        rmTemp = None # initialise rmTemp as None first
        rmHum = None # initialise rmHum as None first
        for key, value in data.items(): # loop though the data to get the key('Pi_SN') and value('Temperature', 'Pi_Temp' ... )
            if roomNo in key: # check to see if the selected room exist in the database           
                for x,y in value.items(): # loop through the value to get the value {'Temperature':value, 'Pi_Temp': value, ... }
                    if 'Pi_Temp' in x:
                        global pi_temp
                        pi_temp = y # store db pi_temp in global variable pi_temp
                    elif 'Light' in x:
                        global rmLight
                        rmLight = y # store db rmLight in global variable rmLight
                    elif 'GPU_Status' in x:
                        global pi_gpu
                        pi_gpu = y # store db pi_gpu in global variable pi_gpu
                    elif 'ARM_Status' in x:
                        global pi_arm
                        pi_arm = y # store db pi_arm in global variable pi_arm
                    elif 'Temperature' in x:
                        rmTemp = y # store db rmTtemp in global variable rmTemp
                    elif 'Humidity' in x:                    
                        rmHum = y # store db rmHum in global variable rmHum

        # compile and store all the data in templateData
        templateData = {        
            'pi_temp' : pi_temp,
            'rmLight' : rmLight,
            'pi_gpu' : pi_gpu,
            'pi_arm' : pi_arm,
            'rmTemp' : rmTemp,
            'rmHum' : rmHum,
            }
        return jsonify(templateData) # return the templateData in json 

@app.route('/multipleRoom', methods=["POST"])
def multipleRoom():
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        data = getLatestData() # get the latest data from db
        multipleRoom = {} #create a empty dictionary 
        global rmTemp, rmHum
        rmTemp = None # initialise rmTemp as None first
        rmHum = None # initialise rmHum as None first
        if request.method == 'POST':
            rooms = request.form # get all the rooms from what the user select from template      
            for keyrm, valuerm in dict(rooms).items(): # loop though the data to get the key('Pi_SN') and value('Temperature', 'Pi_Temp' ... )
                for value in valuerm: 
                    for keydb, valuedb in data.items(): # loop through the value to get the value {'Temperature':value, 'Pi_Temp': value, ... } 
                        if value in keydb: # if value exist in the keydb
                            multipleRoom[value] = {} # create a nested dictionary such that the key is Pi_SN 
                            for x,y in valuedb.items():                            
                                multipleRoom[value][x] = y # append all the data into the nested dictionary based on the Pi_SN

        # compile and store the nested dictionary in templateData
        templateData = {        
            'multipleRoom' : multipleRoom
            }
        # return the templateData to room.html
        return render_template('room.html', **templateData)

@app.route('/lightLineChart/<roomNo>')
def lightLineChart(roomNo):
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        # get details of light intensity & pi_SN
        data = getData('Light')

        results = {}
        # Initialize all 24 hours
        for i in range(24):        
            results[i] = {'Light': 0.0, 'Count': 0}

        # Take the dictionary, convert to list of tuples (key, value), take out the hour from timestamp and value, then finally filter out all the non-relevant room numbers
        converted = list(filter(lambda f: f[1]['Pi_SN'] == roomNo, map(lambda x: (int(re.search(r'(\d+-\d+-\d+)\s(\d+):(\d+):(\d+)', x[0]).group(2)), x[1]), data.iteritems())))
        for c in converted:
            r = results[c[0]]
            r['Light'] += int(c[1]['Light'])
            r['Count'] += 1

        light_data = list(map(lambda d: d[1]['Light'] / d[1]['Count'] if d[1]['Count'] != 0 else 0.0, results.items()))                    
        return jsonify(light_data)


def today(element):
    return element == date.today()

@app.route('/tempLineChart/<roomNo>')
def tempLineChart(roomNo):
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        # get details of Temperature & pi_SN
        data = getData('Temperature')

        results = {}
        # Initialize all 24 hours
        for i in range(24):        
            results[i] = {'Temperature': 0.0, 'Count': 0}

        # Take the dictionary, convert to list of tuples (key, value), take out the hour from timestamp and value, then finally filter out all the non-relevant room numbers    
        converted = list(filter(lambda f: f[1]['Pi_SN'] == roomNo, map(lambda x: (int(re.search(r'(\d+-\d+-\d+)\s(\d+):(\d+):(\d+)', x[0]).group(2)), x[1]), data.iteritems())))
        for c in converted:
            r = results[c[0]]
            r['Temperature'] += int(c[1]['Temperature'])
            r['Count'] += 1

        temp_data = list(map(lambda d: d[1]['Temperature'] / d[1]['Count'] if d[1]['Count'] != 0 else 0.0, results.items()))                    
        return jsonify(temp_data)

@app.route('/humLineChart/<roomNo>')
def humLineChart(roomNo):
    if not session.get('logged_in'):        
        return render_template('login.html')
    else:
        # get details of Humidity & pi_SN
        data = getData('Humidity')

        results = {}
        # Initialize all 24 hours
        for i in range(24):        
            results[i] = {'Humidity': 0.0, 'Count': 0}

        # Take the dictionary, convert to list of tuples (key, value), take out the hour from timestamp and value, then finally filter out all the non-relevant room numbers
        converted = list(filter(lambda f: f[1]['Pi_SN'] == roomNo, map(lambda x: (int(re.search(r'(\d+-\d+-\d+)\s(\d+):(\d+):(\d+)', x[0]).group(2)), x[1]), data.iteritems())))
        for c in converted:
            r = results[c[0]]
            r['Humidity'] += int(c[1]['Humidity'])
            r['Count'] += 1

        hum_data = list(map(lambda d: d[1]['Humidity'] / d[1]['Count'] if d[1]['Count'] != 0 else 0.0, results.items()))                    
        return jsonify(hum_data)

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0')
