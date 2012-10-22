#!/usr/bin/python

import sys
import time
import os
from datetime import datetime,timedelta

## Google Docs keys and id for data-collection pipeline spreadsheet
SPREADSHEET_KEY = '0Aun4Sboak0DhcnRxMXpLX1BDcnNPZjVXQ0hJVHJqb1E'
SPREADSHEET_WORKSHEET_ID = 'od6'

try:
    import gdata.service
    import gdata.service
    from gdata.service import RequestError
    import gdata.spreadsheet
    import gdata.spreadsheet.service
except:
    ## NOTE: download gdata library, install it, restart process
    print "Could not load gdata, trying to install it"
    ret = os.system("ps ax | grep -v grep | grep -q yum")
    if ret != 0:
        ## NOTE: yum is not running.
        os.system("yum install -y python-gdata")
        ## To avoid endless-loops
        if "restarting" not in sys.argv:
            os.execv(sys.argv[0], sys.argv+["restarting"])
    print "failed to load gdata"
    sys.exit(1)

if "restarting" in sys.argv:
    ## This argument is not needed now, remove it.
    i = sys.argv.index("restarting")
    del sys.argv[i]

## DEBUG does not delete anything
DEBUG=False

def double_check_local_time():
    """
        double_check_local_time() --
            To prevent catastrophic deletion of files, perform a santity check
            with at least one other system to establish current time.

            If they agree to within 1 hour, return True
            Else, return False

            This sanity check can be used to exit if clocks are too out-of
            sync.  Better to be conservative than to lose data.
    """

    def ts_is_within(ts1,ts2,diff):
        if abs(ts2-ts1) < diff:
            return True
        print "T1: %s T2: %s Diff: %s > %s" % (ts1, ts2, abs(ts2-ts1), diff)
        return False

    server = "http://ks.measurementlab.net" 
    cmd = "curl --verbose %s 2>&1 | grep Date:" % server
    http_time = os.popen(cmd, 'r').read().strip()
    http_time = http_time[8:]
    # < Date: Wed, 11 Jul 2012 17:01:56 GMT
    dt = datetime.strptime(http_time, '%a, %d %b %Y %H:%M:%S %Z')
    ts_remote = int(time.mktime(dt.timetuple()))
    ts_local = int(time.time())
    return ts_is_within(ts_local,ts_remote,60*60)



## NOTE: last updated 07-12-2012
slicename_to_rsyncpath = {
    'gt_partha' : ['54321/pathload2', '54321/shaperprobe'],
    'iupui_ndt' : ['7999/ndt-data'],
    'iupui_npad' : ['7999/NPAD.v1', '7999/SideStream'],
    'mlab_neubot' : ['7999/neubot'],
    'mpisws_broadband' : ['7999/glasnost'],
}
## NOTE: number of extra days to leave on disk before deleting.
slicename_to_padding = {
    'gt_partha' : 7,
    'iupui_ndt' : 2,
    'iupui_npad' : 7,
    'mlab_neubot' : 7,
    'mpisws_broadband' : 7,
}

## NOTE: these paths are relative to the VM
rsyncpath_to_filesystempath = {
    '54321/pathload2'   : '/home/gt_partha/pathload2',
    '54321/shaperprobe' : '/home/gt_partha/shaperprobe/dropbox',
    '7999/ndt-data'     : '/usr/local/ndt/serverdata',
    '7999/NPAD.v1'      : '/home/iupui_npad/VAR/www/NPAD.v1',
    '7999/SideStream'   : '/home/iupui_npad/VAR/www/SideStream',
    '7999/neubot'       : '/var/lib/neubot',
    '7999/glasnost'     : '/home/mpisws_broadband/glasnost',
}

def get_last_collection_dates_for(fout, slicename):

    # ClientLogin to access spreadsheet
    client = gdata.spreadsheet.service.SpreadsheetsService()  
    spec_feed = client.GetListFeed(SPREADSHEET_KEY, SPREADSHEET_WORKSHEET_ID, 
                    visibility="public", projection="values")

    if slicename not in slicename_to_rsyncpath:
        print >>fout, "%s not in slicename_to_rsyncpath mapping: Code is out of date"
        print >>fout, "Exiting"
        sys.exit(1)

    f_slice = slicename.split("_")
    hostname = os.popen("hostname", 'r').read().strip()

    ret = []
    for row in spec_feed.entry:
        for rsync_path in slicename_to_rsyncpath[slicename]:
            search_pattern = "rsync://%s.%s.%s:%s" % (f_slice[1], f_slice[0], hostname, rsync_path)
            if search_pattern in row.title.text:
                print >>fout, "pattern %s in %s" % (search_pattern, row.title.text) 
                if row.custom['lastsuccessfulcollection'].text is not None:
                    # remove the 'x' prefix
                    date = row.custom['lastsuccessfulcollection'].text[1:]
                    path = rsyncpath_to_filesystempath[rsync_path]
                    path = "/vservers/%s%s" % (slicename, path)
                    print >>fout, "Adding path,last_successful_date : %s,%s" % (path,date)
                    # add the path,date tuple to the return list.
                    ret.append( (path, date) )
    return ret

