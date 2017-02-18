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


import json
import os
import subprocess
import sys
from distutils.spawn import find_executable

from import_file import import_file

from internal.logger import Logger

# prints whether python is version 3 or not
Logger.logInfo("OpenDaVINCI running under Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor))

script_path = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) < 2:
    Logger.logError("Missing Parameters, minimum number of parameter is 2!")
    Logger.logInfo("Usage: ")
    Logger.logInfo("       $ autogen_proto.py protofolder1 protofolder2")
    Logger.logInfo("")
    Logger.logInfo("One of the protofiles must contain the odcore_data_MessageContainer message, if not the process will fail!", color=Logger.YELLOW)
    Logger.logInfo("")
    sys.exit(-1)


class ProtoBuild():
    def __init__(self):
        self.protoc = self.find_protoc()

    def find_protoc(self):
        """Locates protoc executable"""

        if 'PROTOC' in os.environ and os.path.exists(os.environ['PROTOC']):
            protoc = os.environ['PROTOC']
        else:
            protoc = find_executable('protoc')

        if protoc is None:
            Logger.logError('protoc not found. Is protobuf-compiler installed? \n'
                            'Alternatively, you can set the PROTOC environment variable to a local version.')
            sys.exit(1)
        return protoc

    def run(self, protopath, protofile):
        script_path = os.path.dirname(os.path.abspath(__file__))
        proto = os.path.join(protopath, protofile)
        Logger.logInfo('Protobuf-compiling: ' + proto)
        subprocess.check_call([self.protoc, str('--python_out=' + script_path + '/proto/.'), proto, "--proto_path=" + str(protopath)])  # --proto_path
        return [os.path.join(script_path, "proto"), protofile.replace('.proto', '_pb2.py')]


protos = list()
proto_dict = dict()

builder = ProtoBuild()
for path in range(1, len(sys.argv)):
    for dirpath, dirnames, filenames in os.walk(sys.argv[path]):
        for filename in [f for f in filenames if f.endswith(".proto")]:
            current_proto = (builder.run(dirpath, filename))
            proto_python_file = os.path.abspath(os.path.join(current_proto[0], current_proto[1]))
            proto_module = import_file(proto_python_file)
            file = os.path.join(dirpath, filename)
            with open(file, 'r') as File:
                lines = File.readlines()
                for line_nr, line in enumerate(lines):
                    if line.startswith("// Message identifier: "):
                        id = int(line.replace("// Message identifier: ", "").rstrip().replace(".", ""))
                        message = lines[line_nr + 1].split(" ")[1]
                        proto_dict[id] = [str(proto_python_file), str(message)]

if not 0 in proto_dict.keys():
    Logger.logError("ID: 0 --> odcore_data_MessageContainer not found in Protofiles!! Can't continue..")
    sys.exit(-1)

python_version = sys.version_info.major

with open(os.path.join(script_path, "proto_dict.json"), 'w') as fp:
    json.dump(proto_dict, fp, sort_keys=True, indent=2)
Logger.logInfo('')
Logger.logInfo('Succesfully written new database to proto_dict.json!', color=Logger.GREEN)

Logger.logInfo(str(len(proto_dict.keys())) + " messages found!", color=Logger.GREEN)
