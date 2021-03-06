/*
Library from Grow software package
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

// sensor.h

#ifndef sensor_h
#define sensor_h

#include <stdlib.h>
#if ARDUINO >= 100
#include <Arduino.h>
#else
#include <WProgram.h>
#include <wiring.h>
#endif

#include <NewPing.h>

#define MAX_ANALOG_SENSOR     5 // Max number of analog sensors
#define MAX_EQUATION_DEGREE   3 // Max degree of equation for calibration
#define MAX_ULTRASONIC        8 // Max number of ultrasonic sensors
#define MAX_DISTANCE          300 // Maximum distance(cm) we want to ping
#define MIN_SECURITY_DISTANCE 10 // Minimum distance(cm) expected
#define MAX_SECURITY_DISTANCE 82 // Maximum distance(cm) expected
//#define PI 3.1416
#define MAX_WATER_SENSOR      3 // Max number of water sensors
#define AIR_STATE             HIGH // Air state = HIGH
#define WATER_STATE           LOW // Water State = LOW

// Class to declarate Analog Sensor and applied different filters
/* Types:
 *      0 - "Nutrition Pressure"
 *      1 - "Tank Pressure"
 *      2 - "Water Pressure"
 *      250 - Undefined
*/
class analogSensor
  { private:
        uint8_t __Pin, __Degree, __Type;
        bool __FirstRead;
        float __A, __B, __C, __Value, __PreValue;

        // Constants for the filters
        uint8_t __Filter;
        float __Alpha, __Noise, __Err;
        // Exponential Filter: __Alpha = smoothing variable
        // Kalman Filter: __Noise = Enviromental Noise, __Err = Error
        static unsigned long __ActualTime; // Time Counter

        float model(float val);
        float filter(float val);
        float exponential_filter(float alpha, float t, float t_1);
        float kalman_filter(float t, float t_1);
        void printModel();
        void printFilter();
        void begin(); // Start sensor
        void read();

    public:
        static uint8_t __TotalSensors;
        // List of pointers to each sensor
        static analogSensor *ptr[MAX_ANALOG_SENSOR];

        analogSensor(uint8_t pin, uint8_t type=250); // Constructor

        bool setModel(
          uint8_t degree,
          float a = 0,
          float b = 0,
          float c = 0
        );
        void notFilter();
        void defaultFilter(); // Set Kalman with Noise = 0.5
        bool setExponentialFilter(float alpha = 0.5);
        bool setKalmanFilter(float noise);
        float getValue();
        float getPreValue();
        static void beginAll();
        static void readAll();
  };

// Class to work with multiples UltraSonic Sensors
/* Model:
 *      0 = Not model return Distance
 *      1 = Cilinder -> __Param = radio
 *      2 = Rectangular Prism -> __Param = Rectangule Area
 * 
 * Types:
 *      0 - "Recirculation Level"
 *      1 - "Solution 1 Level"
 *      2 - "Solution 2 Level"
 *      3 - "Solution 3 Level"
 *      4 - "Solution 4 Level"
 *      5 - "Water Level"
 *      6 - "Solution Maker Level"
 *      250 - Undefined
*/

class UltraSonic
  { private:
        uint8_t __Pin1, __Pin2, __State, __Type;
        bool __FirstRead;
        NewPing *__Sonar;
        int __minDist, __maxDist, __countState;
        float __Distance, __PreDistance;
        static unsigned long __ActualTime; // Time Counter

        // Constant for the model
        uint8_t __Model;
        float __Param, __Height;

        // Constants for the filters
        uint8_t __Filter;
        float __Alpha, __Noise, __Err;
        // Exponential Filter: __Alpha = smoothing variable
        // Kalman Filter: __Noise = Enviromental Noise, __Err = Error

        float model(float val);
        float cilinder(float val);
        float rectangularPrism(float val);
        float filter(float val);
        float exponential_filter(float alpha, float t, float t_1);
        float kalman_filter(float t, float t_1);
        void printModel();
        void printFilter();
        float read(); // Take a measurement
        uint8_t updateState();

    public:
        static uint8_t __TotalSensors;
        static UltraSonic *ptr[MAX_ULTRASONIC]; // List of pointers to each sensor
        // Constructor
        UltraSonic(
          uint8_t pin1,
          uint8_t pin2,
          uint8_t type=250,
          int minDist = MIN_SECURITY_DISTANCE,
          int maxDist = MAX_SECURITY_DISTANCE
        );

        bool setModel(uint8_t model, float param, float height);
        void notFilter();
        void defaultFilter(); // Set Kalman with Noise = 0.5
        bool setExponentialFilter(float alpha = 0.2);
        bool setKalmanFilter(float noise);
        int getMinDist();
        int getMaxDist();
        float getDistance(); // Returns more actual distance measurement
        float getPreDistance(); // Returns previous distance measurement
        float getVolume(); // Returns volumen measure
        float getMinVolume(); // Returns min volumen with the model saved
        float getMaxVolume(); // Returns max volumen with the model saved
        uint8_t getState(); // Returns state (High/Ok/Low)
        bool changeMinDist(int minDist);
        bool changeMaxDist(int maxDist);
        static void readAndPrint(); // Read and Prints the values of the last measurements
        static void begin(); // Starts counter to take readings
        static void readAll(); // Take reading from all the sensors
  };

// Class to declarate Water/Air Sensor
/*  Types:
 *      0 - "Water Irrigation Sensor"
 *      1 - "Water Evacuation Sensor"
 *      250 - Undefined
*/
class waterSensor
  { private:
        uint8_t __Pin, __Type;
        bool __State, __FirstRead;
        int __countState;

        static unsigned long __ActualTime; // Time Counter
        void begin(); // Start sensor
        void read();

    public:
        static uint8_t __TotalSensors;
        // List of pointers to each sensor
        static waterSensor *ptr[MAX_WATER_SENSOR];

        waterSensor(uint8_t pin, uint8_t type=250 ); // Constructor

        bool getState();
        static void beginAll();
        static void readAll();
  };

  #endif
