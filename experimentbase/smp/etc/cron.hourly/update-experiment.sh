#!/bin/bash

set -x
set -e
echo "RUNNING update-experiment.sh"
source /etc/slice-functions

if [ $UID -eq "0" ] ; then
    su - $SLICENAME -c "$0"
else
    PACKAGE_SLICE=$( get_url_for_file slice-packages/$SLICENAME.tar.gz )
    update /opt/slice $PACKAGE_SLICE
    cp /etc/skel/.bash* /opt/slice/current/
fi
