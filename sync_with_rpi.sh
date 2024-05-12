#!/bin/bash

# exit on error
set -eo pipefail
# cd to script dir
cd "$(dirname "$0")"

SOURCE="./"
DESTINATION="vv-raspberrypi.local:/home/vvolhejn/autoguitar/"

echo "Watching $SOURCE and syncing to $DESTINATION"
fswatch -o $SOURCE | xargs -n1 -I{} rsync --exclude='/.git' --filter="dir-merge,- .gitignore" -a $SOURCE $DESTINATION
