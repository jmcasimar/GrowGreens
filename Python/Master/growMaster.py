#!/usr/bin/env python3

# Import modules
import os
import sys
import csv
import json
import sqlite3
import colored_traceback
from datetime import datetime
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from time import time, sleep, strftime, localtime
sys.path.insert(0, './src/')
import EnvControl
from gui import GUI
from smtp import Mail
from logger import logger
from sensor import BMP280, BME680
from asciiART import asciiArt
from Calendar import Calendar
from credentials import broker, sensor
from growerData import multiGrower
from inputHandler import inputHandler
from mqttCallback import mqttController
from serialCallback import serialController

# Colored traceback useful for raise exception with colors in terminal
colored_traceback.add_hook()

art = asciiArt()
print("\033[1;32;40m", end='')
print(" Welcome to GrowGreens ".center(80,'*'))
art.img_print('./img/GrowGreens1_Web.png')
print("\033[0;37;40m")

# Check if temp dir exists, if not then create it
if not os.path.exists('temp/'): os.makedirs('temp/')
# Check if data dir exists, if not then create it
if not os.path.exists('data/'): os.makedirs('data/')

# Charge logger parameters
log = logger()

# Charge calendar parameters
growCal = Calendar()

# From communication
mGrower = multiGrower(log.logger_grower1, log.logger_grower2, log.logger_grower3, log.logger_grower4)

# From Serial Callback
serialControl = serialController(mGrower,
                                 log.logger,
                                 log.logger_generalControl,
                                 log.logger_motorsGrower,
                                 log.logger_solutionMaker,
                                 "state.json")

# Charge GUI parameters and connect logger and serialControl
gui = GUI(log.logger, serialControl)

# Define functions
def mainClose(): # When program is finishing
    # Close devices when finished
    log.logger.info("Closing devices")
    conn.close() # Database pointer
    serialControl.close()
    log.logger.info("GrowGreens Finished")
    if run: mail.sendMail("ALERTA", "GrowGreens se detuvo")
    else: mail.sendMail("ALERTA", "GrowGreens fue detenido por el operador")

def mqttDisconnect(cliente, mqttObj):
    cliente.disconnect()
    mqttObj.logMain.warning("Client MQTT Disconnected")
    mqttObj.clientConnected = False
    mqttObj.actualTime = time()

def startRoutine(grower):
    if serialControl.mgIsConnected:
        # Check if Grower is available
        if grower.failedConnection == 0:
            # It is time to move Grower
            grower.time2Move()
            top = "{}/Grower{}".format(ID, grower.floor)
            msgs = [{"topic": top, "payload": "OnLED1"},
                    {"topic": top, "payload": "OnLED2"},
                    {"topic": top, "payload": "DisableStream"}]
            publish.multiple(msgs, hostname = brokerIP)
            log.logger.info("Checking Grower{} status to start sequence".format(grower.floor))
    else: log.logger.error("Cannot start sequence. Serial device [motorsGrower] is disconnected.")
    
def checkSerialMsg(grower):
    # Resend serial messages without response for Growers
    if(grower.serialRequest!=""):
        req = False
        if(grower.serialRequest.startswith('continueSequence')
           and time()-grower.actualTime>120): req = True
        elif(not grower.serialRequest.startswith('continueSequence')
             and time()-grower.actualTime>20): req = True
        if req:
            serialControl.write(serialControl.motorsGrower, grower.serialRequest)
            grower.actualTime = time()
            log.logger.info("Resending Grower{} request: {}".format(grower.floor, grower.serialRequest))
            
def checkMqttMsg(grower):
    # Resend mqtt messages withouth response in 20s for Growers
    if(grower.mqttRequest!="" and time()-grower.actualTime>20):
        if grower.mqttRequest=="sendPhotos":
            mssg = "{},{},{},{}".format(grower.mqttRequest, brokerIP,
                broker['username'] , broker['password'])
        elif grower.mqttRequest=="routineFinish":
            mssg = [{"topic": "{}/Grower{}".format(ID, grower.floor), "payload": "OffLED1"},
                    {"topic": "{}/Grower{}".format(ID, grower.floor), "payload": "OffLED2"},
                    {"topic": "{}/Grower{}".format(ID, grower.floor), "payload": "EnableStream"}]
            #grower.mqttReq("sendPhotos")
            grower.mqttReq("")
        else: mssg = grower.mqttRequest
        if(mqttControl.clientConnected):
            try:
                if(type(mssg)==str): publish.single("{}/Grower{}".format(ID, grower.floor), mssg, hostname = brokerIP)
                elif(type(mssg)==list): publish.multiple(mssg, hostname = brokerIP)
            except Exception as e:
                log.logger.error("LAN/WLAN not found- Impossible use publish() to resend Grower{} request [{}]".format(grower.floor, e))
                mqttDisconnect(client, mqttControl)
        grower.actualTime = time()
        
