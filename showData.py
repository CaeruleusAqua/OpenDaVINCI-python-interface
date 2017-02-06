#!/usr/bin/env python3
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

import cv2
import DVnode


def testCallback(msg, timeStamps):
    print(timeStamps[0])
    print("")
    print(msg)
    print("")
    print(node.getKnownMessageIDs())
    print("")


def testImageCallback(image, timeStamps):
    cv2.imshow('image', image)
    cv2.waitKey(1)


node = DVnode.DVnode(cid=111)
print(node.proto_dict.keys())
node.registerCallback(8, testCallback)
node.connect()
node.spin()
