/*
Library for Grow software package
Written by : José Manuel Casillas Martín
email: jmcasimar@sippys.com.mx
Date : 2019-*-*
Version : 0.1 (testing version)

This file is part of Grow Software Package.

Grow is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Grow is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Grow.  If not, see <https://www.gnu.org/licenses/>.
*/

// solutionMaker.h

#ifndef solutionMaker_h
#define solutionMaker_h

#include <stdlib.h>
#if ARDUINO >= 100
#include <Arduino.h>
#else
#include <WProgram.h>
#include <wiring.h>
#endif

#include "AccelStepper.h" // Include AccelStepper library
#include <Wire.h> // Necessary for I2C communication
#include <LiquidCrystal_I2C.h> // For LCD screen
#include <OneWire.h> // Necessary for 1-wire communication
#include <DallasTemperature.h> // For temperature sensor
#include <EZO.h> // For Atlas Scientific sensors
#include <math.h> // For ph/conductivity equations
#include <Servo.h>

#define MAX_SOLUTIONS_NUMBER 4 // The max number of motors that can be dispense
#define MAX_PUMPS_NUMBER 2 // The max number of peristaltic pumps
#define MOTOR_SPEED 4000 // Maximum Steps Per Second
#define MOTOR_ACCEL 1000 // Steps/second/Second of acceleration
#define DEFAULT_MICROSTEP 8 // By default we use configuration of 1/8 microSteps
#define MOTOR_STEP_PER_REV 200 // By default we use motors of 200 steps/rev
#define PUMP_VELOCITY 255 // Value pwm -> 255 = 100%, 155 = 60% of the maximun velocity.
// Less than 155(60%) may not work
#define LCD_I2C_DIR 0x27 // Direction for screen
#define LCD_COLUMNS 20 // Screen columns number
#define LCD_ROWS 4 // Screen rows number
#define RELAY_ACTION_TIME 15000 // 15 seconds by default

// Class to control the Solution Maker
/*
Note: All the motors need same configuration and direction
Some definitions:
  Solution 1 = KNO3
  Solution 2 = NH4H2PO04
  Solution 3 = CA(NO3)2
  Solution 4 = MGSO4 + Micros
  Acid 1 = H3PO4
  Acid 2 = HNO3

  Sol 1 -> Acid 1
  Sol 2 -> Acid 1
  Sol 3 -> Acid 4
  Sol 4 -> Acid 4
*/

