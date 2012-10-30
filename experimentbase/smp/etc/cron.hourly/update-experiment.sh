#!/bin/bash

set -x
set -e
echo "RUNNING update-experiment.sh"
source /etc/slice-functions

if [ $UID -eq "0" ] ; then
    su - $SLICENAME -c "$0"
else
    PACKAGE_SLICE=$( get_url_for_file slice-packages/$SLICENAME.tar.gz )
    PREFIX=/home/$SLICENAME
    update $PACKAGE_SLICE
fi
