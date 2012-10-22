#!/usr/bin/env python
""" Python template for a future nagios check_* command. """

import os
import re
import sys
import time
import signal

import os
import stat
import time

import gdata.service
from gdata.service import RequestError
import gdata.spreadsheet
import gdata.spreadsheet.service
from datetime import datetime

SPREADSHEET_USER = ''
SPREADSHEET_PASSWORD = ''
SPREADSHEET_KEY = ''
SPREADSHEET_WORKSHEET_ID = ''

if SPREADSHEET_USER == '' : 
    print "Please set the USERNAME, PASSWORD, KEY, & WORKSHEET_ID"
    sys.exit(2)

FILENAME="/tmp/collection_dates.txt"
FILENAME_COLLECT_LOCK=FILENAME + ".lock"
FILENAME_COLLECT_TEMP=FILENAME + ".tmp"
VERBOSE=False

def custom_check(opt, args):
    """
        custom_check:
            opt is an OptParse return value containing all commandline and
            default values for arguments defined in parse_args().

            Values are referenced via opt.<valuename>  without "<>"
        args:
            a list of extra positional arguments on the command line that were
            not switched (prefixed with "-" or  "--")

        RETURN VALUE:
            A tuple with (return_state, "message")

            return_state should be one of:
                STATE_OK = 0
                STATE_WARNING = 1
                STATE_CRITICAL = 2
                STATE_UNKNOWN = 3
            Message is any string.
    """
    global VERBOSE
    VERBOSE=opt.verbose
    if "measurement-lab.org" in opt.hostname:
        opt.hostname = opt.hostname[:-20]

    #if "measurement-lab.org" in opt.slicename:
    #    opt.slicename = opt.slicename[:-31]

    #if len(opt.slicename.split(".")) > 2:
    #    opt.slicename = ".".join(opt.slicename.split(".")[:2])

    print VERBOSE
    (status, days) = find_days_since_last_success(opt.slicename, opt.hostname)

    if status == "ERROR":
        if days == -1:
            return (STATE_UNKNOWN, "Never successfully collected")
        else:
            if days >= opt.critical:
                return (STATE_CRITICAL, "No collection in %s days" % days)

            if days >= opt.warning:
                return (STATE_WARNING, "No collection in %s days" % days)

            return (STATE_OK, "Last collection within the last %s days" % days)

    if status == "NODATA":
        # even though no data is collected, strictly no error has occurred.
        if days == -1:
            return (STATE_OK, "Collection OK, but no data ever.")
        else:
            return (STATE_OK, "Last collection %s days ago." % days)

    return (STATE_UNKNOWN, "Script error; you should not see this (%s)" % days)


def touch(fname):
    fhandle = open(fname, 'a')
    try:
        os.utime(fname, None)
    finally:
        fhandle.close()

def find_days_since_last_success(slicename, hostname):
    s = None
    try:
        if VERBOSE: print "statting %s" % FILENAME
        s = os.stat(FILENAME)
    except:
        if VERBOSE: print "%s not found" % FILENAME
        s = None
        
    if s is None or s[stat.ST_MTIME] < time.time() - 60*60:
        ## regenerate file
        try:
            ## check if someone else is collecting dates already.
            ## if the lock is there, we'll skip the exception code and 
            ##      just use the file as-is.
            if VERBOSE: print "stat lock %s " % FILENAME_COLLECT_LOCK
            s = os.stat(FILENAME_COLLECT_LOCK)
        except:
            ## if the lock is not there, stat will raise an IOError and we'll
            ##      collect the dates for everyone.
            ## NOTE: there is a race condition, but it's better than nothing.
            try:
                touch(FILENAME_COLLECT_LOCK)
                if VERBOSE: print "collecting dates"
                collect_dates()
            except Exception, e:
                print e
                if VERBOSE: print "error collecting logs"
                os.system("echo '%s error' >> /tmp/collect.log" % time.ctime())
                pass
            if VERBOSE: print "removing lock: %s" % FILENAME_COLLECT_LOCK
            os.remove(FILENAME_COLLECT_LOCK)

    date_list = open(FILENAME, 'r').readlines()
    for date in date_list:
        if re.match("%s" % hostname, date):
            f = date.split()
            try:
                return (f[1], int(f[2]))
            except:
                return (f[1], f[2])

    return ("NOENTRY", -1)

    print s[stat.ST_MTIME]

def is_valid(d):
    return d is not None
def is_error(d):
    return d is not None

