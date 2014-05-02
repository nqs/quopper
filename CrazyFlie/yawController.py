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
Simple example that connects to the first Crazyflie found, ramps up/down
the motors and disconnects.
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


class YawController:
    """Example that connects to a Crazyflie and ramps the motors up/down and
    the disconnects"""
    def __init__(self, link_uri):

        self._runCouner = 0
        self._firstYawFound = False

        # Set Initial values
        self._thrust = 41000
        self._pitch = 0
        self._roll = 0
        self._yawrate = 0

        self._yawSetPoint = 0

        self._rollPid = PID()
        self._rollPid.SetKp(-.1);	        # Proportional Gain
        #self._rollPid.SetKi(-0.5);	        # Integral Gain
        #self._rollPid.SetKd(-0.1);	        # Derivative Gain

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

        # Variable used to keep main loop occupied until disconnect
        self.is_connected = True

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""

        print "Connected to %s" % link_uri
        self._cf.commander.send_setpoint(0, 0, 0, 20000)

        # The definition of the logconfig can be made before connecting
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

        if not self._firstYawFound:
            self._firstYawFound = True
            self._yawSetPoint = stab_yaw
            return

        prevRoll = self._roll
        error = stab_yaw - self._yawSetPoint
        self._roll = self._rollPid.GenOut(error)
        self._cf.commander.send_setpoint(self._roll, self._pitch, self._yawrate, self._thrust)

        print "Error %s Roll %s, Old Roll %s, Stab Yaw = %s" % (error, self._roll, prevRoll, stab_yaw)

        self._runCouner = self._runCouner + 1
        if self._runCouner > 20000:
            print "Exiting"
            self._cf.commander.setpoint(0, 0, 0, 0)
            self._cf.close_link()
            os._exit(1)

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
        self._cf.close_link()
        os._exit(1)

if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    # Scan for Crazyflies and use the first one found
    print "Scanning interfaces for Crazyflies..."
    #available = cflib.crtp.scan_interfaces()
    #print "Crazyflies found:"
    #for i in available:
    #    print i[0]

    default="radio://0/10/250K"
    controller = YawController(default)

    signal.signal(signal.SIGINT, controller.kill)

    #le = YawController(available[0][0])

    #if len(available) > 0:
    #    le = YawController(available[0][0])
    #else:
    #    print "No Crazyflies found, cannot run example"
    while controller.is_connected:
        time.sleep(1)
