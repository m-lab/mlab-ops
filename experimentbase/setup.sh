#!/bin/bash

set -x 
set -e 
if [ -z "$1" ] ; then
    echo "please provide slice name as only argument"
    exit 1
fi
mkdir build
pushd initscript
    ./build.sh > ../build/bootstrap.sh
popd
tar -C smp -zcvf build/slice-management-package.tar.gz .
tar -C spp -zcvf build/$1.tar.gz .

