
bootstrap.sh is the default PlanetLab initscript for M-Lab slices.

This script is installed in the slice at first creation.  It's purpose is to
setup the local environment to support crond, rsyslog, and download, verify and
install a minimal set of scripts for managing the installation of the actual
slice image.

It installs itself into /etc/cron.hourly to periodically:
    Check if latest slice management package is installed. 
    If not, download & unpack latest SMP.
    If so, do nothing.

TODO: add a random delay within the hour to avoid hitting central all at once.

MP:
    install rsync.cfg
    mkdir for standard dirs
    install slicectrl
    install crontab for "PP update"
    
PP:
    slicectrl start
