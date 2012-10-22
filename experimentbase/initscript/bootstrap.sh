#!/bin/bash

set -x
set -e

# SETUP FUNCTIONS
function assert_dir () {
    dir=$1
    /usr/bin/test -d $dir || ( 
            echo "ERROR: No $dir!" && exit 1 )
}

function sanity_checks () {

    # SANITY CHECKS AND ENVIRONMENT SETUP
    # check for root user
    if [ $UID -ne "0" ] ;
    then
       echo "You must run this program with root permissions..."
       exit 1
    fi

    # check that slice name is given or saved.
    if [ -z "$SLICENAME" ] && [ ! -f /etc/slicename ] ; then
        echo "Please pass the slicename as the second argument"
        exit 1
    fi

    # if it's given then save it.
    if [ -n "$SLICENAME" ] ; then
        # SAVE SLICENAME
        echo $SLICENAME > /etc/slicename
    fi
}

function setup_crond () {
    # ENABLE CROND
    /sbin/chkconfig crond on
    l=`pgrep crond | wc -l`
    if [ $l -eq 0 ] ; then
        # START CROND IF IT IS NOT RUNNING
        /sbin/service crond start
    fi

    # copy this script to run hourly.
    if [ -f $SCRIPT ] && [ ! -f /etc/cron.hourly/$( basename $SCRIPT ) ] ; then
        assert_dir "/etc/cron.hourly"
        /bin/cp $SCRIPT /etc/cron.hourly/
    fi
}

function get_package_and_verify () {
    # filename for the publickey we will use to verify the stage2 initscript
    PUBKEY_FN=`mktemp /tmp/publickey.XXXXXXXXXX`

    # filename for the extract stage2 initscript
    STAGE2_FN=`mktemp /tmp/stage2-initscript.XXXXXXXXXX`

    # URL for the stage2 initscript
    STAGE2_URL="$1"
    STAGE2_FILE=$( basename $STAGE2_URL )

    # filename and URL for the signature of the stage2 initscript
    STAGE2_SIGNATURE_FN=$STAGE2_FN.sig
    STAGE2_SIGNATURE_URL=$STAGE2_URL.sig

    # create the public key file
    cat <<EOF > $PUBKEY_FN
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDhB8rNF0EH9DfjMw2mDGTYur/N
MmaQaiXICDaxlL1MppY9B6GFQVDbthrqM9HjBUUyDUnQ1jrOjE0II7QKeSc5Gqys
8e8S92stMzdSvtcogfhJcYElq9pCXLbzxI7xzRRoK1zEuKPz3Op5wDjUj1x8/x02
LfnWuuFYf4U5JCRoRwIDAQAB
-----END PUBLIC KEY-----
EOF

    DELAY=1
    RETRY=1

    while [ $RETRY -eq 1 ]; do
       # break out of loop by default
       RETRY=0

       # download the stage2 initscript
       wget $STAGE2_URL -O $STAGE2_FN
       if [ ! -f $STAGE2_FN -o $? -ne 0 ]
       then
          echo "Failed to download $STAGE2_URL"
          RETRY=1
       fi

       # download the signature
       if [ $RETRY -eq 0 ]; then
          wget $STAGE2_SIGNATURE_URL -O $STAGE2_SIGNATURE_FN
          if [ ! -f $STAGE2_SIGNATURE_FN -o $? -ne 0 ]
          then
             echo "Failed to download $STAGE2_SIGNATURE_URL"
             RETRY=1
          fi
       fi

       # make sure the signature is correct
       if [ $RETRY -eq 0 ]; then
          # verify the signature
          RESULT=`openssl dgst -sha256 -signature $STAGE2_SIGNATURE_FN -verify $PUBKEY_FN $STAGE2_FN`
          echo "Signature Verification: $RESULT"
          if [ "$RESULT" != "Verified OK" ]; then
             echo "OpenSSL failed to verify $STAGE2_SIGNATURE_FN"
             RETRY=1
          fi
       fi

       # if something went wrong, then retry. This covers connection errors as
       # well as problems with the stork repository itself. If the repository is
       # offline, then the script will keep retrying until it comes online.
       if [ $RETRY -eq 1 ]; then
          echo "Delaying $DELAY seconds"
          sleep $DELAY
          # exponential backoff, where the sum of all times are less than 1 hour 
          # before exiting.
          DELAY=$(( $DELAY * 2 ))
          if [ $DELAY -gt 1024 ]; then
             # ERROR
             rm -f $PUBKEY_FN
             rm -f $STAGE2_FN
             rm -f $STAGE2_SIGNATURE_FN
             rm -f $STAGE2_SIGNATURE_URL
             return 1
          fi
       fi
    done

    echo "GOT STAGE2!"
    # NOTE: rename tmp file to proper filename
    cp $STAGE2_FN /tmp/$STAGE2_FILE 
}

function start () {
    FILENAME=$( basename $PACKAGE_MANAGE )
    get_package_and_verify $PACKAGE_MANAGE
    RETVAL=$?
    if [ $RETVAL -eq 0 ] ; then
        # TODO: unpack $FILENAME
    fi
}

function reset () {
    rm -f /etc/slicename
    rm -f /etc/cron.hourly/bootstrap.sh
}

SCRIPT=$0
COMMAND=$1
SLICENAME=$2

if [ $COMMAND != "reset" ]; then
    sanity_checks
    setup_crond
    SLICENAME=`cat /etc/slicename`
else
    SLICENAME="blah"
fi

PACKAGE_MANAGE="http://ks.measurementlab.net/slice-management-package.tar.gz"
PACKAGE_SLICE="http://ks.measurementlab.net/slice-packages/$SLICENAME.tar.gz"

if [ -z "$COMMAND" ] ; then
    # SET A DEFAULT COMMAND, when started from CRON
    COMMAND=start
fi

case "$COMMAND" in
    start)
        start
        RETVAL=$?
        ;;
    reset)
        reset 
        RETVAL=$?
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

RETVAL=$?
exit $RETVAL
