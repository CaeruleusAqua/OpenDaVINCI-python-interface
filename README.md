# python-opendavinci
This repository is used for python-opendavinci bindings. OpenDaVINCI (http://www.opendavinci.org) is an open source development architecture for virtual, networked, and cyber-physical system infrastructures. The source code of OpenDaVINCI is available at https://github.com/se-research/OpenDaVINCI


## General Informations
Please note, the the main purpose for the python binding is testing and prototyping.

The bindings does not reach the speed als the original C++ implementation does.
There are also not hard realtime capable. 
If you want to implement some heavy computations, like image processing
or PointCloud computations, I recommend using the C++ interface!

If you wart to implement some general signal processing or logic, like a state machine,
it should be fine to us it!

I tried to integrate meaningful error messages. If something is unclear, please contact me!




## Install Instructions

### Install Docker and prepare OpenDaVINCI Docker image

The following tutorial describes how to install the Python bindings on Ubuntu 16.04.

Install Docker: https://docs.docker.com/engine/installation/linux/ubuntulinux/

Clone the OpenDaVINCI source tree:

    $ git clone https://github.com/se-research/OpenDaVINCI

Go to OpenDaVINCI/docker and build OpenDaVINCI Docker image:

    $ cd OpenDaVINCI/docker

    $ make

Download an example recording file based on the comma.ai dataset (https://github.com/commaai/research): http://www.cse.chalmers.se/~bergerc/example.tar

Extract the archive's content to your home folder "example": $HOME/example

### Install Python libraries and protobuf compiler

Install Python. Python should already been installed by default on Ubuntu 16.04. Otherwise, run:

    $ sudo apt-get install python

Or if you wish using python3:

    $ sudo apt-get install python3

Since apt does not contain all necessary Python libraries we using pip to install dependencies:

    $ sudo pip2 install sysv_ipc posix_ipc opencv-python numpy protobuf import_file
    
    or
    
    $ sudo pip3 install sysv_ipc posix_ipc opencv-python numpy protobuf import_file

Clone the python-opendavinci repository:

    $ git clone https://github.com/CaeruleusAqua/OpenDaVINCI-python-interface

Install protobuf compiler:

    $ sudo apt-get install protobuf-compiler python-protobuf

Go to python-opendavinci and run autogen_proto.py, append paths to protofiles separated by space

    $ cd python-opendavinci

    $ ./autogen_proto.py /opt/od4/share/proto/ /opt/opendlv.core/share/proto/
    
The output should look like this:

    Protobuf-compiling: /opt/od4/share/proto/odvdopendlv.proto
    Protobuf-compiling: /opt/od4/share/proto/odvdcommaai.proto
    Protobuf-compiling: /opt/od4/share/proto/automotivedata.proto
    Protobuf-compiling: /opt/od4/share/proto/opendavinci.proto
    Protobuf-compiling: /opt/opendlv.core/share/proto/odvdfh16truck.proto
    Protobuf-compiling: /opt/opendlv.core/share/proto/odvdtrimble.proto
    Protobuf-compiling: /opt/opendlv.core/share/proto/odvdimu.proto
    Protobuf-compiling: /opt/opendlv.core/share/proto/odvdapplanix.proto
    Protobuf-compiling: /opt/opendlv.core/share/proto/odvdv2v.proto
    Protobuf-compiling: /opt/opendlv.core/share/proto/odvdvehicle.proto
    Protobuf-compiling: /opt/opendlv.core/share/proto/odvdopendlvdatamodel.proto
    
    Succesfully written new database to proto_dict.p!
    100 messages found!

 


## Test the python-opendavinci bindings

In Terminal 1, run odsupercomponent for the software component lifecycle management in OpenDaVINCI:

    $ docker run -ti --rm --net=host /seresearch/opendavinci-ubuntu-16.04-complete /opt/od4/bin/odsupercomponent --cid=111 --verbose=1

In Terminal 2, run the OpenDaVINCI visualization environment odcockpit (the first command grants access to your Xserver):

    $ xhost +

    $ docker run -ti --rm --net=host --ipc=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v $HOME/example:/opt/HOST -w /opt/HOST seresearch/opendavinci-ubuntu-16.04-complete /opt/od4/bin/odcockpit --cid=111 --verbose=1

In the odcockpit window, start plugins LiveFeed, Player, SharedImageViewer. In the Player plugin, load the downloaded recording file that is mapped to /opt/HOST/recorder.rec in the odcockpit Docker container. Then click the "Play" button in the Player plugin. The video will be replayed in SharedImageViewer.

In Terminal 3, go to python-opendavinci and run the Python script:

    $ python showData.py

Then Terminal 3 shall show data dump from the video. Meanwhile, the video will be replayed in a new pop-up "image" window in addition to SharedImageViewer in odcockpit.

![Screenshot](https://github.com/se-research-studies/python-opendavinci/blob/master/pythonBindingTest.jpg)


## Using the python-opendavinci toolkit

I also integrated some may usefull tools.

### odpy-msg

The first tool is called "odpy-msg" and allows to get a lot information over all odvd messages in real time.

The syntax is as follows:

    $ ./odpy-msg.py cid echo|list|hz odvd_id

for example:

    $ ./odpy-msg.py 111 echo 19

    $ geodetic_WGS84:
    $   latitude: 57.7916976772    
    $   longitude: 12.7628630476
    $ geodetic_WGS84:
    $   latitude: 57.7916976772
    $   longitude: 12.7628630477
    $ ..
    
    $ ./odpy-msg.py 111 list

    $ ID: 533   --> 1414 Hz    -->  opendlv_core_sensors_applanix_Grp1Data
    $ ID: 19    --> 1413 Hz    -->  geodetic_WGS84
    $ ID: 27    --> 141 Hz     -->  odcore_data_image_H264Frame
    $ ID: 8     --> 0 Hz       -->  odcore_data_dmcp_ModuleStatistics
    $ ..

    $ ./odpy-msg.py 111 hz 19

    $ Rate: 1303 Hz
    $ Rate: 1197 Hz


### protoPlayer
The protoPlayer is a python implementation of odplayer. This is not yet feature complete. Playing Video and SharedMemory objects is not implemented

The syntax is as follows:

    $ protoPrint.py CID input.rec [playbackspeed]
    
The playbackspeed is optional. Zero means unlimited speed.
You will be warned, if the commanded playbackspeed is to high.


### wgs84
The WGS84 Module is an reimplementation of the original OpenDaVINCI WGS84 Class.
It allows you to convert GPS coordinates to local cartesian ones (like OpenDaVINCI does).
The module should have the same behavior as the C++ version.


## Python-Opendavinci Bindings Notes

### multithreading
The DVnode is running multithreaded. The number of threads is currently limited to 4.
Each of your callbacks will run in one of this four Treads. I don't recommend doing
your computations inside of the callbacks, because this can block the decoding of the odvd messages.
Instead of that you should save your data into a global or class member and do your computation
in the main loop or another thread.

You may also want take care of the thread synchronization mechanisms in Python:

http://effbot.org/zone/thread-synchronization.htm

You will be warned from the program, if the computation time inside of the callbacks is to high!
The message should look like this:

    Warning! Receive buffer full! Decrease Proccessing time or Message send rate!
   
Please also note: The multithreding in python is limited by the GlobalInterpreterLock:

https://wiki.python.org/moin/GlobalInterpreterLock

If somebody needs full multithreading, I will may switch to python multiprocessing, to get rid of this limitation.

