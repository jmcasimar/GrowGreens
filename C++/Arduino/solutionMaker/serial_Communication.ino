/*****   Lecture on serial Events   *****/
/*
 * The structure of the commands is specified on each function
 *
 * Notes: Values of 1, 2, 3, 4, 5, 7, 9, etc... are char type, and its value is assigned according to the ASCII Table starting at char(48)="0"
 * For further information see ASCII Table
*/
const char zero_char = char(48);

void serialEvent() {                                  //if the hardware serial port_0 receives a char
  inputstring = Serial.readStringUntil(13);           //read the string until we see a <CR>
  input_string_complete = true;                       //set the flag used to tell if we have received a completed string from the PC

  if(input_string_complete==true){
    String parameter[5];
    int k = 0;
    int l = 0;
    // Split the parameters
    for (int j = 0; j<inputstring.length(); j++){
      if(inputstring[j] == ','){ // Looking for ','
        parameter[k] = inputstring.substring(l,j);
        k++;
        l = j+1;
      }
      else if(j==inputstring.length()-1){
        parameter[k] = inputstring.substring(l,j+1);
      }
    }

    // prepare()
    // -> Form "prepare,float[liters],int[sol],float[ph],float[ec]"
    if(parameter[0]==F("prepare")){
      float liters = parameter[1].toFloat();
      byte sol = parameter[2].toInt();
      float ph = parameter[3].toFloat();
      float ec = parameter[4].toFloat();
      if(liters>0){
        if(sol>=0 && sol<4){
          if(ph>0 && ph<14){
            if(ec>0){
              Serial.println(F("Request accepted"));
              Serial.print(F("info,Preparing "));
              Serial.print(liters);
              Serial.print(F(" liters of solution "));
              Serial.print(sol+1);
              Serial.print(F(" with ph="));
              Serial.print(ph);
              Serial.print(F("and ec="));
              Serial.println(ec);
              if(show){
                 delay(10000);
                 sMaker.SolFinished = true;
                 Serial.println(F("info,Solution Finished"));
                 Serial.println(F("Solution Finished"));
              } else {
                sMaker.prepareSolution(liters, sol, ph, ec);
                sMaker.eventLCD();
              }
            }
            else {Serial.println(F("error,prepare(): ec has to be positive"));}
          }
          else {Serial.println(F("error,prepare(): ph out of range [0-14]"));}
        }
        else {Serial.println(F("error,prepare(): solution out of range [0-3]"));}
      }
      else {Serial.println(F("error,prepare(): liters has to be positive"));}
    }

    // solFinished() ?
    else if(parameter[0]==F("?solutionFinished") || parameter[0]==F("?solutionFinished\n")){
      if(sMaker.SolFinished){Serial.println(F("Solution Finished"));}
      else{Serial.println(F("warning,Solution is not ready"));}
    }

    // dispense()
    // -> Form "dispense,int[Motor],long[grams]"
    else if(parameter[0]==F("dispense")){
      int act = parameter[1].toInt();
      long grams = parameter[2].toFloat();
      if(act>=0 && act<MAX_SOLUTIONS_NUMBER){
        if(grams>0){
          sMaker.dispense(long(grams*1000), act);
          sMaker.eventLCD();
        }
        else{ Serial.println(F("error,dispense(): Grams has to be positive"));}
      }
      else{ Serial.println(F("error,dispense(): Motor out of range [0-3]"));}
    }

    // dispenseAcid()
    // -> Form "dispenseAcid,int[pump],float[mililiters]"
    else if(parameter[0]==F("dispenseAcid")){
      int act = parameter[1].toInt();
      float mililiters = parameter[2].toFloat();
      if(act>=0 && act<MAX_PUMPS_NUMBER){
        if(mililiters>0){
          sMaker.dispenseAcid(mililiters, act);
          sMaker.eventLCD();
        }
        else{ Serial.println(F("error,dispenseAcid(): Mililiters has to be positive"));}
      }
      else{ Serial.println(F("error,dispenseAcid(): Pump out of range [0-1]"));}
    }

    // stop()
    else if(parameter[0]==F("stop")){
      int act = parameter[2].toInt();

      // -> Form "stop,motor,int[motor]"
      if(parameter[1]==F("motor")){
        if(act>=0 && act<MAX_SOLUTIONS_NUMBER){
          sMaker.stop(act);
          sMaker.eventLCD();
        }
        else{ Serial.println(F("error,stop(): Motor out of range [0-3]"));}
      }

      // -> Form "stop,pump,int[pump]"
      else if(parameter[1]==F("pump")){
        if(act>=0 && act<MAX_PUMPS_NUMBER){
          sMaker.stop(act+MAX_SOLUTIONS_NUMBER);
          sMaker.eventLCD();
        }
        else{ Serial.println(F("error,stop(): Pump out of range [0-1]"));}
      }
      else{Serial.println(F("error,stop(): Parameter[1] does not match a type"));}
    }

    // calibration()
    else if(parameter[0]==F("calibration")){

      // -> Form "calibration,motor,int[motor],long[revolutions]"
      if(parameter[1]==F("motor")){
        int act = parameter[2].toInt();
        long rev = parameter[3].toInt();
        if(act>=0 && act<MAX_SOLUTIONS_NUMBER){
          if(rev>0){
            sMaker.stepperCalibration(rev, act);
            sMaker.eventLCD();
          }
          else{ Serial.println(F("error,calibration(): Revotutions has to be positive"));}
        }
        else{ Serial.println(F("error,calibration(): Motor out of range [0-3]"));}
      }

      // -> Form "calibration,pump,int[pump],long[Time]"
      else if(parameter[1]==F("pump")){
        int act = parameter[2].toInt();
        float Time = parameter[3].toFloat();
        if(act>=0 && act<MAX_PUMPS_NUMBER){
          if(Time>0){
            sMaker.pumpCalibration(Time, act);
            sMaker.eventLCD();
          }
          else{ Serial.println(F("error,calibration(): Time has to be positive"));}
        }
        else{ Serial.println(F("error,calibration(): Pump out of range [0-1]"));}
      }

      // Set parameters for motors/pumps
      // -> Form "calibration,setCal,int[act],int[param]" param must be the (mg/rev)/40
      else if(parameter[1]==F("setCal")){
        int act = parameter[2].toInt();
        int param = parameter[3].toInt();
        if(act>=0 && act<MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER){
          if(param>=0 && param<=255){
            sMaker.setCalibrationParameter(param, act);
            sMaker.eventLCD();
            write_EEPROM(act, param);
          }
          else{Serial.println(F("error,calibration(): Parameter must be a byte [0-255]"));}
        }
        else{Serial.println(F("error,calibration(): Actuator out of range [0-5]"));}
      }

      // Set parameter for ph/ec equations
      // -> Form "calibration,setCal1,int[act],int[param]"
      else if(parameter[1]==F("setCal1")){
        int act = parameter[2].toInt();
        int param = parameter[3].toInt();
        if(act>=0 && act<MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER){
          if(param>=0 && param<=255){
            sMaker.setCalibrationParameter1(param, act);
            sMaker.eventLCD();
            write_EEPROM(act+MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER, param);
          }
          else{Serial.println(F("error,calibration(): Parameter must be a byte [0-255]"));}
        }
        else{Serial.println(F("error,calibration(): Actuator out of range [0-5]"));}
      }
      else{Serial.println(F("error,calibration(): Parameter[1] does not match a type"));}
    }

    // ezo()
    else if(parameter[0]==F("ezo")){
      int sensorType = 10;
      String sensorString = "";
      if(parameter[1]==F("ph")){
        sensorType = EZO_PH;
        sensorString = "phmeter";
      }
      else if(parameter[1]==F("ec")){
        sensorType = EZO_EC;
        sensorString = "ecmeter";
      }
      if(sensorType==EZO_PH || sensorType==EZO_EC){
        // -> Form "ezo,sensorType[ph/ex],isEnable"
        if(parameter[2]==F("isEnable") || parameter[2]==F("isEnable\n")){
          if(sMaker.EZOisEnable(sensorType)){
            Serial.print(sensorString);
            Serial.println(F(": Enable"));
          }
          else{
            Serial.print(sensorString);
            Serial.println(F(": Disable"));
          }
        }
        // -> Form "ezo,sensorType[ph/ex],calibration,int[action],float[val]"
        else if(parameter[2]==F("calibration")){
          int action = parameter[3].toInt();
          float val = parameter[4].toFloat();
          sMaker.EZOcalibration(sensorType, action, val);
        }
        else if(parameter[2]==F("exportCal") || parameter[2]==F("exportCal\n")){ // -> Form "ezo,sensorType[ph/ex],exportCal"
          sMaker.EZOexportCal(sensorType);
        }
        else if(parameter[2]==F("startImport") || parameter[2]==F("startImport\n")){ // -> Form "ezo,sensorType[ph/ex],startImport"
          sMaker.EZOimport(true);
        }
        else if(parameter[2]==F("stopImport") || parameter[2]==F("stopImport\n")){ // -> Form "ezo,sensorType[ph/ex],stopImport"
          sMaker.EZOimport(false);
        }
        else if(parameter[2]==F("importCal") || parameter[2]==F("importCal\n")){ // -> Form "ezo,sensorType[ph/ex],importCal"
          sMaker.EZOimportCalibration(sensorType, parameter[3]);
        }
        else if(parameter[2]==F("sleep") || parameter[2]==F("sleep\n")){ // -> Form "ezo,sensorType[ph/ex],sleep"
          if(!sMaker.EZOisSleep()) Serial.println(F("warning,EZO Sensors: Enter into sleep mode"));
          sMaker.EZOsleep();
        }
        else if(parameter[2]==F("awake") || parameter[2]==F("awake\n")){ // -> Form "ezo,sensorType[ph/ex],awake"
          if(sMaker.EZOisSleep()) Serial.println(F("warning,EZO Sensors: Awaking sensors"));
          sMaker.EZOawake();
        }
        else if (parameter[2]==F("info") || parameter[2]==F("info\n")){ // Form "ezo,sensorType[ph/ec],info"
          sMaker.EZOinformation();
        }
        else{Serial.println(F("error,ezo(): Parameter[2] does not match a type"));}
      }
      else{Serial.println(F("error,ezo(): Parameter[1] does not match a type"));}
    }

    // filter()
    else if(parameter[0]==F("filter")){
      if(parameter[1]==F("notFilter") || parameter[1]==F("notFilter\n")){ // -> Form "filter,notFilter"
        sMaker.notFilter();
      }
      else if(parameter[1]==F("default") || parameter[1]==F("default\n")){ // -> Form "filter,defaultFilter"
        sMaker.defaultFilter();
      }
      else if(parameter[1]==F("exponential")){ // -> Form "filter,exponential,float[alpha]"
        float alpha = parameter[2].toFloat();
        if(alpha>0 && alpha<1) sMaker.setExponentialFilter(alpha);
        else Serial.println(F("error,filter(): alpha out of range [0-1]"));
      }
      else if(parameter[1]==F("kalman")){ // -> Form "filter,exponential,kalman,float[noise]"
        float noise = parameter[2].toFloat();
        if(noise>0) sMaker.setKalmanFilter(noise);
        else Serial.println(F("error,filter(): noise has to be positive"));
      }
      else if(parameter[1]==F("print") || parameter[1]==F("print\n")){ // -> Form "filter,print"
        sMaker.printFilter();
      }
      else{Serial.println(F("error,filter(): Parameter[1] does not match a type"));}
    }

    // eeprom()
    else if(parameter[0]==F("eeprom")){
      if(parameter[1]==F("print") || parameter[1]==F("print\n")){ // -> Form "eeprom,print"
        print_EEPROM();
      }
      else if(parameter[1]==F("read") || parameter[1]==F("read\n")){ // -> Form "eeprom,read"
        read_EEPROM(HIGH);
      }
      else if(parameter[1]==F("clean") || parameter[1]==F("clean\n")){ // -> Form "eeprom,clean"
        clean_EEPROM();
      }
    }

    else{Serial.println(F("warning, Serial Command Unknown"));}
  }
  input_string_complete = false;
}
