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

    
"""

def main():

    from optparse import OptionParser
    parser = OptionParser()

    parser.set_defaults(sitesonly=None, slicesonly=None, sliceattrsonly=None,
                        site=None, hostname=None, slicename=None,
                        url=session.API_URL, debug=False, verbose=False, 
                       )

    parser.add_option("", "--dryrun", dest="debug", action="store_true",
                        help="Only issues 'Get*' calls to the API.  Commits nothing to the API")
    parser.add_option("", "--verbose", dest="verbose", action="store_true",
                        help="Print all the PLC API calls being made.")

    parser.add_option("", "--site", dest="site", 
                        help="only act on the given site")
    parser.add_option("", "--hostname", dest="hostname", 
                        help="only act on the given hostname")
    parser.add_option("", "--slicename", dest="slicename", 
                        help="only act on the given slicename")

    parser.add_option("", "--sitesonly", dest="sitesonly", action="store_true",
                        help="only sync sites, nodes, and pcus (ignore slices)")
    parser.add_option("", "--slicesonly", dest="slicesonly", action="store_true",
                        help="only sync slices to nodes (to save time)")
    parser.add_option("", "--sliceattrsonly", dest="sliceattrsonly", action="store_true",
                        help="only sync the attributes of slices (ignore sites) (to save time)")

    parser.add_option("", "--url", dest="url", 
                        help="PLC url to contact")
    parser.add_option("-6", "--sliceipv6", dest="sliceipv6", action="store_true",
                        help="Enable IPv6 assignment to slices as well as the host machine (if possible)")

    (options, args) = parser.parse_args()
    if len(sys.argv) == 1:
        usage()
        parser.print_help()
        sys.exit(1)

    session.setup_global_session(options.url, options.debug, options.verbose)

    # always setup the configuration for everything (very fast)
    for slice in slice_list:
        for site in site_list:
            for host in site['hosts']:
                h = site['hosts'][host]
                slice.add_host_address(h)

    # begin processing arguments to apply filters, etc
    # three options:
    #   - do only sites, slices, or slice attributes
    #   - do a single site, hostname, or slicename
    #   - do everything

    if ( options.sitesonly is not None or
         options.slicesonly is not None or 
         options.sliceattrsonly is not None ):
        pass
        if options.sitesonly:
            print "sites only"
            for x in site_list: print x ; break
        if options.slicesonly:
            print "slice only"
            for x in slice_list: print x ; break
        if options.sliceattrsonly:
            print "attr only"
            for x in slice_list: print x['attr'] ; break

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

        if options.hostname:
            print "hostname"
            for site in site_list:
                for host in site['hosts']:
                    h = site['hosts'][host]
                    if options.hostname in h.hostname():
                        print h
                        h.sync()
            pass

        if options.slicename:
            print "slicename"
            for slice in slice_list: 
                if slice['name']  == options.slicename:
                    print slice
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
