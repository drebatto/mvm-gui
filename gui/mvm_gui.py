#!/usr/bin/env python3
'''
Runs the MVM GUI
'''

import sys
import os
import os.path
from PyQt5 import QtCore, QtWidgets

import yaml

from mainwindow import MainWindow
from communication.esp32serial import ESP32Serial
from communication.fake_esp32serial import FakeESP32Serial
from messagebox import MessageBox
from serial.serialutil import SerialException

def start_gui():
    """
    Launch the MVM GUI
    """
    base_dir = os.path.dirname(__file__)
    settings_file = os.path.join(base_dir, 'default_settings.yaml')

    with open(settings_file) as mvm_settings:
        config = yaml.load(mvm_settings, Loader=yaml.FullLoader)
    print('Config:', yaml.dump(config), sep='\n')

    app = QtWidgets.QApplication(sys.argv)

    esp32 = None
    if 'fakeESP32' in sys.argv:
        print('******* Simulating communication with ESP32')
        esp32 = FakeESP32Serial(config)
    else:
        while True:
            try:
                err_msg = "Cannot communicate with port %s" % config['port']
                esp32 = ESP32Serial(config)
                break
            except SerialException as error:
                msg = MessageBox()
                retry = msg.critical("Do you want to retry?",
                                     "Severe hardware communication error",
                                     str(error) + err_msg, "Communication error",
                                     {msg.Retry: lambda: True,
                                      msg.Abort: lambda: sys.exit(-1)})
                if not retry():
                    break

    if esp32 is None:
        exit(-1)

    esp32.set("wdenable", 1)

    watchdog = QtCore.QTimer()
    watchdog.timeout.connect(esp32.set_watchdog)
    watchdog.start(config["wdinterval"] * 1000)

    window = MainWindow(config, esp32)
    window.show()
    app.exec_()
    esp32.set("wdenable", 0)

if __name__ == "__main__":
    start_gui()
