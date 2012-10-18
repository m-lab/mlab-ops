#!/usr/bin/python

import pprint
#from planetlab.types import *
from planetlab import session
from slices import *
from sites  import *
import sys

def usage():
    print """
    apply.py takes static configurations stored in sites.py and slices.py
        and applies them to the PLC database adding or updating objects, 
        tags, and other values when appropriate.

    Examples:
        ./apply.py --dryrun --syncsite all
                Does everything. Verifies existing sites & slices, creates
                ones that are non-existent.  This will take a very long time
                due to the delays for every RPC call to the PLC api.

        ./apply.py --dryrun --syncsite nuq01
                Creates site, nodes, pcus, and associates slices with 
                these machines.  Pulls definitions from sites.py & slices.py

        ./apply.py --dryrun --syncsite nuq01 --on mlab4.nuq01.measurement-lab.org
                Resync the node configuration for given hostname.

        ./apply.py --dryrun --syncslice all
                Associates *all* slices with all machines and updates any 
                pending slice attributes.  Sites and slices should be defined in 
                sites.py & slices.py
                
        ./apply.py --dryrun --syncslice ooni_probe --skipwhitelist
                Like "--syncslice all" except only applied to the given
                slicename.

        ./apply.py --dryrun --syncslice ooni_probe --on mlab4.nuq01.measurement-lab.org
                Performs the --syncslice operations, but only on the given
                target machine.  This is useful for applying IPv6 address
                updates (or other slice attributes) to only a few machines, instead 
                of all of them.  Some slice attributes may be applied
                globally, despite "--on <hostname>".

                In this example, ooni_probe must be explicitly permitted to
                receive an ipv6 on mlab4.nuq01 in slices.py. 
    Comments:
        It may be preferrable to eliminate sites.py since that really only
        needs to run once.  And, provide more intelligent update functions to
        re-assign nodegroups, assign which hosts are in the ipv6 pool, etc.

        And, keeping slices.py as a concise description of what and how slices
        are deployed to M-Lab.
"""

def main():

    from optparse import OptionParser
    parser = OptionParser()

    parser.set_defaults(syncsite=None, syncslice=None,
                        ondest=None, skipwhitelist=False, skipsliceips=False,
                        site=None, hostname=None, slicename=None, 
                        url=session.API_URL, debug=False, verbose=False, )

    parser.add_option("", "--dryrun", dest="debug", action="store_true",
                        help="Only issues 'Get*' calls to the API.  Commits nothing to the API")
    parser.add_option("", "--verbose", dest="verbose", action="store_true",
                        help="Print all the PLC API calls being made.")

    #parser.add_option("", "--site", dest="site", 
    #                    help="only act on the given site")
    #parser.add_option("", "--hostname", dest="hostname", 
    #                    help="only act on the given hostname")
    #parser.add_option("", "--slicename", dest="slicename", 
    #                    help="only act on the given slicename")

    parser.add_option("", "--on", dest="ondest", 
                        help="only act on the given site")

    parser.add_option("", "--syncsite", dest="syncsite", 
                        help="only sync sites and create nodes, pcus, if needed. (saves time)")
    parser.add_option("", "--syncslice", dest="syncslice", 
                        help="only sync slices and attributes of slices. (saves time)")

    parser.add_option("", "--skipwhitelist", dest="skipwhitelist", action="store_true",
                        help="dont try to white list the given slice. (saves time)")
    parser.add_option("", "--skipsliceips", dest="skipsliceips", action="store_true",
                        help="dont try to assign ips to slice. (saves time)")

    parser.add_option("", "--url", dest="url", 
                        help="PLC url to contact")
    parser.add_option("-6", "--sliceipv6", dest="sliceipv6", action="store_true",
                        help="Enable IPv6 assignment to slices as well as the host machine (if possible)")

    (options, args) = parser.parse_args()
    if len(sys.argv) == 1:
        usage()
        parser.print_help()
        sys.exit(1)

    print "setup plc session"
    session.setup_global_session(options.url, options.debug, options.verbose)

    # always setup the configuration for everything (very fast)
    print "loading slice & site configuration"
    for slice in slice_list:
        for site in site_list:
            for host in site['nodes']:
                h = site['nodes'][host]
                slice.add_node_address(h)

    # begin processing arguments to apply filters, etc
    # three options:
    #   - do only sites, slices, or slice attributes
    #   - do a single site, hostname, or slicename
    #   - do everything

    if ( options.syncsite is not None or 
         options.syncslice is not None ):

        if options.syncsite is not None:
            for site in site_list: 
                # sync everything when syncsite is None, or only when it matches
                if options.syncsite == "all" or options.syncsite == site['name']:
                    print "Syncing: site", site['name']
                    site.sync(options.ondest)

        if options.syncslice:
            print options.syncslice
            for slice in slice_list: 
                if options.syncslice == "all" or options.syncslice == slice['name']:
                    print "Syncing: slice", slice['name']
                    slice.sync(options.ondest, options.skipwhitelist, options.skipsliceips)

    elif ( options.site is not None or
         options.hostname is not None or
         options.slicename is not None ):
        if options.site:
            print "site"
            for site in site_list: 
                if site['name'] == options.site: 
                    print site 
                    site.sync()
            pass

        if options.hostname and not options.slicename:
            print "hostname"
            for site in site_list:
                for host in site['nodes']:
                    h = site['nodes'][host]
                    if options.hostname in h.hostname():
                        print h
                        h.sync()
            pass

        if options.slicename:
            print "slicename", options.slicename
            for slice in slice_list: 
                if slice['name'] == options.slicename:
                    #print slice
                    slice.sync(options.hostname)
            pass

    else:
        print "everything"
        # apply sites, nodes, pcus,
        for x in site_list: print x ; break
        # apply slices, slice attributes, slice-to-node mappings
        #for x in slice_list: print x
        pass

    #print h

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
