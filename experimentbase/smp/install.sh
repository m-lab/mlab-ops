#!/bin/bash

echo "HELLO WORLD!"
set -x
set -e

function install_file () {
    src=$1
    dst=$2
    if [ -f $src ] ; then
        cp $src $dst
        return $?
    fi
    return 1
}

source etc/slice-functions
slicename=$( get_slice_name )
if has_private_ip ; then
    port=7999
else
    port=`python -c "print 7999+sum([ ord(c) for c in '$slicename' ])"`
fi
if [ -f etc/rsyncd.conf ] ; then
    sed -e 's/SLICENAME/'$slicename'/g' \
        -e 's/PORT/'$port'/g' etc/rsyncd.conf > /etc/rsyncd.conf
    mkdir -p /var/spool/$slicename
fi
install_file etc/slice-functions /etc/
install_file bin/slice-recreate  /usr/bin/
install_file bin/slice-restart   /usr/bin/
install_file init.d/slicectrl-functions    /etc/init.d/
install_file init.d/slicectrl /etc/init.d