# Aux Variables
try: param = sys.argv[1]
except: param = ""
start = ""
run = False

if(param==""):
    print("With this window you can check and control your production system," +
          " but before you must have completed your training. If you have not taked this" +
          " training could cause severe damage to yourself and to the system.")
    start = input("Do you want to continue? y/n\n")

if(start.startswith("y") or start.startswith("Y") or param=="start"):
    run = True
    log.logger.debug("Permission to start GrowGreens accepted")

    # Define database
    DataBase = './data/{}.db'.format(strftime("%Y-%m-%d", localtime()))
    conn = sqlite3.connect(DataBase)

    # Define config variables
    with open("config.json") as f:
        data = json.load(f)
        ID = data["ID"]
        brokerIP = data["staticIP"]
        city = data["city"]
        state = data["state"]

    # Define Mail object
    #mail = Mail(log.logger, "direccion@sippys.com.mx", city, state, ID) # Main logger, Team Ecolistico
    # Main logger, me and @IFTTT
    mail = Mail(["jmcasimar@sippys.com.mx", "trigger@applet.ifttt.com"], city, state, ID, log.logger)

    # Define variables imported form other files
    # From MQTT Callback
    mqttControl = mqttController(ID,
                                 brokerIP,
                                 conn,
                                 serialControl.mGrower,
                                 log.logger,
                                 log.logger_grower1,
                                 log.logger_grower2,
                                 log.logger_grower3,
                                 log.logger_grower4,
                                 log.logger_esp32front,
                                 log.logger_esp32center,
                                 log.logger_esp32back)

    # From inputHandler
    inputControl = inputHandler(ID, brokerIP, log.logger, serialControl, mqttControl, gui)

    try:
        # Define MQTT communication
        client = mqtt.Client()
        client.on_connect = mqttControl.on_connect  # Specify on_connect callback
        client.on_message = mqttControl.on_message  # Specify on_message callback
        #client.on_publish = mqttController.on_publish  # Specify on_publish callback
        client.on_disconnect = mqttControl.on_disconnect  # Specify on_disconnect callback
        # Connect to MQTT broker. Paremeters (IP direction, Port, Seconds Alive)
        if(client.connect(brokerIP, 1883, 60)==0): mqttControl.clientConnected = True
        else: log.logger.error("Cannot connect with MQTT Broker")
    except Exception as e: log.logger.error("Cannot connect with MQTT Broker [{}]".format(e))

    # Setting up
    if sensor['external'] == 'BMP280': bme = BMP280(log.logger) # Start bmp280 sensor
    else: bme = BME680(log.logger) # Start bme680 sensor
    day = 0
    hour = 0
    minute = 0
    boot = False
    log.logger.info("Setting up devices...")
    serialControl.open()
    log.logger.info("Devices ready")
    mail.sendMail("ALERTA", "GrowGreens acaba de iniciar")
    gui.begin()
else:
    run = False
    log.logger.warning("Permission to start GrowGreens refused")

