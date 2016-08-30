# python-opendavinci
This repository is used for python-opendavinci bindings. OpenDaVINCI (http://www.opendavinci.org) is an open source development architecture for virtual, networked, and cyber-physical system infrastructures. The source code of OpenDaVINCI is available at https://github.com/se-research/OpenDaVINCI

The following tutorial describes how to work with data using the Python bindings on Ubuntu 16.04.

### Install Docker and prepare OpenDaVINCI Docker image

1. Install Docker: https://docs.docker.com/engine/installation/linux/ubuntulinux/

2. Clone the OpenDaVINCI source tree:

    $ git clone https://github.com/se-research/OpenDaVINCI

3. Go to OpenDaVINCI/docker and build OpenDaVINCI Docker image:

    $ cd OpenDaVINCI/docker

    $ make

4. Download an example recording file based on the comma.ai dataset (https://github.com/commaai/research): http://www.cse.chalmers.se/~bergerc/example.tar

5. Extract the archive's content to your home folder "example": $HOME/example

### Install Python libraries and protobuf compiler

1. Install Python. Python should already been installed by default on Ubuntu 16.04. Otherwise, run

    $ sudo apt-get install python

2. Install Python libraries:

    $ sudo apt-get install python-numpy python-posix-ipc python-sysv-ipc python-opencv

3. Clone the python-opendavinci repository:

    $ git clone https://github.com/se-research-studies/python-opendavinci

4. Install protobuf compiler:

    $ sudo apt-get install protobuf-compiler python-protobuf

5. Go to python-opendavinci and compile the message definition:

    $ cd python-opendavinci

    $ protoc --python_out=. comma.proto

### Test the python-opendavinci bindings

1. In Terminal 1, run odsupercomponent for the software component lifecycle management in OpenDaVINCI:

    $ docker run -ti --rm --net=host /seresearch/opendavinci-ubuntu-16.04-complete /opt/od4/bin/odsupercomponent --cid=111 --verbose=1

2. In Terminal 2, run the OpenDaVINCI visualization environment odcockpit (the first command grants access to your Xserver):

    $ xhost +

    $ docker run -ti --rm --net=host --ipc=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v $HOME/example:/opt/HOST -w /opt/HOST seresearch/opendavinci-ubuntu-16.04-complete /opt/od4/bin/odcockpit --cid=111 --verbose=1

3. In the odcockpit window, start plugins LiveFeed, Player, SharedImageViewer. In the Player plugin, load the downloaded recording file that is mapped to /opt/HOST/recorder.rec in the odcockpit Docker container. Then click the "Play" button in the Player plugin. The video will be replayed in SharedImageViewer.

4. In Terminal 3, go to python-opendavinci and run the Python script:

    $ python showData.py

Then Terminal 3 shall show data dump from the video. Meanwhile, the video will be replayed in a new pop-up "image" window in addition to SharedImageViewer in odcockpit.

![Screenshot](https://github.com/se-research-studies/python-opendavinci/blob/master/pythonBindingTest.jpg)