def collect_dates():
    """
    lastsuccessfulcollection  (lc) can have two states: 1) a valid date,     2) empty.
    errorssincelastsuccessful (er) also has two states: 1) an error message, 2) empty.

    And four combinations of two:
     a)  lc-valid, er-empty
     b)  lc-valid, er-message
     c)  lc-empty, er-message
     d)  lc-empty, er-empty

    a) is the best case, b/c it means data was collected no problems.
    b) collection was successful once before, and now an error prevents success.
    c) an error has occurred, and maybe the node was never online, 
        so there is no lastsuccessfulcollection date, like with b).
    d) no data was collected and there was no error.  If this is an error,
        it is somewhere else.
    """
    # ClientLogin to access spreadsheet
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.email = SPREADSHEET_USER
    gd_client.password = SPREADSHEET_PASSWORD
    gd_client.source = sys.argv[0]
    gd_client.ProgrammaticLogin()

    spec_feed = gd_client.GetListFeed(SPREADSHEET_KEY,
                                      SPREADSHEET_WORKSHEET_ID)
    def getdate(d):
        if d is None:
            return None
        try:
            return datetime.strptime(d, "x%Y-%m-%d-%H:%M")
        except:
            return datetime.strptime(d, "x%Y-%m-%d")

    output = open(FILENAME_COLLECT_TEMP, 'w')
    for row in spec_feed.entry:
        ## extract "slice.name.mlab.site" from rsync:// url
        ## rsync://broadband.mpisws.mlab1.ams02.measurement-lab.org:7999/glasnost
        fields = row.title.text.split(":")
        url = fields[1][2:-20]
        d_err = row.custom['errorsincelastsuccessful'].text
        d_last_attempt = getdate(row.custom['lastcollectionattempt'].text)
        d_last_success = getdate(row.custom['lastsuccessfulcollection'].text)

        if VERBOSE:
            print ( url, row.custom['lastsuccessfulcollection'].text, 
                   d_last_success, d_err )

        # a)
        if is_valid(d_last_success) and not is_error(d_err):
            # While data was once collected, the last collection returned no
            # data, and there is no error.
            print >>output, url, "NODATA", (d_last_attempt-d_last_success).days
        # b)
        elif is_valid(d_last_success) and is_error(d_err):
            # 
            print >>output, url, "ERROR", (d_last_attempt-d_last_success).days
        # c) 
        elif not is_valid(d_last_success) and is_error(d_err):
            # maybe never collected.
            print >>output, url, "ERROR", -1
        # d)
        else: # if not is_valid(d_last_success) and not is_error(d_err):
            print >>output, url, "NODATA", -1

    output.close()
    ## make the new contents accessible to all.
    os.rename(FILENAME_COLLECT_TEMP, FILENAME)

def parse_args():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", 
                       default=False, 
                       action="store_true", 
                       help="Verbose mode: print extra details.")
    parser.add_option("-t", "--timeout", dest="timeout", 
                       type="int", 
                       default=60, 
                       help="Kill this script after 'timeout' seconds.")

    parser.add_option("-s", "--slicename", dest="slicename", default=None, 
                       help="The slicename to check.")
    parser.add_option("-H", "--hostname", dest="hostname", default=None, 
                       help="The hostname to check.")
    parser.add_option("-w", "--warning", dest="warning", default=3, 
                       help="Days before state is 'WARNING'.")
    parser.add_option("-c", "--critical", dest="critical", default=5, 
                       help="Days before state is 'CRITICAL'.")

    if len(sys.argv) == 0: 
        # len() never == 0.  included as reference for mandatory args.
        parser.print_help()
        sys.exit(1)
        
    (options, args) = parser.parse_args()
    return (options, args)


STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3
STATE_DEPENDENT = 4

state_list = [ STATE_OK, STATE_WARNING, STATE_CRITICAL, 
               STATE_UNKNOWN, STATE_DEPENDENT, ]


class TimeoutException(Exception):
    pass

def init_alarm(timeout):
    def handler(signum, _frame):
        """Raise a TimeoutException when called"""
        raise TimeoutException("signal %d" % signum)
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)

def clear_alarm():
    signal.alarm(0)

def main():
    """ Unless there is a bug here, 
        it is preferable to modify only custom_check()
    """

    (opt, args) = parse_args()
    init_alarm(opt.timeout)

    # defaults
    ret = STATE_UNKNOWN
    timeout_error = 0
    exception_error = 0

    try:
        (ret,msg) = custom_check(opt, args)
        if ret not in state_list:
            raise Exception("Returned wrong state type from custom_check(): should be one of %s" % state_list)

    except TimeoutException:
        timeout_error = 1
    except KeyboardInterrupt:
        sys.exit(STATE_UNKNOWN)
    except Exception, err:
        exception_error = 1
        import traceback
        # this shouldn't happen, so more details won't hurt.
        traceback.print_exc()

    clear_alarm()

    if exception_error > 0 or timeout_error > 0:
        print "UNKNOWN - could not complete check (%s)" % exception_error
        sys.exit(STATE_UNKNOWN)
    elif ret == STATE_CRITICAL:
        print "CRITICAL - %s" % msg
    elif ret == STATE_WARNING:
        print "WARNING - %s" % msg
    elif ret == STATE_UNKNOWN:
        print "UNKNOWN - %s" % msg
    else:
        print "OK - %s" % msg

    sys.exit(ret)

if __name__ == "__main__":
    main()

