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


import os
import pickle
import subprocess
import sys
from distutils.spawn import find_executable

from import_file import import_file


class ProtoBuild():
    def __init__(self):
        self.protoc = self.find_protoc()

    def find_protoc(self):
        "Locates protoc executable"

        if 'PROTOC' in os.environ and os.path.exists(os.environ['PROTOC']):
            protoc = os.environ['PROTOC']
        else:
            protoc = find_executable('protoc')

        if protoc is None:
            sys.stderr.write('protoc not found. Is protobuf-compiler installed? \n'
                             'Alternatively, you can point the PROTOC environment variable at a local version.')
            sys.exit(1)

        return protoc

    def run(self, protopath, protofile):
        proto = os.path.join(protopath, protofile)
        sys.stderr.write('Protobuf-compiling ' + proto + '\n')
        subprocess.check_call([self.protoc, '--python_out=./proto/.', proto, "--proto_path=" + str(protopath)])  # --proto_path
        output = os.path.join("proto", protofile.replace('.proto', '_pb2.py'))
        return ["proto", protofile.replace('.proto', '_pb2.py')]


protos = list()
proto_dict = dict()

builder = ProtoBuild()
for path in range(1, len(sys.argv)):
    for dirpath, dirnames, filenames in os.walk(sys.argv[path]):
        for filename in [f for f in filenames if f.endswith(".proto")]:
            current_proto = (builder.run(dirpath, filename))
            proto_python_file = os.path.abspath(os.path.join("proto", current_proto[1]))
            proto_module = import_file(proto_python_file)
            file = os.path.join(dirpath, filename)
            with open(file, 'r') as File:
                lines = File.readlines()
                for line_nr, line in enumerate(lines):
                    if line.startswith("// Message identifier: "):
                        id = int(line.replace("// Message identifier: ", "").rstrip().replace(".", ""))
                        message = lines[line_nr + 1].split(" ")[1]
                        proto_dict[id] = [str(proto_python_file), str(message)]


if not proto_dict.has_key(0):
    sys.stderr.write("ID: 0 --> odcore_data_MessageContainer not found in Protofiles!! Can't continue..")
#print proto_dict
pickle.dump(proto_dict, open("proto_dict.p", "wb"))
