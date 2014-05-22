import time, sys
import os, signal
from threading import Thread
import os.path as _path

#FIXME: Has to be launched from within the example folder
sys.path.append("./crazyflie-clients-python/lib")
import cflib
from cflib.crazyflie import Crazyflie

import logging
logging.basicConfig(level=logging.ERROR)

from cflib.crazyflie.log import Log, LogVariable, LogConfig

from pid import PID

class JoystickController:
    """Example that connects to a Crazyflie and ramps the motors up/down and
    the disconnects"""
    def __init__(self, link_uri):
        self._reconnectThreadStarted = False
        self._connect(link_uri)

    def _connect(self, link_uri):

        from cfclient.utils.input import JoystickReader
        from cfclient.utils.config import Config

        self._link_uri = link_uri

        self._jr = JoystickReader(do_device_discovery=False)

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
        self.is_connected = True

        self.setup_controller("xbox360_mode - rachel")

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

        self._jr.input_updated.add_callback(self._cf.commander.send_setpoint)

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

        if stab_roll > 15 or stab_roll > 15:
            print "I'm out of control!!!!!"
            self._cf.commander.setpoint(0, 0, 0, 0)
            #self._cf.close_link()
            os._exit(1)

        #self._cf.commander.send_setpoint(self._roll, self._pitch, self._yawrate, self._thrust)

        #print "Pitch %s, Old Pitch %s, Stab Pitch = %s" % (self._pitch, prevPitch, stab_pitch)
        #print "Roll %s, Old Roll %s, Stab Roll = %s" % (self._roll, prevRoll, stab_roll)
        #print "Yaw %s, Old Yaw %s, Stab Yaw = %s" % (self._yawrate, prevYawRate, stab_yaw)

    def _connection_failed(self, link_uri, msg):
        self._jr.stop_input()
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the speficied address)"""
        print "Connection to %s failed: %s" % (link_uri, msg)
        self.is_connected = False

        if not self._reconnectThreadStarted:
            Thread(target=self._reconnect).start()

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print "Connection to %s lost: %s" % (link_uri, msg)
        self.is_connected = False

        if not self._reconnectThreadStarted:
            Thread(target=self._reconnect).start()

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print "Disconnected from %s" % link_uri
        self.is_connected = False

        if not self._reconnectThreadStarted:
            Thread(target=self._reconnect).start()

    def _reconnect(self):
        self._reconnectThreadStarted = True
        time.sleep(0.1)
        print "Reconnecting"
        #self._connect(self._link_uri)
        self._reconnectThreadStarted = False
        if not self.is_connected:
            self._cf.open_link(self._link_uri)


    def setup_controller(self, input_config, input_device=0, xmode=False):
        """Set up the device reader""" 
        # Set up the joystick reader
        self._jr.device_error.add_callback(self._input_dev_error)
        print "Client side X-mode: %s" % xmode
        if (xmode):
            self._cf.commander.set_client_xmode(xmode)

        devs = self._jr.getAvailableDevices()
        print "Will use [%s] for input" % devs[input_device]["name"]
        self._jr.start_input(devs[input_device]["name"],
                             input_config)

    def controller_connected(self):
        """ Return True if a controller is connected"""
        return True if (len(self._jr.getAvailableDevices()) > 0) else False

    def list_controllers(self):
        """List the available controllers"""
        for dev in self._jr.getAvailableDevices():
            print "Controller #{}: {}".format(dev["id"], dev["name"])

    def _input_dev_error(self, message):
        """Callback for an input device error"""
        print "Error when reading device: {}".format(message)
        sys.exit(-1)

    def kill(self, signal, frame):
        print "Ctrl+C pressed"
        self._cf.commander.send_setpoint(0, 0, 0, 0)
        #self._cf.close_link()
        os._exit(1)

if __name__ == '__main__':

    # Sets the config path
    sys.path[1] = _path.join(sys.path[0], "conf")
    sys.path[0] = _path.join(sys.path[0], "crazyflie-clients-python", "lib")

    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    default="radio://0/10/250K"
    controller = JoystickController(default)

    signal.signal(signal.SIGINT, controller.kill)

    while True:
        time.sleep(1000)
