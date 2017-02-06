#!/usr/bin/env python3
# Copyright (C) 2016 Julian Scholle
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA


import datetime
import struct
import sys
import time

from DVnode import DVnode
from internal.logger import Logger

if len(sys.argv) < 3:
    Logger.logError("Missing Parameters, minimum number of parameter is 2!")
    Logger.logInfo("Usage: ")
    Logger.logInfo("       $ protoPrint.py CID input.rec [playbackspeed]")
    Logger.logInfo("Set playbackspeed to 0, for unlimited speed")
    Logger.logInfo("")
    sys.exit(-1)

try:
    CID = int(sys.argv[1])
except:
    Logger.logError("CID malformed!")
    Logger.logInfo("Usage: ")
    Logger.logInfo("       $ protoPrint.py 123 input.rec ")
    Logger.logInfo("")
    sys.exit(-1)

speed = 1
if len(sys.argv) > 3:
    try:
        speed = float(sys.argv[3])
    except:
        Logger.logError("Speed malformed!")
        Logger.logInfo("Usage: ")
        Logger.logInfo("       $ protoPrint.py 123 input.rec 1.0")
        Logger.logInfo("")
        sys.exit(-1)

node = DVnode(cid=CID)
node.run = True
node.connect()

lasttimestamp = None
lasttime = datetime.datetime.now()

# Read contents from file.
with open(sys.argv[2], "rb") as f:
    Logger.logInfo("Reading File, please wait..")

    MessageContainer = node.proto_dict[0]
    LENGTH_OPENDAVINCI_HEADER = 5

    header = f.read(LENGTH_OPENDAVINCI_HEADER)
    while len(header) == LENGTH_OPENDAVINCI_HEADER:
        try:
            byte0 = ord(header[0])
            byte1 = ord(header[1])
        except:
            byte0 = header[0]
            byte1 = header[1]

        # Check for OpenDaVINCI header.
        if byte0 == int('0x0D', 16) and byte1 == int('0xA4', 16):
            v = struct.unpack('<L', header[1:5])  # Read uint32_t and convert to little endian.
            expectedBytes = v[0] >> 8  # The second byte belongs to OpenDaVINCI's Container header.

            buffer = f.read(expectedBytes)

            if speed != 0:
                container = MessageContainer()
                container.ParseFromString(buffer)
                if lasttimestamp is None:
                    lasttimestamp = datetime.datetime.fromtimestamp(timestamp=container.sent.seconds) + datetime.timedelta(
                            microseconds=container.sent.microseconds)
                    lasttime = datetime.datetime.now()
                else:
                    newtime = datetime.datetime.fromtimestamp(timestamp=container.sent.seconds) + datetime.timedelta(
                            microseconds=container.sent.microseconds)
                    deltatime = ((newtime - lasttimestamp).total_seconds()) / float(speed)
                    time_to_wait = deltatime - (datetime.datetime.now() - lasttime).total_seconds()
                    if time_to_wait < 0:
                        Logger.logWarn("Can't play at commanded speed!")
                    else:
                        time.sleep(time_to_wait)
                    lasttimestamp = newtime
                    lasttime = datetime.datetime.now()

            node.publish_raw(buffer)

            header = f.read(LENGTH_OPENDAVINCI_HEADER)

        else:
            Logger.logError("Failed to consume OpenDaVINCI container!")
            sys.exit(-1)
