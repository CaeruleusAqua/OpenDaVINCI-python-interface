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

"""This module handles the whole communication with the OpenDaVINCI middleware"""

__license__ = "GNU General Public License"
__docformat__ = 'reStructuredText'

import datetime
import posix_ipc
import signal
import socket
import struct
import sys
import sysv_ipc
import thread

import numpy as np

import opendavinci_pb2


class DVnode:
    """This class handles the whole communication with the OpenDaVINCI middleware

    You can create multiple objects of the class with different cid's (or equal). So you can easily transmit data between two cid spaces.
    """

    def __init__(self, cid, port=12175):
        assert cid <= 255
        self.MCAST_PORT = port
        self.MCAST_GRP = "225.0.0." + str(cid)
        self.run = False
        self.connected = False
        self.callbacks = dict()
        self.imageCallbacks = dict()
        self.containerCallbacks = list()
        self.knownIDs = list()
        self.sock = None

    def connect(self):
        """
        Needs to be called to receive or publish any data.
        """
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

    def publish(self, container):
        """
        Publishes data using OpenDaVINCI, this is the python equivalent to getConference().send(container);


        Parameters
        ----------
        container : opendavinci_pb2.odcore_data_MessageContainer
            container to publish
        """
        data = container.SerializeToString()
        header = self.__get_od_header(len(data))
        tosend = header + data
        self.sock.sendto(tosend, (self.MCAST_GRP, self.MCAST_PORT))

    @staticmethod
    def __get_od_header(size):
        a = struct.pack("<B", *bytearray([0x0D, ]))
        b = struct.pack("<L", ((size & 0xFFFFFF) << 8) | 0xA4)
        return a + b

    def registerCallback(self, msgID, func, msgType, params=()):
        """
        Registers a new Callback function

        Minimum callback function declaration should look like:
            def callback(msg, timeStamps):

        but can also be extended eg:
            def callback(msg, timeStamps, x, y, z):
        in this case x,y,z should be forwarded using the params parameter:
            dvnode.registerCallback(msgID, callback, msgType, params=(x,y,z)):


        Parameters
        ----------
        msgID : int
            Message identifier from the ODVD or Protobuf file.
        func : function
            Callback function to be called
        msgType : google.protobuf.pyext.cpp_message
            Expected message type to given msgID
        params : tuple
            should contain all other parameters which should be forwarded to the callback function
        """
        assert hasattr(func, '__call__')
        self.callbacks[msgID] = (func, msgType, params)

    def registerContainerCallback(self, func):
        """
        Registers a new Callback function, but callback receives container and you have to deserialize the message by yourself,
        usefull if you want to record the data  using the writeToFile function

        Minimum callback function declaration should look like:
            def containerCallback(container)

        Parameters
        ----------
        func : function
            Callback function to be called
        """
        assert hasattr(func, '__call__')
        self.containerCallbacks.append(func)

    def registerImageCallback(self, name, func, params=()):
        """
        Registers a new Callback function, but directly decodes the image message to an numpy array, which can easy used with openCV

        Minimum callback function declaration should look like:
            def imageCallback(image, timeStamps)
        but can also be extended eg:
            def imageCallback(image, timeStamps, x, y, z):
        in this case x,y,z should be forwarded using the params parameter:
            dvnode.registerImageCallback("image_name", callback, params=(x,y,z)):

        Parameters
        ----------
        name : string
            the name of the Video stream to receive
        func : function
            Callback function to be called
        params : tuple
            should contain all other parameters which should be forwarded to the callback function
        """
        assert hasattr(func, '__call__')
        self.imageCallbacks[str(name)] = (func, params)

    @staticmethod
    def writeToFile(container, filename):
        """
        Writes given container to File and automatically add the OpenDaVINCI recording header.
        Repeated call will append the Data to the file. If you want a fresh recording you need to delete the file manually

        Parameters
        ----------
        container : opendavinci_pb2.odcore_data_MessageContainer
           container to write
        filename : string
           file to write into
        """
        buf = container.SerializeToString()
        with open(filename, "ab") as myfile:
            size = len(buf)
            a = struct.pack("<B", *bytearray([0x0D, ]))
            myfile.write(a)
            b = struct.pack("<L", ((size & 0xFFFFFF) << 8) | (0xA4))
            myfile.write(b)
            myfile.write(buf)

    @staticmethod
    def __getCRC32(string):
        retVal = 0

        for char in string:
            retVal = retVal ^ ord(char) ^ 0x04C11DB7  # The CRC32 polynomial.

        return retVal

    def __threadedImageConverter(self, msg, stamps, callback):
        # FIXME: incorporate _POSIX_NAME_MAX if available instead of constant 14, also the fallback to 12 if not defined
        MAX_NAME_LENGTH = 14
        name = str("/" + msg.name.replace("/", "_"))[:MAX_NAME_LENGTH]
        sem = posix_ipc.Semaphore(str(name))
        sm = sysv_ipc.SharedMemory(self.__getCRC32(name))
        sem.acquire()
        try:
            image = sm.read(msg.size + 4)[4:]
        finally:
            sm.detach()
            sem.release()
            sem.close()

        tmp = np.frombuffer(image, np.uint8).reshape(msg.height, msg.width, msg.bytesPerPixel)
        callback[0](tmp, stamps, *callback[1])

    def __spin(self):
        while True:
            try:
                data = self.sock.recv(65507)
                if len(data) > 5:  # LENGTH_OPENDAVINCI_HEADER = 5
                    byte0 = data[0]
                    byte1 = data[1]
                    size = (struct.unpack('<L', data[1:5])[0] >> 8)
                    # Check for OpenDaVINCI header.
                    if ord(byte0) == int('0x0D', 16) and ord(byte1) == int('0xA4', 16):
                        i = 0
                        while len(data) < size + 5:
                            print "Waiting for more udp data, current retry: ", i
                            i += 1
                            data += self.sock.recv(65507)
                        container = opendavinci_pb2.odcore_data_MessageContainer()
                        container.ParseFromString(data[5:])
                        for callback in self.containerCallbacks:
                            thread.start_new_thread(callback, (container,))
                        if container.dataType not in self.knownIDs:
                            self.knownIDs.append(container.dataType)
                        if container.dataType in self.callbacks.keys():
                            msg = self.callbacks[container.dataType][1]()
                            msg.ParseFromString(container.serializedData)
                            send = datetime.datetime.fromtimestamp(timestamp=container.sent.seconds) + datetime.timedelta(
                                    microseconds=container.sent.microseconds)
                            received = datetime.datetime.fromtimestamp(timestamp=container.received.seconds) + datetime.timedelta(
                                    microseconds=container.received.microseconds)
                            timestamps = [send, received]
                            thread.start_new_thread(self.callbacks[container.dataType][0], (msg, timestamps) + (self.callbacks[container.dataType][2]))

                        if container.dataType == 14:
                            msg = opendavinci_pb2.odcore_data_image_SharedImage()
                            msg.ParseFromString(container.serializedData)
                            send = datetime.datetime.fromtimestamp(timestamp=container.sent.seconds) + datetime.timedelta(
                                    microseconds=container.sent.microseconds)
                            received = datetime.datetime.fromtimestamp(timestamp=container.received.seconds) + datetime.timedelta(
                                    microseconds=container.received.microseconds)
                            timestamps = [send, received]
                            if msg.name in self.imageCallbacks.keys():
                                thread.start_new_thread(self.__threadedImageConverter, (msg, timestamps, self.imageCallbacks[msg.name]))
            except:
                print("Unexpected error:", sys.exc_info()[0])

    def getKnownMessageIDs(self):
        """
        returns all yet received message ID's since the program runs
        """
        return self.knownIDs

    @staticmethod
    def spin():
        """
        Causes the program to go into IDLE mode.. but keeps program running. Function is blocking.
        Doesn't needs to be called
        """
        signal.pause()