try:
    # Main program
    while run:
        if gui.isOpen: gui.run()
        serialControl.loop()
        inputControl.loop()
        now = datetime.now()

        # If mqtt connected check for messages
        if mqttControl.clientConnected: client.loop(0.2)
        else:
            sleep(0.2)
            # Else try to reconnect every 30s
            if(time()-mqttControl.actualTime>30):
                mqttControl.actualTime = time()
                try:
                    # Reconnect client
                    client = mqtt.Client()
                    client.on_connect = mqttControl.on_connect  # Specify on_connect callback
                    client.on_message = mqttControl.on_message  # Specify on_message callback
                    #client.on_publish = mqttController.on_publish  # Specify on_publish callback
                    client.on_disconnect = mqttControl.on_disconnect  # Specify on_disconnect callback
                    # Connect to MQTT broker. Paremeters (IP direction, Port, Seconds Alive)
                    if(client.connect(brokerIP, 1883, 60)==0): mqttControl.clientConnected = True
                    else: log.logger.error("Cannot connect with MQTT Broker")

                except Exception as e: log.logger.error("Cannot connect with MQTT Broker [{}]".format(e))

        # When it is a new day
        if day!=now.day:
            # Update day
            day = now.day
            # Change database file
            splitPath = DataBase.split("/")
            DataBase = ""
            for i,spl in enumerate(splitPath):
                if i==len(splitPath)-1: DataBase += strftime("%Y-%m-%d", localtime()) + ".db"
                else: DataBase += spl + "/"
            conn.close()
            conn = sqlite3.connect(DataBase)

        # When it is a new hour
        if hour!=now.hour:
            hour = now.hour

        # When it is a new minute
        if minute!=now.minute:
            # Update Minute
            minute = now.minute
            # Save last ESP32 info and request an update
            if(boot):
                # Upload sensor data
                mqttControl.ESP32.upload2DB(conn)
                mqttControl.mGrower.upload2DB(conn)
                bme.upload2DB(conn)
                # Send to generalControl new time info
                serialControl.write(serialControl.generalControl, "updateHour,{0},{1}".format(
                    now.hour, now.minute))
            else: boot = True
            # Check if ESP32's and Growers are connected
            mqttControl.mGrower.updateStatus()
            mqttControl.ESP32.updateStatus()

            if(mqttControl.clientConnected):
                try:
                    msgs = [{"topic": "{}/Grower1".format(ID), "payload": "cozirData"},
                            {"topic": "{}/Grower2".format(ID), "payload": "cozirData"},
                            {"topic": "{}/Grower3".format(ID), "payload": "cozirData"},
                            {"topic": "{}/Grower4".format(ID), "payload": "cozirData"},
                            {"topic": "{}/esp32front".format(ID), "payload": "sendData"},
                            {"topic": "{}/esp32center".format(ID), "payload": "sendData"},
                            {"topic": "{}/esp32back".format(ID), "payload": "sendData"}]
                    # Request ESP32's and Growers data
                    publish.multiple(msgs, hostname = brokerIP)
                except Exception as e:
                    log.logger.error("LAN/WLAN not found- Impossible use publish() to request ESP&Grower data [{}]".format(e))
                    mqttDisconnect(client, mqttControl)

            # Request bme data
            if bme.read(): bme.logData()
            else: log.logger.warning("{} sensor cannot take reading".format(sensor['external']))

            # Coordinate Grower routines
            if(hour==6 and minute==0): # At 6am
                #startRoutine(mGrower.Gr1)                
                log.logger.info("Checking Grower1 status to start sequence")
            elif(hour==8 and minute==0):# At 8am
                #startRoutine(mGrower.Gr2)                
                log.logger.info("Checking Grower2 status to start sequence")
            elif(hour==10 and minute==0): # At 10am
                #startRoutine(mGrower.Gr3)                
                log.logger.info("Checking Grower3 status to start sequence")
            elif(hour==12 and minute==0): # At 12pm
                #startRoutine(mGrower.Gr4)                
                log.logger.info("Checking Grower4 status to start sequence")
            elif(hour==23 and minute==59): # At 11:59pm
                # Request mongoDB-Parse Server IP
                publish.single("{}/Server".format(ID), 'whatIsMyIP', hostname = brokerIP)
            elif(hour==0 and minute==0): # At 0am
                # Update Plant database and restart GUI
                if mqttControl.serverIP != '':
                    try:
                        gui.Seed2DB(mqttControl.serverIP)
                        gui.ResetSeedValues()
                        mqttControl.serverIP = ''
                        log.logger.info("Plant Database Updated")
                    except Exceptions as e: log.logger.error("Plant Database failed to update.\n{}".format(e))
                else: log.logger.warning("Parse Server Disconnected")
                
            elif(hour==7 and minute==0): # At 7am
                # Send Dayly tasks
                sub, msg = growCal.getEmail()
                if(msg!=''): mail.sendMail(sub, msg)
        
        # Check Serial Pending
        checkSerialMsg(mGrower.Gr1)
        checkSerialMsg(mGrower.Gr2)
        checkSerialMsg(mGrower.Gr3)
        checkSerialMsg(mGrower.Gr4)
        
        # Check MQTT Pending
        checkMqttMsg(mGrower.Gr1)
        checkMqttMsg(mGrower.Gr2)
        checkMqttMsg(mGrower.Gr3)
        checkMqttMsg(mGrower.Gr4)

        if inputControl.exit:
            ex = input("Are you sure? y/n\n")
            if (ex.startswith("y") or start.startswith("Y")):
                run = False
                mainClose() # Finished th program
                log.logger.warning("Program finished by operator")
            else:
                inputControl.exit = False
                log.logger.warning("Exit canceled")

except Exception as e:
    log.logger.critical("Exception Raised", exc_info=True)
    raise e

finally:
    if run: mainClose() # Finished the program
