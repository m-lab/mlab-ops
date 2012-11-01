#!/bin/bash

set -x 
set -e 
if [ -z "$1" ] ; then
    echo "please provide slice name as only argument"
    exit 1
fi
mkdir -p build

cp initscript/bootstrap-functions build/update-manager.sh
tar -C smp -zcvf build/slice-management-package.tar.gz .
tar -C slice_example -zcvf build/$1.tar.gz bin init 

if [ -n "$2" ] && [ "$2" = "install" ] ; then
    scp build/update-manager.sh mlab4.nuq01:/vservers/mlab_ops/tmp/
    scp -r build/*.tar.gz ks:mlabops/keys/
    ssh ks "cd mlabops/keys; ./setup.sh"
fi

