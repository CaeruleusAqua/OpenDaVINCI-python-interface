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
import datetime

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
        self.knownIDs = list()
        self.sock = None

    def connect(self):
        assert not self.connected
        # open UDP multicast socect
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.MCAST_PORT))  # use MCAST_GRP instead of '' to listen only / to MCAST_GRP, not all groups on MCAST_PORT
        req = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        self.connected = True
        if not self.run:
            thread.start_new_thread(self.__spin, ())
            self.run = True

    def registerCallback(self, msgID, func, msgType, params=()):
        assert hasattr(func, '__call__')
        self.callbacks[msgID] = (func, msgType, params)

    def registerImageCallback(self, name, func, params=()):
        assert hasattr(func, '__call__')
        self.imageCallbacks[str(name)] = (func, params)

    @staticmethod
    def __getCRC32(string):
        retVal = 0

        for char in string:
            retVal = retVal ^ ord(char) ^ 0x04C11DB7  # The CRC32 polynomial.

        return retVal

    def __threadedImageConverter(self, msg, stapms, callback):
        name = "/" + msg.name.replace("/", "_")
        sem = posix_ipc.Semaphore(name)
        sm = sysv_ipc.SharedMemory(self.__getCRC32(name))
        sem.acquire()
        try:
            image = sm.read(msg.size + 4)[4:]
        finally:
            sm.detach()
            sem.release()
            sem.close()

        tmp = np.frombuffer(image, np.uint8).reshape(msg.height, msg.width, msg.bytesPerPixel)
        callback[0](tmp, stapms, *callback[1])

    def __spin(self):
        data = self.sock.recv(2048)
        while True:
            if len(data) > 5:  # LENGTH_OPENDAVINCI_HEADER = 5
                byte0 = data[0]
                byte1 = data[1]

                # Check for OpenDaVINCI header.
                if ord(byte0) == int('0x0D', 16) and ord(byte1) == int('0xA4', 16):
                    container = comma_pb2.Container()
                    container.ParseFromString(data[5:])
                    if container.dataType not in self.knownIDs:
                        self.knownIDs.append(container.dataType)
                    if container.dataType in self.callbacks.keys():
                        msg = self.callbacks[container.dataType][1]()
                        msg.ParseFromString(container.serializedData)
                        send = datetime.datetime.fromtimestamp(timestamp=container.sent.seconds) + datetime.timedelta(microseconds=container.sent.microseconds)
                        received = datetime.datetime.fromtimestamp(timestamp=container.received.seconds) + datetime.timedelta(microseconds=container.received.microseconds)
                        timestamps = [send, received]
                        thread.start_new_thread(self.callbacks[container.dataType][0], (msg, timestamps) + (self.callbacks[container.dataType][2]))

                    if container.dataType == 14:
                        msg = comma_pb2.SharedImage()
                        msg.ParseFromString(container.serializedData)
                        send = datetime.datetime.fromtimestamp(timestamp=container.sent.seconds) + datetime.timedelta(microseconds=container.sent.microseconds)
                        received = datetime.datetime.fromtimestamp(timestamp=container.received.seconds) + datetime.timedelta(microseconds=container.received.microseconds)
                        timestamps = [send, received]
                        if msg.name in self.imageCallbacks.keys():
                            thread.start_new_thread(self.__threadedImageConverter, (msg, timestamps, self.imageCallbacks[msg.name]))

            data = self.sock.recv(2048)

    def getKnownMessageIDs(self):
        return self.knownIDs

    @staticmethod
    def spin():
        signal.pause()
