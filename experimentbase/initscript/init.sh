#!/bin/bash

set -x
set -e
# NOTE: below is replaced by the content of bootstrap-functions 
#       when building this file as an initscript.
#       The initscript then creates this file for others to import.
PREFIX=/etc/mlab
mkdir -p $PREFIX
cat <<\EOFEOF > $PREFIX/bootstrap-functions
ALLFUNCTIONS
EOFEOF
source $PREFIX/bootstrap-functions

function assert_dir () {
    local dir=$1
    /usr/bin/test -d $dir || ( 
            echo "ERROR: No $dir!" && exit 1 )
}

function setup_crond_hourly_update () {
    # link this script to run hourly.
    CRONSCRIPT=/etc/cron.hourly/$( basename $SCRIPT )
    if [ -f $SCRIPT ] && \
       [ ! -e $CRONSCRIPT  ] ; then
        assert_dir "/etc/cron.hourly"
        ln -s $SCRIPT $CRONSCRIPT
    fi
}

function setup_crond () {
    # ENABLE CROND
    /sbin/chkconfig rsyslog on
    l=`pgrep -f rsyslogd | wc -l`
    if [ $l -eq 0 ] ; then
        service rsyslog start 
    fi
    /sbin/chkconfig crond on
    l=`pgrep -f crond | wc -l`
    if [ $l -eq 0 ] ; then
        # START CROND IF IT IS NOT RUNNING
        cat <<EOF > /usr/bin/fakemail.sh
#!/bin/bash
cat >> /var/log/cron.output
EOF
        chmod 755 /usr/bin/fakemail.sh
        cat <<EOF > /etc/logrotate.d/cronoutput
/var/log/cron.output {
    copytruncate
    compress
    monthly
    notifempty
    rotate 5
    missingok
}
EOF
        echo "CRONDARGS='-m /usr/bin/fakemail.sh'" > /etc/sysconfig/crond
        /sbin/service crond start
    fi
}


function update () {
    echo "update"
    if package_is_latest $PACKAGE_MANAGE ; then
        echo "package is latest"
    else 
        echo "package is NOT latest"
        package_setup $PACKAGE_MANAGE
    fi
}

function reset () {
    rm -f /etc/slicename
    rm -f /etc/cron.hourly/bootstrap.sh
    rm -rf $PREFIX
    rm -f /etc/rsyncd.conf
    rm -f /etc/slice-functions
    rm -f /etc/init.d/slicectrl.sh
    rm -f /etc/init.d/slicectrl-functions
}

SCRIPT=$0
COMMAND=$1
SLICENAME=$2

if [ "$COMMAND" = "reset" ]; then
    reset
    exit $?
fi
if [ -z "$COMMAND" ] ; then
    # SET A DEFAULT COMMAND, when started from CRON
    COMMAND=update
fi

sanity_checks
setup_crond
setup_crond_hourly_update
SLICENAME=`cat /etc/slicename`
PACKAGE_MANAGE="http://ks.measurementlab.net/slice-management-package.tar.gz"
PACKAGE_SLICE="http://ks.measurementlab.net/slice-packages/$SLICENAME.tar.gz"

case "$COMMAND" in
    start|update)
        update
        RETVAL=$?
        ;;
    *)
        echo "Usage: $0 {start|update|reset}"
        exit 1
        ;;
esac

RETVAL=$?
exit $RETVAL