total_size = 0
total_count = 0

def visit_and_delete(args, dirname, filenames):
    global total_size
    global total_count
    (ts_last_collection,fout) = args
    for filename in filenames:
        full_path = "%s/%s" % (dirname,filename)
        try:
            s = os.stat(full_path)
            # NOT A DIRECTORY
            if s.st_mtime < ts_last_collection and not os.path.isdir(full_path):
                total_size += s.st_size
                total_count += 1
                print >>fout, "safely removing: (%s, %sKB) /%s" % ( total_count, 
                            total_size/1024, "/".join(full_path.split("/")[3:]) )
                if not DEBUG: 
                    os.remove(full_path)
            # IS-A DIRECTORY
            elif s.st_mtime < ts_last_collection and os.path.isdir(full_path):
                print >>fout, "safely removing: (%s, %sKB) /%s" % ( total_count, 
                            total_size/1024, "/".join(full_path.split("/")[3:]) )
                if not DEBUG and len(os.listdir(full_path))==0:
                    print >>fout, "safely removing dir: %s" % full_path
                    os.rmdir(fullpath)

        except Exception, e:
            print >>fout, "error regarding: %s" % e

def parse_args():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", 
                       default=False, 
                       action="store_true", 
                       help="Verbose mode: print extra details.")
    parser.add_option("-p", "--padding", dest="padding", 
                       type="int", 
                       default=-1, 
                       help="Keep data within the last <padding> days, even"+
                            "if it has been collected.")
    parser.add_option("-s", "--slicename", dest="slicename", 
                       default=None,
                       help="Slicename to operate on.")
    parser.add_option("", "--until-nonzero-delete", dest="nonzerodelete", 
                      default=False, action="store_true",
                      help="Reduce padding from default until a non-zero "+
                           "number of files are removed or padding==0 is "+
                           "reached..")
    parser.add_option("", "--dryrun", dest="dryrun", 
                      default=False, action="store_true",
                      help="With this argument, no files are actually deleted.")

    (options, args) = parser.parse_args()
    return (options, args)

def main():
    
    ## TODO: add additional sanity checks.
    #        /vservers , root user, 
    (options, args) = parse_args()

    if options.dryrun:
        global DEBUG
        DEBUG=True

    if not double_check_local_time():
        print "I'm sorry; local time is out of sync with a remote machine."
        print "To prevent data loss, this script will not run without "
        print "external validation of the local clock."
        sys.exit(2)

    log_file = "/var/log/delete_logs_safely.log"
    fout = open(log_file, 'a')
    print "Logging to %s" % log_file
    print "DEBUG mode is %s" % DEBUG

    if options.slicename is None:
        slice_list = slicename_to_rsyncpath.keys()
    else:
        slice_list = [ options.slicename ]

    for slicename in slice_list:
        date_list = get_last_collection_dates_for(fout, slicename)
        if options.padding != -1:
            delta = timedelta(options.padding) # pad with given # of days
        else:
            delta = timedelta(slicename_to_padding[slicename])

        for (path,date) in date_list:
            # NOTE: if nonzerodelete option is enabled, then reduce delta 
            #       by 1 until total_count is > zero 
            #       if nonzerodelete is not enabled, then this will run once.
            # Uncollected data is protected, b/c delta is greater than zero
            while delta >= timedelta(0):
                print "Using padding of '%s' before %s" % (delta, date)
                dt = datetime.strptime(date, '%Y-%m-%d')
                dt = dt-delta
                ts = int(time.mktime(dt.timetuple()))
                print >>fout, "Starting at %s (%s) for %s:%s all before %s" % (
                        time.time(), time.ctime(), slicename, path, dt)
                os.path.walk(path, visit_and_delete, (ts,fout))
                ## Either we have deleted some files, so stop.
                ## Or, the nonzerodelete option is false, so stop,
                ## Or, if total_count==0 & nonzerodelete is true, do not
                ##     continue loop reducing delta.
                if total_count > 0 or not options.nonzerodelete:
                    print >>fout, "Finished at %s (%s) for %s:%s all before %s" % (
                        time.time(), time.ctime(), slicename, path, dt)
                    break;
                delta -= timedelta(1)

    print "Removed: %s, %s KB" % ( total_count, total_size/1024 )

    fout.close()
    ## run resync script to adjust limits after delete
    if not DEBUG:
        print "Running resync_vdlimit.sh.."
        #if len(slice_list) == 1:
        #    os.system("/usr/lib/nagios/plugins/resync_vdlimit.sh %s >> %s 2>&1" % (slice_list[0], log_file))
        #else:
        #    os.system("/usr/lib/nagios/plugins/resync_vdlimit.sh >> %s 2>&1" % log_file)

if __name__ == "__main__":
    main()
