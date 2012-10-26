#!/bin/bash

set -x 
set -e 
if [ -z "$1" ] ; then
    echo "please provide slice name as only argument"
    exit 1
fi
mkdir -p build
pushd initscript
    sed -e '/ALLFUNCTIONS/ { 
      r bootstrap-functions
      d 
    }' init.sh > ../build/bootstrap.sh
popd
tar -C smp -zcvf build/slice-management-package.tar.gz .
tar -C slice_example -zcvf build/$1.tar.gz .

if [ -n "$2" ] && [ "$2" = "install" ] ; then
    scp -r build/*.tar.gz ks:mlabops/keys/
fi

