#!/usr/bin/env python3

# Import directories
from serial import Serial
from time import time, sleep
from systemState import systemState

class serialController:
    def __init__(self, multiGrower, loggerMain, loggerGC, loggerMG, loggerSM, stateFile):
        # Define loggers
        self.logMain = loggerMain
        self.logGC = loggerGC
        self.logMG = loggerMG
        self.logSM = loggerSM
        
        # Define microcontrolers
        try:
            self.generalControl = Serial('/dev/generalControl', 115200, timeout=0)
            self.generalControl.dtr = False # Reset
            self.generalControl.close()
            self.gcIsConnected = True
        except Exception as e:
            self.gcIsConnected = False
            raise Exception("Communication with generalControl device cannot be stablished. [{}]".format(e))
        try:
            self.motorsGrower = Serial('/dev/motorsGrower', 115200, timeout=0)
            self.motorsGrower.dtr = False # Reset
            self.motorsGrower.close()
            self.mgIsConnected = True
        except Exception as e:
            self.mgIsConnected = False
            self.logMain.error("Communication with motorsGrower device cannot be stablished. [{}]".format(e))
        try:
            self.solutionMaker = Serial('/dev/solutionMaker', 115200, timeout=0)
            self.solutionMaker.dtr = False # Reset
            self.solutionMaker.close()
            self.smIsConnected = True
        except Exception as e:
            self.smIsConnected = False
            self.logMain.error("Communication with solutionMaker device cannot be stablished. [{}]".format(e))
        # Define multiGrower variables with mqtt module
        self.mGrower = multiGrower
        # Define responses auxVariables
        self.resp = []
        self.respLine = []
        self.respTime = time()
        # Charge system state
        self.system = systemState(stateFile)
        if(self.system.load()): self.logMain.info("System State charged")
        else: self.logMain.error("Cannot charge System State because it does not exist")
        
    def open(self):
        if self.gcIsConnected and not self.generalControl.is_open:
            self.generalControl.open()
            sleep(0.33)
            self.generalControl.reset_input_buffer()
            self.generalControl.dtr = True
        if self.mgIsConnected and not self.motorsGrower.is_open:
            self.motorsGrower.open()
            sleep(0.33)
            self.motorsGrower.reset_input_buffer()
            self.motorsGrower.dtr = True
        if self.smIsConnected and not self.solutionMaker.is_open:
            self.solutionMaker.open()
            sleep(0.33)
            self.solutionMaker.reset_input_buffer()
            self.solutionMaker.dtr = True
    
    def close(self):
        if self.gcIsConnected and self.generalControl.is_open: self.generalControl.close()
        if self.mgIsConnected and self.motorsGrower.is_open: self.motorsGrower.close()
        if self.smIsConnected and self.solutionMaker.is_open:self.solutionMaker.close()
    
    def Msg2Log(self, logger, mssg):
        if(mssg.startswith("debug,")): logger.debug(mssg.split(",")[1])
        elif(mssg.startswith("info,")): logger.info(mssg.split(",")[1])
        elif(mssg.startswith("warning,")): logger.warning(mssg.split(",")[1])
        elif(mssg.startswith("error,")): logger.error(mssg.split(",")[1])
        elif(mssg.startswith("critical,")): logger.critical(mssg.split(",")[1])
        else: logger.debug(mssg)

    def write(self, serialObject, mssg):
        if serialObject == self.generalControl and self.gcIsConnected: aux = True
        elif serialObject == self.motorsGrower and self.mgIsConnected: aux = True
        elif serialObject == self.solutionMaker and self.smIsConnected: aux = True
        if aux:
            serialObject.write(bytes(mssg, "utf-8"))
            serialObject.flush()
        else: self.logMain.error("Cannot write to serial device. It is disconnected.")
            
    def cleanLine(self, line):
        resp = line.split(",")
        if len(resp)>1: return resp[1]
        else: return resp[0]
    
    def detectGrower(self, line):
        if(line.startswith("Grower1")): return 1
        elif(line.startswith("Grower2")): return 2
        elif(line.startswith("Grower3")): return 3
        elif(line.startswith("Grower4")): return 4
        else: return 0
    
    def cleanGrowerLine(self, line):
        resp = line.split(":")[1][1:]
        return resp
    
    def getGrowerLine(self, line):
        resp = self.cleanLine(line)
        num = self.detectGrower(resp)
        return resp, num
    
    def startGrowerSequence(self, fl):
        if fl==1:
            self.mGrower.Gr1.serialReq("")
            x, y = self.mGrower.Gr1.getSequenceParameters()
        elif fl==2:
            self.mGrower.Gr2.serialReq("")
            x, y = self.mGrower.Gr2.getSequenceParameters()
        elif fl==3:
            self.mGrower.Gr3.serialReq("")
            x, y = self.mGrower.Gr3.getSequenceParameters()
        elif fl==4:
            self.mGrower.Gr4.serialReq("")
            x, y = self.mGrower.Gr4.getSequenceParameters()
        self.write(self.motorsGrower, "sequence,{},{},{}".format(fl,x,y))
        self.logMain.info("Grower{} sending request to start sequence".format(fl))
    
    def stopGrower(self, fl):
        self.write(self.motorsGrower, "stop,{}".format(fl))
        self.logMain.warning("Grower{} is busy, sending request to stop".format(fl))
    
    def decideStartOrStopGrower(self, resp):
        auxBool = False
        num = self.detectGrower(resp)
        if(num==1): auxBool = self.mGrower.Gr1.startRoutine
        elif(num==2): auxBool = self.mGrower.Gr2.startRoutine
        elif(num==3): auxBool = self.mGrower.Gr3.startRoutine
        elif(num==4): auxBool = self.mGrower.Gr4.startRoutine
        
        if(num>=1 and num<=4): resp = self.cleanGrowerLine(resp)
        if resp.startswith("Available") and auxBool:
            self.startGrowerSequence(num)
            return True
        elif resp.startswith("Unavailable") and auxBool:
            self.stopGrower(num)
            return True
        
        return False
        
    def GrowerInRoutine(self, fl):
        if(fl==1):
            self.mGrower.Gr1.startRoutine = False
            self.mGrower.Gr1.inRoutine = True
            self.mGrower.Gr1.count = 0
        elif(fl==2):
            self.mGrower.Gr2.startRoutine = False
            self.mGrower.Gr2.inRoutine = True
            self.mGrower.Gr2.count = 0
        elif(fl==3):
            self.mGrower.Gr3.startRoutine = False
            self.mGrower.Gr3.inRoutine = True
            self.mGrower.Gr3.count = 0
        elif(fl==4):
            self.mGrower.Gr4.startRoutine = False
            self.mGrower.Gr4.inRoutine = True
            self.mGrower.Gr4.count = 0
        self.logMain.info("Grower{} sequence started".format(fl))
    
    def GrowerInPosition(self, fl):
        # request Grower to take pictures
        if(fl==1):
            photoName = self.mGrower.Gr1.count
            self.mGrower.Gr1.count += 1
            self.mGrower.Gr1.serialReq("")
            self.mGrower.Gr1.mqttReq("photoSequence,{}".format(photoName))
            self.mGrower.Gr1.actualTime = time()-20
        elif(fl==2):
            photoName = self.mGrower.Gr2.count
            self.mGrower.Gr2.count += 1
            self.mGrower.Gr2.serialReq("")
            self.mGrower.Gr2.mqttReq("photoSequence,{}".format(photoName))
            self.mGrower.Gr2.actualTime = time()-20
        elif(fl==3):
            photoName = self.mGrower.Gr3.count
            self.mGrower.Gr3.count += 1
            self.mGrower.Gr3.serialReq("")
            self.mGrower.Gr3.mqttReq("photoSequence,{}".format(photoName))
            self.mGrower.Gr3.actualTime = time()-20
        elif(fl==4):
            photoName = self.mGrower.Gr4.count
            self.mGrower.Gr4.count += 1
            self.mGrower.Gr4.serialReq("")
            self.mGrower.Gr4.mqttReq("photoSequence,{}".format(photoName))
            self.mGrower.Gr4.actualTime = time()-20
        
        self.logMain.debug("Grower{} in position to take photo sequence".format(fl))
    
    def GrowerRoutineFinish(self, fl):
        if(fl==1):
            self.mGrower.Gr1.count = 1
            self.mGrower.Gr1.mqttReq("routineFinish")
            self.mGrower.Gr1.serialReq("")
            self.mGrower.Gr1.inRoutine = False
            self.mGrower.Gr1.actualTime = time()-20
        elif(fl==2):
            self.mGrower.Gr2.count = 1
            self.mGrower.Gr2.mqttReq("routineFinish")
            self.mGrower.Gr2.serialReq("")
            self.mGrower.Gr2.inRoutine = False
            self.mGrower.Gr2.actualTime = time()-20
        elif(fl==3):
            self.mGrower.Gr3.count = 1
            self.mGrower.Gr3.mqttReq("routineFinish")
            self.mGrower.Gr3.serialReq("")
            self.mGrower.Gr3.inRoutine = False
            self.mGrower.Gr3.actualTime = time()-20
        elif(fl==4):
            self.mGrower.Gr4.count = 1
            self.mGrower.Gr4.mqttReq("routineFinish")
            self.mGrower.Gr4.serialReq("")
            self.mGrower.Gr4.inRoutine = False
            self.mGrower.Gr4.actualTime = time()-20
        self.logMain.info("Grower{} finished its routine".format(fl))
        
    def sendBootParams(self):
        self.write(self.generalControl, "boot,{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format(
            self.system.state["solution"], self.system.state["volumenNut"],
            self.system.state["volumenH2O"], self.system.state["consumptionNut"],
            self.system.state["consumptionH2O"], self.system.state["pumpIn"],
            self.system.state["IPC"], self.system.state["MPC"],
            self.system.state["missedNut"], self.system.state["missedH2O"]))
        
    def updateSystemState(self, index):
        param = self.respLine[index].split(",")
        if(len(param)>=11 and param[-1]!=''):
            if(self.system.update("solution", int(param[1]))): pass
            #self.logMain.debug("System Solution Updated")
            else: self.logMain.error("Cannot Update Solution State")
            if(self.system.update("volumenNut", float(param[2]))): pass
            #self.logMain.debug("System volNut Updated")
            else: self.logMain.error("Cannot Update volNut State")
            if(self.system.update("volumenH2O", float(param[3]))): pass
            #self.logMain.debug("System volH2O Updated")
            else: self.logMain.error("Cannot Update volH2O State")
            if(self.system.update("consumptionNut", float(param[4]))): pass
            #self.logMain.debug("System consNut Updated")
            else: self.logMain.error("Cannot Update consNut State")
            if(self.system.update("consumptionH2O", float(param[5]))): pass
            #self.logMain.debug("System consH2O Updated")
            else: self.logMain.error("Cannot Update consH2O State")
            if(self.system.update("pumpIn", int(param[6]))): pass
            #self.logMain.debug("System pumpIn Updated")
            else: self.logMain.error("Cannot Update pumpIn State")
            if(self.system.update("IPC", int(param[7]))): pass
            #self.logMain.debug("System IPC Updated")
            else: self.logMain.error("Cannot Update IPC State")
            if(self.system.update("MPC", int(param[8]))): pass
            #self.logMain.debug("System MPC Updated")
            else: self.logMain.error("Cannot Update MPC State")
            if(self.system.update("missedNut", float(param[9]))): pass
            #self.logMain.debug("System missedNut Updated")
            else: self.logMain.error("Cannot Update missedNut State")
            if(self.system.update("missedH2O", float(param[10]))): pass
            #self.logMain.debug("System missedH2O Updated")
            else: self.logMain.error("Cannot Update missedH2O State")
            
        else: self.logMain.error("Line incomplete - {}".format(self.respLine[index]))
    
    def requestSolution(self, index):
        # Form -> "?solutionMaker,float[liters],int[sol],float[ph],int[ec]"
        param = self.respLine[index].split(",")
        if(len(param)>=5):
            liters = float(param[1])
            solution = int(param[2])
            ph = float(param[3])
            ec = int(param[4])
            self.logMain.debug("Prepare Solution line: {}".format(self.respLine[index]))
            # Check parameters
            if(liters>0):
                if(solution>=0 and solution<4):
                    if(ph>0 and ph<14):
                        if(ec>0 and ec<5000):
                            # If parameters correct then request a solution
                            self.write(self.solutionMaker, "prepare,{0},{1},{2},{3}".format(
                                liters, solution, ph, ec))
                        else: self.logGC.error("solutionMaker ec out of range [0-5000]")
                    else: self.logGC.error("solutionMaker ph out of range [0-14]")
                else: self.logGC.error("solutionMaker solution out of range [0-3]")
            else: self.logGC.error("solutionMaker liters has to be positive")
        else: self.logMain.error("Line incomplete - {}".format(self.respLine[index]))            
        
    def concatResp(self, resp, line):
        # If that request is not save
        if not resp in self.resp:
            self.resp.append(resp) # Add the request
            self.respLine.append(line) # Add the line
            self.respTime = time() # Restart timer
            
    def response(self):
        if not self.gcIsConnected or self.generalControl.in_waiting==0: gControl = True
        else: gControl = False
        if not self.mgIsConnected or self.motorsGrower.in_waiting==0: motorG = True
        else: motorG = False
        if not self.smIsConnected or self.solutionMaker.in_waiting==0: sMaker = True
        else: sMaker = False
        if(time()-self.respTime>1 and gControl and motorG and sMaker and len(self.resp)>0):
            for i, resp in enumerate(self.resp):
                # generalControl is requesting the necessary booting parameters
                if(resp == "boot"): self.sendBootParams()            
                # Update system state
                elif(resp == "updateSystemState"): self.updateSystemState(i)
                # generalControl is requesting to prepare a solution
                elif(resp == "requestSolution"): self.requestSolution(i)
                # generalControl ask if sMaker finished to prepare the solution
                elif(resp == "askSolFinished"): self.write(self.solutionMaker, "?solutionFinished")
                # solutionMaker accepts to prepare a new solution
                elif(resp == "requestAccepted"): self.write(self.generalControl, "solutionMaker,accept")
                # solutionMaker finished to prepare the solution
                elif(resp == "solutionFinished"): self.write(self.generalControl, "solutionMaker,finished")
                    
                self.logMain.debug("Request {} was answered".format(resp))
              
            self.resp = []
            self.respLine = []           
            
    def loop(self):
        if self.gcIsConnected:
            # If bytes available in generalControl
            while self.generalControl.in_waiting>0:
                line1 = str(self.generalControl.readline(), "utf-8")[0:-1]
                self.Msg2Log(self.logGC, line1)
                if(line1.startswith("?boot")):
                    self.concatResp("boot", line1)
                elif(line1.startswith("updateSystemState")):
                    self.concatResp("updateSystemState", line1)
                elif(line1.startswith("?solutionMaker")):
                    if self.smIsConnected: self.concatResp("requestSolution", line1)
                    else: self.concatResp("requestAccepted", line1)
                elif(line1.startswith("?solutionFinished")):
                    if self.smIsConnected: self.concatResp("askSolFinished", line1)
                    else: self.concatResp("solutionFinished", line1)
        
        if self.mgIsConnected:
            # If bytes available in motorsGrower
            while self.motorsGrower.in_waiting>0:
                line2 = str(self.motorsGrower.readline(), "utf-8")[0:-1]
                self.Msg2Log(self.logMG, line2)
                
                decition = False
                # If we are waiting for a particular response from Grower1
                if(self.mGrower.Gr1.serialRequest!="" and not decition):
                    decition = self.decideStartOrStopGrower(self.cleanLine(line2))
                    
                # If we are waiting for a particular response from Grower2
                if(self.mGrower.Gr2.serialRequest!="" and not decition):
                    decition = self.decideStartOrStopGrower(self.cleanLine(line2))
                            
                # If we are waiting for a particular response from Grower3
                if(self.mGrower.Gr3.serialRequest!="" and not decition):
                    decition = self.decideStartOrStopGrower(self.cleanLine(line2))
                        
                # If we are waiting for a particular response from Grower4
                if(self.mGrower.Gr4.serialRequest!="" and not decition):
                    decition = self.decideStartOrStopGrower(self.cleanLine(line2))
                
                # If we are waiting Gr1 to reach home and start the sequence
                if(self.mGrower.Gr1.serialRequest=="" and self.mGrower.Gr1.startRoutine and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==1):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("Starting Routine Stage 2"):
                            decition = True
                            self.GrowerInRoutine(num)
                            
                # If we are waiting Gr2 to reach home and start the sequence
                if(self.mGrower.Gr2.serialRequest=="" and self.mGrower.Gr2.startRoutine and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==2):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("Starting Routine Stage 2"):
                            decition = True
                            self.GrowerInRoutine(num)
                            
                # If we are waiting Gr3 to reach home and start the sequence
                if(self.mGrower.Gr3.serialRequest=="" and self.mGrower.Gr3.startRoutine and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==3):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("Starting Routine Stage 2"):
                            decition = True
                            self.GrowerInRoutine(num)
                            
                # If we are waiting Gr4 to reach home and start the sequence
                if(self.mGrower.Gr4.serialRequest=="" and self.mGrower.Gr4.startRoutine and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==4):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("Starting Routine Stage 2"):
                            decition = True
                            self.GrowerInRoutine(num)
                    
                # If we are waiting Gr1 to reach next sequence position
                if(self.mGrower.Gr1.inRoutine and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==1):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("In Position"):
                            decition = True
                            self.GrowerInPosition(num)
                        elif resp.startswith("Routine Finished"):
                            decition = True
                            self.GrowerRoutineFinish(num)
                            
                # If we are waiting Gr2 to reach next sequence position
                if(self.mGrower.Gr2.inRoutine and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==2):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("In Position"):
                            decition = True
                            self.GrowerInPosition(num)
                        elif resp.startswith("Routine Finished"):
                            decition = True
                            self.GrowerRoutineFinish(num)
                            
                # If we are waiting Gr3 to reach next sequence position
                if(self.mGrower.Gr3.inRoutine  and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==3):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("In Position"):
                            decition = True
                            self.GrowerInPosition(num)
                        elif resp.startswith("Routine Finished"):
                            decition = True
                            self.GrowerRoutineFinish(num)
                            
                # If we are waiting Gr4 to reach next sequence position
                if(self.mGrower.Gr4.inRoutine and not decition):
                    resp, num = self.getGrowerLine(line2)
                    if(num==4):
                        resp = self.cleanGrowerLine(resp)
                        if resp.startswith("In Position"):
                            decition = True
                            self.GrowerInPosition(num)
                        elif resp.startswith("Routine Finished"):
                            decition = True
                            self.GrowerRoutineFinish(num)
        
        if self.smIsConnected:
            # If bytes available in solutionMaker
            while self.solutionMaker.in_waiting>0:
                line3 = str(self.solutionMaker.readline(), "utf-8")[0:-1]
                self.Msg2Log(self.logSM, line3)
                self.respTime = time()
                if(line3.startswith("Request accepted")):
                    self.concatResp("requestAccepted", line3)
                elif(line3.startswith("Solution Finished")):
                    self.concatResp("solutionFinished", line3)
        
        # Send all responses
        self.response()