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

from pid import PID

import datetime


class DanceController:
    
    def __init__(self, link_uri):

        # Set Initial values
        # 43000 @ 3700mV
        # 47000 @ 3500mV - not enough
        self._thrust = 29000
        self._roll = 0
        self._rollTrim = 2
        self._pitchSetPoint = 30
        self._yawSetPoint = 0
        self._initialYawSet = False
        self._rollThrustFactor = 150
        self._pitchTrustFactor = 250

        self._rollPid = PID()
        self._rollPid.SetKp(-1.4)           # Proportional Gain
        self._rollPid.SetKi(-0.5)   # Integral Gain
        self._rollPid.SetKd(0)          # Derivative Gain

        """ Initialize and run the example with the specified link_uri """
        print "Connecting to %s" % link_uri

        self._cf = Crazyflie(ro_cache="./crazyflie-clients-python/lib/cflib/cache",
                             rw_cache="./crazyflie-clients-python/lib/cflib/cache")

        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

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
        self._lg_stab.add_variable("gyro.x", "float")
        self._lg_stab.add_variable("gyro.y", "float")
        self._lg_stab.add_variable("gyro.z", "float")

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
        gyro_x = new_dict['Logger']['gyro.x']
        gyro_y = new_dict['Logger']['gyro.y']
        gyro_z = new_dict['Logger']['gyro.z']

        if stab_roll > 15 or stab_pitch > 45:
            print "I'm out of control!!!!!"
            self._cf.commander.send_setpoint(0, 0, 0, 0)
            self._cf.close_link()
            os._exit(1)

        # prevRoll = self._roll
        # self._roll = self._rollPid.GenOut(stab_roll) + self._rollTrim

        # self._cf.commander.send_setpoint(self._roll, self._pitchSetPoint, 0,
                # self._thrust + self._rollThrustFactor * abs(self._roll) + self._pitchTrustFactor * abs(stab_pitch))

        print "Roll %s, Old Roll %s, Stab Roll = %s" % (self._roll, prevRoll, stab_roll)

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

        start_time = datetime.datetime.now()
        print "start time = "
        print start_time

        primary_beat_interval = 0.5

        thrust = 30000
        thrust_increment = 1000
        max_thrust = 60000

        # dance opening - rev motors
        revCount = 4
        while revCount > 0:
            self._cf.commander.send_setpoint(0, 0, 0, 40000)
            time.sleep(primary_beat_interval)

            self._cf.commander.send_setpoint(0, 0, 0, 0)
            time.sleep(primary_beat_interval)

            revCount -= 1
            print "rev motors"
            print revCount

        # lift off
        while thrust < max_thrust:
            thrust += thrust_increment
            print "thrust = "
            print thrust

            self._cf.commander.send_setpoint(0, 0, 0, thrust)
            time.sleep(0.1)

        # hover
        thrust = 50000
        hoverCount = 4
        while hoverCount > 0:
            thrust -= thrust_increment
            self._cf.commander.send_setpoint(0, -4, 0, thrust)
            time.sleep(0.1)

            thrust += thrust_increment
            self._cf.commander.send_setpoint(0, 4, 0, thrust)
            time.sleep(0.1)

        print "End"
        self._cf.commander.send_setpoint(0, 0, 0, 0)

        # Make sure that the last packet leaves before the link is closed
        # since the message queue is not flushed before closing
        time.sleep(0.1)

        self._cf.close_link()
        os.exit(0)

if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    default="radio://0/10/250K"
    controller = DanceController(default)

    signal.signal(signal.SIGINT, controller.kill)

    while controller.is_connected:
        time.sleep(1)