class solutionMaker
  {
    private:
        uint8_t        __DirS[MAX_SOLUTIONS_NUMBER], __StepS[MAX_SOLUTIONS_NUMBER]; // Pins required for all the motors
        uint8_t        __Motor[MAX_PUMPS_NUMBER*2]; // Pins to control all the peristaltic pumps
        uint8_t        __En[MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER]; // Pin to enable all the motors and pumps
        uint8_t        __Relay1; // Pin to control relay
        bool           __IsEnable[MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER]; // Let´s know if the motor/pump isenable/disable
        bool           __Available[MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER]; // Let´s know if the motor/pump available/unavailable
        uint8_t        __Calibration[MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER]; // Calibration parameter for motor/pumps
        uint8_t        __Calibration1[MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER]; // Calibration parameter for ph/conductivity equations

        uint8_t        __MicroSteps; // Inverse of the configurated microSteps in the driver
        uint8_t        __StepPerRev; // Steps per rev

        uint8_t        __PumpVelocity; // pwm value
        bool           __InvertPump; // Invert the direction of all the pumps
        unsigned long  __PumpTime[MAX_PUMPS_NUMBER]; // Time counter for pumps working
        unsigned long  __PumpOnTime[MAX_PUMPS_NUMBER]; // The time that the pumps will be working
        unsigned long  __ReadTime, __RelayTime, __LCDTime; // Auxiliars counter for sensorReads, relays ans LCD turn off light
        // One led for each solution, one for each acid and two for status
        uint8_t        __Led[MAX_SOLUTIONS_NUMBER+MAX_PUMPS_NUMBER+2]; // Pins for LED´s
        uint8_t        __LCDButton; // Pin to read LCD button

        bool           __Work; // Variable to know if is working the Solution Maker
        bool           __StatusLCD; // Variable to know if the screen is on/off
        bool           __LCDLightOn; // Variable to turn off the LCD light
        bool           __RelayState; // Variable to hold the state of the relay

        // Atlas Scientific Sensors variables
        float __pH, __eC; // Variables to hold the phMeter and ecMeter values
        // Variable to know if some Atlas Scientific Sensor is exporting its calibration parameters
        bool  __ExportEzo;
        bool  __ImportEzo; // Variable to know if we are importing some calibration parameter
        bool  __SleepEzo; // Variable to know if Atlas Scientific Sensors are in sleep mode

        // Temperature sensor
        float __Temp; // Variable to hold the temperature
        float __LCDTemp; // Variable to change the Temp Value on LCD

        // Constants for the filters
        uint8_t __Filter;
        float __Alpha , __Noise , __Err;
        // Exponential Filter: __Alpha = smoothing variable
        // Kalman Filter: __Noise = Enviromental Noise, __Err = Error

        // Pointers
        AccelStepper *stepperS[MAX_SOLUTIONS_NUMBER]; // Pointer for each stepper motor
        EZO *phMeter; // Pointer to phMeter (Atlas Scientific sensor)
        EZO *ecMeter; // Pointer to ecMeter (Atlas Scientific sensor)
        OneWire *ourWire; // Pointer to Wire Object
        DallasTemperature *tempSensor; // Pointer to temperature sensor
        LiquidCrystal_I2C *lcd; // Pointer to control LCD screen
        Servo *SolutionServo[MAX_SOLUTIONS_NUMBER];


        bool isWorking(); // Returns true if some actuator is unavailable, else false
        void enable(uint8_t actuator); // Enable/Disable the actuator
        void disable(uint8_t actuator); // Disable the actuator
        void turnOnPump(unsigned long time1, uint8_t pump); // Turn on pump
        void turnOffPump(uint8_t pump); // Turn off pump
        /* Converts time [s] to volume [ml] for the pumps
            By default use calibration param of the first pump assuming that all are equals
        */
        unsigned long TimeToML(float seconds, uint8_t pump);
        /* Converts volume [ml] to time [s] for the pumps
            By default use calibration param of the first pump assuming that all are equals
        */
        unsigned long MLToTime(float mililiters, uint8_t pump);
        // Return the number of mg that equals the revs parameter in some stepper
        long RevToMG(long rev, uint8_t st);
        // Return the number of revs that equals the mg parameter in some stepper
        long MGToRev(long mg, uint8_t st);
        long RevToSteps(long rev); // Returns the number of steps that are require to move one rev
        long StepsToRev(long st); // Returns the number of rev that are some steps
        // Calculate how much mg of powder or liters of H2O do you need to balance conductivity
        float balanceEC(float EC_init, float EC_final, float liters, uint8_t st);
        // Calculate how much ml of acid or liters of H2O do you need to balance ph
        float balancePH(float PH_init, float PH_final, float liters, uint8_t pump);
        void moveStepper(long steps, uint8_t st);
        void resetPosition(uint8_t st); // reset the position to zero of some stepper
        // Print in serial an action executed with the correct format
        void printAction(String act, uint8_t actuator, uint8_t level=0);
        // Print in serial an action executed with the correct format (Atlas Scientific Sensors)
        void printEZOAction(String act, uint8_t sensorType, uint8_t level=0);
        void printLCD(String main, String subAction = ""); // Print something in LCD Screen
        void checkButtonLCD(); // Check if the button is pressed and turn on the backlight
        float filter(float val, float preVal);
        float exponential_filter(float alpha, float t, float t_1);
        float kalman_filter(float t, float t_1);
        void readTemp(); // Read temperature from DSB1820
        void EZOReadRequest(float temp, bool sleep = false); // Request a single read in Atlas Scientific Sensors
        void readRequest(); // Request a single reading of the temperature, ph and ec
        void EZOexportFinished(); // When some export is finished set variable to ask for a new one
        void relayControl(); // Control the actions of the relay

    public:
        bool SolFinished; // Variable to know if the last Solution request finished

        // Constructor. Dir, Step and Enable Pins for all the motors
        solutionMaker(
          uint8_t dirS1,
          uint8_t stepS1,
          uint8_t dirS2,
          uint8_t stepS2,
          uint8_t dirS3,
          uint8_t stepS3,
          uint8_t dirS4,
          uint8_t stepS4,
          uint8_t enable1,
          uint8_t enable2,
          uint8_t enable3,
          uint8_t enable4,
          uint8_t motor1A,
          uint8_t motor1B,
          uint8_t motor2A,
          uint8_t motor2B,
          uint8_t en1,
          uint8_t en2,
          uint8_t led1,
          uint8_t led2,
          uint8_t led3,
          uint8_t led4,
          uint8_t led5,
          uint8_t led6,
          uint8_t led7,
          uint8_t led8,
          uint8_t tempSens,
          uint8_t lcdButton,
          uint8_t relay1
        );

         // Init the object with default configuration
        void begin(
          uint8_t SolutionServo1=26,
          uint8_t SolutionServo2=28,
          uint8_t steps_per_rev = MOTOR_STEP_PER_REV,
          uint8_t microStep = DEFAULT_MICROSTEP,
          uint8_t pump_velocity = PUMP_VELOCITY,
          bool invertPump = false
        );

        bool dispense(long some_mg, uint8_t st); // Move some stepper to dispense some_mg
        /* Move some revs in any stepper.
        It allows to measure the mg dispense to get the calibration parameter */
        void stepperCalibration(long rev, uint8_t st);
        /* Move some miliseconds any pump.
        It allows to measure the ml dispense to get the calibration parameter */
        bool dispenseAcid(float some_ml, uint8_t pump); // Add some ml of acid with a pump
        /* Turn on a pump.
        It allows to measure the ml dispense to get the calibration parameter */
        void pumpCalibration(float time1, uint8_t pump);
        void setCalibrationParameter(uint8_t param, uint8_t actuator); // Set parameters for motors/pumps
        void setCalibrationParameter1(uint8_t param, uint8_t actuator); // Set parameter for ph/ec equations
        bool isEnable(uint8_t actuator); // Returns true if actuator is enable, else false
        bool isAvailable(uint8_t actuator); // Returns true if actuator is available, else false
        long getMG(uint8_t st); // Returns the mg that were dispense
        void stop(uint8_t st); // Stops some motor/pump
        void notFilter();
        void defaultFilter(); // Set Kalman with Noise = 0.5
        bool setExponentialFilter(float alpha = 0.5);
        bool setKalmanFilter(float noise);
        void printFilter();
        bool EZOisEnable(uint8_t sensorType); // Ask to atlas Scientific Sensor if they are enable
        void EZOcalibration(uint8_t sensorType, uint8_t act, float value);
        void EZOexportCal(uint8_t sensorType); // Run Export Calibration Sequence in Atlas Scientific Sensor
        // Import calibration parameter to Atlas Scientific Sensor
        void EZOimportCalibration(uint8_t sensorType, String parameters);
        void EZOimport(bool start); // If start true (start import), else (stop import)
        void EZOsleep(); // Enter in low power mode the Atlas Scientific Sensor
        void EZOawake(); // Awake the Atlas Scientific Sensors if they are in sleep mode
        bool EZOisSleep(); // Returns __Sleep variable
        // Make all the maths and execute the actions to prepare a solution
        void eventLCD(); // Read Solution Maker Status and print it on the screen
        void run(); // Run all the actuator with conditions
        void prepareSolution(float liters, uint8_t sol, float ph, float ec);
        // Not ready EZO functions
        //void EZOread(uint8_t sensorType) // Takes read for the Atlas Scientific Sensor
        //void EZOreadWithTempCompensation(uint8_t sensorType) // Takes read for the Atlas Scientific Sensor
        // EZOtempCompensation(uint8_t sensorType) // Set a new temperature to adjust new readings
  };

#endif
