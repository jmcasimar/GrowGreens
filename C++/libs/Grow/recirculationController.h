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

// recirculationController.h

#ifndef recirculationController_h
#define recirculationController_h

#include <stdlib.h>
#if ARDUINO >= 100
#include <Arduino.h>
#else
#include <WProgram.h>
#include <wiring.h>
#endif

#include <sensor.h>

#define MAX_NUMBER_US_SENSOR 7 // Number of UltraSonic sensors
#define MAX_RECIRCULATION_TANK 5 // Number of tanks/recipients
#define MAX_RECIRCULATION_DESTINATIONS 3 // Number of final tanks/recipients
#define flowSensor1 3 // Define flowSensor pin
#define NUTRITION_KEGS 0
#define WATER_KEGS 1
#define SOLUTION_MAKER 2
#define SOL1 0
#define SOL2 1
#define SOL3 2
#define SOL4 3
#define WATER 4

// Class to control the recirculation of nutrient and water
/* Notes:
 * Solution and valves Definition:
 * Solution 1 = 0
 * Solution 2 = 1
 * Solution 3 = 2
 * Solution 4 = 3
 * Water      = 4
*/
class recirculationController
 {  private:
        /*** States ***/
        bool __InPump, __OutPump, __SolPump; // Water Pumps
        bool __InValve[MAX_RECIRCULATION_TANK];
        bool __OutValve[MAX_RECIRCULATION_TANK];
        bool __ReleaseValve;
        bool __Go[MAX_RECIRCULATION_DESTINATIONS]; // Go(Transfer) Valves
        bool __Fh2o, __FSol; // Valves to fill with water
        bool __FPump; // Fill Pump in municipal line
        bool __Rh2o, __RSol; // Release valve for the kegs

        /*** Aux Variables ***/
        uint8_t __In, __Out; // Solution coming in and coming out
        uint8_t __LastOut; // Solution in current process coming out
        float __VolKnut, __VolKh2o; // Volume in kegs (nutrition/H2O)
        float __VolCnut, __VolCh20; // Aux control to calculate Volume missing (nutrition/H2O/sMaker)
        float __SolLiters; // Aux Control in moveSol()
        float __OutLiters, __ActualLiters; // Aux Control moveOut()
        float __SMLiters; // Aux control when SMaker is getting water from outside
        float __FillNut, __FillH2O; // Aux Control in fillH2O() and fillNut()
        uint8_t __Wait4Fill; // Aux Control when we need get water from municipal line
        float __WaitLiters; // Aux Control to save how much liters we needs from municipal line

        /*** Alert Variables ***/
        bool __alertRecirculation;
        bool __alertFlowSensor, __alertLevelSensor;
        uint8_t __alertPumpIn, __alertPumpOut, __alertSolPump;
        float __CompareInVol, __CompareOutVol, __CompareSolVol, __CompareH2OVol;
        float __CompareLevel[MAX_NUMBER_US_SENSOR];
        unsigned long __AlertTime;

        /*** Sensors ***/
        // Ultrasonic
        UltraSonic *__Level[MAX_NUMBER_US_SENSOR];
        // Flow meter
        float __K; // flowSensor constant
        static volatile long __NumPulses; // count flowSensorpulses
        float __H2OVol; // Water that already enter
        unsigned long __ActualTime;

        static void countPulses(); // Interrupt Caudalimeter
        void getVolume(); // Returns volume since fill proccess starts
        void printAction(float volume, String from, String to, uint8_t level=0);
        void printAction(String act, uint8_t level=0);
        void printAction(String act1, String act2, String act3, String act4, uint8_t level=0);

        void fillH2O(float liters); // Fills the water kegs with water
        void fillSol(float liters); // Fills the solution maker with water

    public:
         recirculationController(); // Constructor

         // Start level switch and assign UltraSonic ptrs
         void begin(
           UltraSonic &level0, // Recirculation tank
           UltraSonic &level1, // Solution 1
           UltraSonic &level2, // Solution 2
           UltraSonic &level3, // Solution 3
           UltraSonic &level4, // Solution 4
           UltraSonic &level5, // Water
           UltraSonic &level6  // Solution Maker
          );

         static void flowSensorBegin();

         bool getInPump(); // Returns In Pump State
         bool getOutPump(); // Returns Out Pump State
         bool getSolPump(); // Returns Out Pump State

         bool getInValve(uint8_t valve); // Returns Valve In State
         bool getOutValve(uint8_t valve); // Returns Valve Out State
         bool getReleaseValve(); // Returns Release Valve State
         bool getGoValve(uint8_t valve); // Returns Valve Go State

         bool getFH2OValve(); // Returns Fill H2O Valve State
         bool getFSolValve(); // Returns Fill Sol Valve State
         bool getFPump(); // Return Fill Pump State

         bool getRH2OValve(); // Returns Release H2O Valve State
         bool getRSolValve(); // Returns Release Sol Valve State
         void releaseKegs(bool nut); // Free the solution into the kegs
         void recirculationController::finishRelease(bool nut); // Close release valve

         bool setIn(uint8_t solution); // Solution coming in
         bool setOut(uint8_t solution); // Solution coming out
         uint8_t getIn(); // Returns actual solution coming in
         uint8_t getOut(); // Returns actual solution coming out
         uint8_t InpumpWorkIn(); // If InPump is working returns the solution, else return 250

         bool addVolKnut(float liters); // Change the volume in nutrition kegs
         bool addVolKh2o(float liters); // Change the volume in H2O kegs
         float getVolKnut(); // Returns actual volume in nutrition kegs
         float getVolKh2o(); // Returns actual volume in H2O kegs
         float getVolCnut(); // Returns control volume in nutrition kegs
         float getVolCh2o(); // Returns control volume in H2O kegs
         void resetVolKnut(); // Set the volume in nutrition kegs in 0
         void resetVolKh2o(); // Set the volume in H2O kegs in 0

         bool moveIn(); // InPump move
         uint8_t moveOut(float liters, uint8_t to_Where); // OutPump move
         bool moveSol(); // SolPump move

         void updateState(); // Update volumes in kegs and volumes missed
         void checkAlert(); // Check to enable/disable an alert
         void run(bool check, bool sensorState);
  };

  #endif
