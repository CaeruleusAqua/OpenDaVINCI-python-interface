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

import sys
from threading import Lock
from time import sleep

import DVnode

if len(sys.argv) < 3:
    print("\033[1;31;40mError: Missing Parameters, minimum number of parameter is 1 \033[0;37;40m")
    print("Usage: ")
    print("       $ odpy-msg.py cid [echo|list]")
    print("")
    sys.exit(-1)
try:
    cid = int(sys.argv[1])
except:
    print("\033[1;31;40mError: CID malformed..\033[0;37;40m")
    sys.exit(-1)


def printMessage(msg, id):
    printout = (str(msg.DESCRIPTOR.full_name) + ":" + "\n")
    lines = str(msg).splitlines()
    for line in lines:
        printout += ("  " + line + "\n")
    printout += ("")
    print(printout)


def echoContainer(container):
    msg = node.getMessagte(container)
    if msg is not None:
        printMessage(msg, container.dataType)


def echo(msg, timeStamps, msg_id):
    printMessage(msg, msg_id)


hz_counter = 0
hz_lock = Lock()


def hzCallback(msg, timeStamps):
    global hz_lock, hz_counter
    hz_lock.acquire()
    hz_counter += 1
    hz_lock.release()


hz_dict = dict()
def hzContainerCallback(container):
    global hz_lock, hz_dict

    if container.dataType in hz_dict.keys():
        hz_lock.acquire()
        hz_dict[container.dataType] += 1
        hz_lock.release()
    else:
        hz_lock.acquire()
        hz_dict[container.dataType] = 1
        hz_lock.release()



node = DVnode.DVnode(cid=cid)

if sys.argv[2] == "echo":
    if len(sys.argv) == 3:
        node.non_threaded = True
        node.registerContainerCallback(echoContainer)
    else:
        msg_ids = map(int, sys.argv[3].split(','))
        for msg_id in msg_ids:
            node.registerCallback(msg_id, echo, (msg_id,))

    node.connect()
    node.spin()

elif sys.argv[2] == "list":
    node.registerContainerCallback(hzContainerCallback)
    node.connect()
    while True:
        print("Currently known messages:")
        messages = node.getKnownMessageIDs()
        for msg in messages:
            hz_lock.acquire()
            if msg in hz_dict.keys():
                print("ID: " + str(msg) + "\t  --> " + str(hz_dict[msg]) + " Hz\t -->  " + str(node.getMessageName(msg)))
                hz_dict[msg]=0
            else:
                print("ID: " + str(msg) + "\t  --> " + str(0) + " Hz\t -->  " + str(node.getMessageName(msg)))
            hz_lock.release()
        print("")
        sleep(1)

elif sys.argv[2] == "hz":
    node.registerCallback(int(sys.argv[3]),hzCallback)
    node.connect()
    while True:
        sleep(1)
        hz_lock.acquire()
        rate = hz_counter
        hz_counter = 0
        hz_lock.release()
        print("Rate: " + str(rate) + " Hz")
