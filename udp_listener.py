#!/usr/bin/env python2
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
import socket
import struct
import sysv_ipc

import cv2

import comma_pb2

MCAST_GRP = "225.0.0.33"
MCAST_PORT = 12175

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))  # use MCAST_GRP instead of '' to listen only / to MCAST_GRP, not all groups on MCAST_PORT
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


def getCRC32(string):
    # The CRC32 polynomial.
    CRC32POLYNOMIAL = 0x04C11DB7

    retVal = 0

    for char in string:
        retVal = retVal ^ ord(char) ^ CRC32POLYNOMIAL

    return retVal


# Print Container's payload.
def extractAndPrintPayload(identifier, p):
    if identifier == 14:
        print "SharedImage"
        msg = comma_pb2.SharedImage()
        msg.ParseFromString(p)
        print "Payload: " + str(msg)

        sem = posix_ipc.Semaphore("/cam0")
        sm = sysv_ipc.SharedMemory(getCRC32("/cam0"))
        image = None
        sem.acquire()
        try:
            image = sm.read(msg.size)
            sm.detach()
        finally:
            sem.release()
            sem.close()

        nparr = np.fromstring(image, np.uint8).reshape(160, 320, 3)
        tmp = nparr.copy()
        nparr[:, :, 0] = tmp[:, :, 1]
        nparr[:, :, 1] = tmp[:, :, 2]
        nparr[:, :, 2] = tmp[:, :, 0]
        #nparr = cv2.cvtColor(nparr, cv2.cv.CV_GBR2RGB)
        #cv2.imshow('image', nparr)
        #cv2.waitKey(1)


        if identifier == 400:
            msg = comma_pb2.HDF()
            msg.ParseFromString(p)
            print "Payload: " + str(msg)

        if identifier == 27:
            msg = comma_pb2.H264Frame()
            msg.ParseFromString(p)
            print "Payload: " + str(msg)


# Print Container's content.
def printContainer(c):
    # print "Container ID = " + str(c.dataType)
    # print "Container sent = " + str(c.sent)
    # print "Container received = " + str(c.received)
    extractAndPrintPayload(c.dataType, c.serializedData)


# Main.
containers = []

print "Reading File, please wait.."

buf = ""
bytesRead = 0
expectedBytes = 0
LENGTH_OPENDAVINCI_HEADER = 5
consumedOpenDaVINCIContainerHeader = False

data = sock.recv(2048)

while True:
    if len(data) > LENGTH_OPENDAVINCI_HEADER:
        byte0 = data[0]
        byte1 = data[1]

        # Check for OpenDaVINCI header.
        if ord(byte0) == int('0x0D', 16) and ord(byte1) == int('0xA4', 16):
            v = struct.unpack('<L', data[1:5])  # Read uint32_t and convert to little endian.
            expectedBytes = v[0] >> 8  # The second byte belongs to OpenDaVINCI's Container header.
            #           buf = ""  # Reset buffer as we will read now the actual serialized data from Protobuf.

            container = comma_pb2.Container()
            container.ParseFromString(data[5:])
            printContainer(container)

    data = sock.recv(2048)
