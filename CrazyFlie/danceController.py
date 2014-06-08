# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2014 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.

"""
DANCE DANCE REVOLUTION
"""

import time, sys
import os, signal
from threading import Thread

#FIXME: Has to be launched from within the example folder
sys.path.append("./crazyflie-clients-python/lib")
import cflib
from cflib.crazyflie import Crazyflie

import logging
logging.basicConfig(level=logging.ERROR)

from cflib.crazyflie.log import Log, LogVariable, LogConfig

import datetime

import winsound, sys


class DanceController:
    
    def __init__(self, link_uri):

        # Set Initial values
        # 43000 @ 3700mV
        # 47000 @ 3500mV - not enough
        self._thrust = 10000
        self._rollTrim = 0
        self._pitchTrim = 0
        self._rollThrustFactor = 150
        self._pitchTrustFactor = 250

        self._maxBatteryCounter = 50
        self._batteryCounter = 0
        self._batteryVoltage = 4000     #about full

        """ Initialize and run the example with the specified link_uri """
        print "Connecting to %s" % link_uri

        self._cf = Crazyflie(ro_cache="./crazyflie-clients-python/lib/cflib/cache",
                             rw_cache="./crazyflie-clients-python/lib/cflib/cache")

        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        self.is_connected = False

        self._cf.open_link(link_uri)
        print "Connecting to %s" % link_uri

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""

        print "Connected to %s" % link_uri
        self._cf.commander.send_setpoint(0, self._rollTrim, 0, 29000)
        self._cf.commander.set_client_xmode(False)

        # The definition of the loggconfig can be made before connecting
        self._lg_stab = LogConfig(name="Logger", period_in_ms=10)
        self._lg_stab.add_variable("stabilizer.roll", "float")
        self._lg_stab.add_variable("stabilizer.pitch", "float")
        self._lg_stab.add_variable("stabilizer.yaw", "float")
        self._lg_stab.add_variable("stabilizer.thrust", "uint16_t")
        # self._lg_stab.add_variable("gyro.x", "float")
        # self._lg_stab.add_variable("gyro.y", "float")
        # self._lg_stab.add_variable("gyro.z", "float")
        self._lg_stab.add_variable("pm.vbat", "float")

        # Adding the configuration cannot be done until a Crazyflie is
        # connected, since we need to check that the variables we
        # would like to log are in the TOC.
        self._cf.log.add_config(self._lg_stab)
        if self._lg_stab.valid:
            # This callback will receive the data
            self._lg_stab.data_received_cb.add_callback(self._stab_log_data)

            # This callback will be called on errors
            self._lg_stab.error_cb.add_callback(self._stab_log_error)

            # Start the logging
            self._lg_stab.start()
        else:
            print("Could not add logconfig since some variables are not in TOC")

        # Variable used to keep main loop occupied until disconnect
        self.is_connected = True

        print "Starting dance thread..."
        Thread(target=self.dance).start()


    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print "Error when logging %s: %s" % (logconf.name, msg)

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        #print "[%d][%s]: %s" % (timestamp, logconf.name, data)
        new_dict = {logconf.name:data}
        stab_roll = new_dict['Logger']['stabilizer.roll']
        stab_pitch = new_dict['Logger']['stabilizer.pitch']
        stab_yaw = new_dict['Logger']['stabilizer.yaw']
        # gyro_x = new_dict['Logger']['gyro.x']
        # gyro_y = new_dict['Logger']['gyro.y']
        # gyro_z = new_dict['Logger']['gyro.z']
        battery = new_dict['Logger']['pm.vbat']

        if stab_roll > 99 or stab_pitch > 99:
            print "I'm out of control!!!!!"
            self._cf.commander.send_setpoint(0, 0, 0, 0)
            self._cf.close_link()
            os._exit(1)

        # prevRoll = self._roll
        # self._roll = self._rollPid.GenOut(stab_roll) + self._rollTrim
        # print "Roll %s, Old Roll %s, Stab Roll = %s" % (self._roll, prevRoll, stab_roll)

        # print battery
        self._batteryCounter += 1
        if(self._batteryCounter > self._maxBatteryCounter):
            self._batteryVoltage = battery * 1000
            print self._batteryVoltage
            self._batteryCounter = 0

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the speficied address)"""
        print "Connection to %s failed: %s" % (link_uri, msg)
        self.is_connected = False

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print "Connection to %s lost: %s" % (link_uri, msg)
        self.is_connected = False

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print "Disconnected from %s" % link_uri
        self.is_connected = False

    def kill(self, signal, frame):
        print "Ctrl+C pressed"
        self._cf.commander.send_setpoint(0, 0, 0, 0)
        time.sleep(0.1)
        self._cf.close_link()
        os._exit(1)
        
    def dance(self):
        print "Dance start"

        # start music
        Thread(target=self.play_music).start()

        primary_beat_interval = 1.3

        thrust_increment = 2000
        max_thrust = 54000

        self.adjust_thrust(30000)

        roll = 0
        pitch = 0
        yaw = 0

        self.rev_motors(primary_beat_interval)

        self.lift_off(self._thrust, max_thrust, thrust_increment)

        # hover
        self.adjust_thrust(48000)
        self.hover(roll, yaw, self._thrust, thrust_increment)

        # spin
        self.adjust_thrust(45000)
        magnitude = -90
        spinCounter = 4
        while spinCounter > 0:
            self.spin(magnitude, 1, self._thrust)
            spinCounter -= 1

        # level out
        self.adjust_thrust(48000)

        # turn to give enough space for dart
        # self.spin(magnitude, -1, self._thrust)

        # level out
        self.level_out(self._thrust)

        # dart left
        self.adjust_thrust(38000)
        magnitude = 80
        self.dart(magnitude, 1, self._thrust)

        # level out
        self.adjust_thrust(45000)
        self.level_out(self._thrust)

        # gain altitude and turn
        altitude_counter = 2
        while altitude_counter > 0:
            self.adjust_thrust(max_thrust)
            self.hover(0, 90, self._thrust, thrust_increment)
            altitude_counter -= 1

        # level out
        self.adjust_thrust(44000)
        self.level_out(self._thrust)

        # dart right
        self.adjust_thrust(37000)
        magnitude = 80
        self.dart(magnitude, 1, self._thrust)

        # level out
        self.adjust_thrust(46000)
        self.level_out(self._thrust)

        # spin
        self.adjust_thrust(44000)
        magnitude = 40
        spinCounter = 4
        while spinCounter > 0:
            self.spin(magnitude, 1, self._thrust)
            spinCounter -= 1

        # level out
        self.level_out(self._thrust)

        # spin
        self.adjust_thrust(45000)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, 1, self._thrust)
        self.spin(magnitude, 1, self._thrust)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)

        # level out
        self.level_out(self._thrust)

        # spin up
        magnitude = 40
        self.adjust_thrust(max_thrust)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)

        # spin down
        self.adjust_thrust(42000)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)

        # spin up
        magnitude = 70
        self.adjust_thrust(max_thrust - 4000)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)

        # spin down
        self.adjust_thrust(42000)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)

        # spin up
        magnitude = 100
        self.adjust_thrust(46000)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)

        # spin down
        magnitude = 70
        self.adjust_thrust(42000)
        self.spin(magnitude, -1, self._thrust)
        self.spin(magnitude, -1, self._thrust)

        # land
        self.land(self._thrust, thrust_increment)

        print "End"
        self._cf.commander.send_setpoint(0, 0, 0, 0)

        # make sure the music has time to end
        time.sleep(8.0)

        # Make sure that the last packet leaves before the link is closed
        # since the message queue is not flushed before closing
        time.sleep(0.1)

        self._cf.close_link()
        os.exit(0)

    # dance helper functions
    def adjust_thrust(self, newThrust):
        self._thrust = newThrust
        print self._batteryVoltage
        if(self._batteryVoltage > 4100):
            self._thrust -= 2000
        if(self._batteryVoltage > 4000):
            self._thrust -= 2000
        if(self._batteryVoltage < 3700):
            self._thrust += 1000
        if(self._batteryVoltage < 3600):
            self._thrust += 1000
        if(self._batteryVoltage < 3300):
            self._thrust += 2000
        if(self._batteryVoltage < 3000):
            self._thrust += 2000
        print "ADJUSTED THRUST"
        print self._thrust

    def rev_motors(self, primary_beat_interval):
        revCount = 2
        while revCount > 0:
            self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, 0, 30000)
            # time.sleep(primary_beat_interval)
            time.sleep(0.01)
            self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, 0, 0)

            time.sleep(primary_beat_interval)
            revCount -= 1

    def lift_off(self, thrust, max_thrust, thrust_increment):
        print "lifting off"
        while self._thrust < max_thrust:
            self.adjust_thrust(self._thrust + thrust_increment)
            self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, 0, self._thrust)
            time.sleep(0.1)

    def hover(self, roll, yaw, thrust, thrust_increment):
        print "hovering"
        hoverCount = 4
        while hoverCount > 0:
            thrust -= thrust_increment
            self._cf.commander.send_setpoint(roll + self._rollTrim, -4 + self._pitchTrim, yaw, thrust)
            time.sleep(0.1)

            thrust += thrust_increment
            self._cf.commander.send_setpoint(roll + self._rollTrim, 4 + self._pitchTrim, yaw, thrust)
            time.sleep(0.1)
            hoverCount -= 1

    def dart(self, magnitude, direction, thrust):
        print "darting"
        self._cf.commander.send_setpoint(magnitude*direction, magnitude*direction, 0, thrust)
        time.sleep(0.3)

    def spin(self, magnitude, direction, thrust):
        print "spinning"
        self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, magnitude*direction*4, thrust)
        time.sleep(0.3)
        self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, magnitude*direction*4, thrust)
        time.sleep(0.3)
        self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, 0, thrust)

    def level_out(self, thrust):
        counter = 4
        while counter > 0:
            print "leveling out"
            self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, 0, thrust)
            time.sleep(0.1)
            counter -= 1

    def land(self, thrust, thrust_increment):
        while thrust > thrust_increment:
            print "landing"
            thrust -= thrust_increment
            self._cf.commander.send_setpoint(self._rollTrim, self._pitchTrim, 0, thrust)
            time.sleep(0.1)

    def play_music(self):
        winsound.PlaySound('FlightOfTheBumblebeeEDIT.wav', winsound.SND_FILENAME)

if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    default="radio://0/10/250K"
    controller = DanceController(default)

    signal.signal(signal.SIGINT, controller.kill)

    while controller.is_connected:
        time.sleep(1)
