# OpenDaVINCI - Portable middleware for distributed components.
# Copyright (C) 2016  Julian-B. Scholle
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import numpy as np
import posix_ipc
import signal
import socket
import struct
import sysv_ipc
import thread
import cv2

import comma_pb2


class DVnode:
    def __init__(self, cid, port=12175):
        assert cid <= 255
        self.MCAST_PORT = port
        self.MCAST_GRP = "225.0.0." + str(cid)
        self.run = False
        self.connected = False
        self.callbacks = dict()
        self.imageCallbacks = dict()

    def connect(self):
        assert not self.connected
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.MCAST_PORT))  # use MCAST_GRP instead of '' to listen only / to MCAST_GRP, not all groups on MCAST_PORT
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.connected = True
        if not self.run:
            thread.start_new_thread(self.__spin__, ())
            self.run = True

    def registerCallback(self, id, func, msgType, params=()):
        assert hasattr(func, '__call__')
        self.callbacks[id] = (func, msgType, params)

    def registerImageCallback(self, name, func, params=()):
        assert hasattr(func, '__call__')
        self.imageCallbacks[name] = (func, params)

    def getCRC32(self, string):
        # The CRC32 polynomial.
        CRC32POLYNOMIAL = 0x04C11DB7

        retVal = 0

        for char in string:
            retVal = retVal ^ ord(char) ^ CRC32POLYNOMIAL

        return retVal

    # to prof
    def __threaded_deserialize__(self):
        pass

    def __threaded_imageConverter__(self, msg, stapms, callback):
        name = "/" + msg.name.replace("/", "_")
        sem = posix_ipc.Semaphore(name)
        sm = sysv_ipc.SharedMemory(self.getCRC32(name))
        sem.acquire()
        try:
            image = sm.read(msg.size+4)[4:]
        finally:
            sm.detach()
            sem.release()
            sem.close()

        tmp = np.frombuffer(image, np.uint8).reshape(msg.height, msg.width, msg.bytesPerPixel)
        callback[0](tmp, stapms, *callback[1])

    def __spin__(self):
        LENGTH_OPENDAVINCI_HEADER = 5

        data = self.sock.recv(2048)

        while True:
            if len(data) > LENGTH_OPENDAVINCI_HEADER:
                byte0 = data[0]
                byte1 = data[1]

                # Check for OpenDaVINCI header.
                if ord(byte0) == int('0x0D', 16) and ord(byte1) == int('0xA4', 16):
                    container = comma_pb2.Container()
                    container.ParseFromString(data[5:])
                    type = container.dataType
                    if type in self.callbacks.keys():
                        msg = self.callbacks[type][1]()
                        msg.ParseFromString(container.serializedData)
                        TimeStamps = [container.sent, container.received]
                        thread.start_new_thread(self.callbacks[type][0], (msg, TimeStamps).__add__(self.callbacks[type][2]))

                    if type == 14:
                        msg = comma_pb2.SharedImage()
                        msg.ParseFromString(container.serializedData)
                        TimeStamps = [container.sent, container.received]
                        if msg.name in self.imageCallbacks.keys():
                            thread.start_new_thread(self.__threaded_imageConverter__, (msg, TimeStamps, self.imageCallbacks[msg.name]))

            data = self.sock.recv(2048)

    def spin(self):
        signal.pause()
