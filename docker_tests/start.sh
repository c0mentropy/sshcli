#!/bin/sh

service ssh start

echo "flag{this_is_a_sample_flag}" > /flag

tail -f /dev/null
