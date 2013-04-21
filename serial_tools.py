# Copyright 2013 Guillaume Emont <guij@emont.org>
#
# This file is part of CCLogger
#
# CCLogger is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import platform, os, stat, termios

import serial

def is_serial(file_name):
    file_info = os.stat(file_name)
    if not stat.S_ISCHR(file_info.st_mode):
        return False
    try:
        termios.tcgetattr(file(file_name))
        return True
    except termios.error:
        return False

CC128_PORT_CONFIGURATION = {
    'baudrate': 57600,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE
}

def linux_find_pl2303():
    """
    Return the first serial usb device handled by the pl2303 driver.
    """
    # might be a bit fragile, but works for me
    DRIVER_PATH='/sys/bus/usb-serial/drivers/pl2303'
    
    if os.path.exists(DRIVER_PATH):
        for file_name in os.listdir(DRIVER_PATH):
            dev_path = os.path.join('/dev/', file_name)
            if os.path.exists(dev_path) and is_serial(dev_path):
                return dev_path

    raise RuntimeError("Could not find device, is it plugged in?")

def open_cc128(file_name=None):
    if file_name is None:
        file_name = linux_find_pl2303()
    print "Opening serial port", file_name
    return serial.Serial(port=file_name,
            **CC128_PORT_CONFIGURATION)

if __name__ == '__main__':
    print linux_find_pl2303()
