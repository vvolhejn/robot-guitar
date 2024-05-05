#!/bin/bash

# exit on error
set -eo pipefail
# cd to script dir
cd "$(dirname "$0")"

SOURCE="./autoguitar/"
DESTINATION="vv-raspberrypi.local:/home/vvolhejn/autoguitar/autoguitar/"

echo "Watching $SOURCE and syncing to $DESTINATION"
fswatch -o $SOURCE | xargs -n1 -I{} rsync -a $SOURCE $DESTINATION
