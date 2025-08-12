#!/bin/bash

# Check if exactly three port arguments are passed
if [ $# -ne 3 ]; then
  echo "Usage: sh $0 <host_port_1> <host_port_2> <host_port_3>"
  echo "Example: sh run.sh 8401 8411 8421"
  exit 1
fi

# Read the passed port arguments
HOST_PORT_1=$1
HOST_PORT_2=$2
HOST_PORT_3=$3

# Fixed container ports
CONTAINER_PORT_1=22
CONTAINER_PORT_2=8888
CONTAINER_PORT_3=9999

# Output port mapping information
echo "Mapping host port $HOST_PORT_1 to container port $CONTAINER_PORT_1"
echo "Mapping host port $HOST_PORT_2 to container port $CONTAINER_PORT_2"
echo "Mapping host port $HOST_PORT_3 to container port $CONTAINER_PORT_3"

# Run the Docker container
sudo docker run -itd \
  -p $HOST_PORT_1:$CONTAINER_PORT_1 \
  -p $HOST_PORT_2:$CONTAINER_PORT_2 \
  -p $HOST_PORT_3:$CONTAINER_PORT_3 \
  --rm ubuntu/testssh2:22.04 /start.sh

# Output the container start information
echo "Container started with port mappings: $HOST_PORT_1:$CONTAINER_PORT_1, $HOST_PORT_2:$CONTAINER_PORT_2, $HOST_PORT_3:$CONTAINER_PORT_3"

