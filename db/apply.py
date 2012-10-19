#!/usr/bin/python

import pprint
#from planetlab.types import *
from planetlab import session
from slices import *
from sites  import *
import sys

def usage():
    return """
    apply.py takes static configurations stored in sites.py and slices.py
        and applies them to the PLC database adding or updating objects, 
        tags, and other values when appropriate.

    Examples:
        ./apply.py --dryrun ....
                Only perform Get* api calls.  Absolutely no changes are made
                to the PLC DB. HIGHLY recommended before changes.

        ./apply.py --syncsite all
                Does everything. Verifies existing sites & slices, creates
                sites that are non-existent.  This will take a very long time
                due to the delays for every RPC call to the PLC api.

        ./apply.py --syncsite nuq01
                Creates site, nodes, pcus, and associates slices with 
                these machines.  Pulls definitions from sites.py & 
                slices.py

        ./apply.py --syncsite nuq01 --on mlab4.nuq01.measurement-lab.org
                Resync the node configuration for given hostname.

        ./apply.py --syncslice all
                Associates *all* slices with all machines and updates any 
                pending slice attributes.  Sites and slices should be 
                defined in sites.py & slices.py
                
        ./apply.py --syncslice ooni_probe --skipwhitelist
                Like "--syncslice all" except only applied to the given
                slicename.

        ./apply.py --syncslice ooni_probe --on mlab4.nuq01.measurement-lab.org
                Performs the --syncslice operations, but only on the given
                target machine.  This is useful for applying IPv6 address
                updates (or other slice attributes) to only a few machines, 
                instead of all of them.  Some slice attributes may be applied
                globally, despite "--on <hostname>".

                In this example, ooni_probe must be explicitly permitted to
                receive an ipv6 on mlab4.nuq01 in slices.py. 
    Comments:
        Since an external sites & slices list was necessary while M-Lab was
        part of PlanetLab to differentiate mlab from non-mlab, 
        it may be possible to eliminate sites.py now. That really only
        needs to run once and subsequent slice operations could query the DB
        for a list of current sites or hosts.  More intelligent update 
        functions could to re-assign nodes to nodegroups, assign which hosts 
        are in the ipv6 pool, etc. just a thought.

        Keeping slices.py as a concise description of what and how slices
        are deployed to M-Lab is probably still helpful to see everything in
        one place.
"""

def main():

    from optparse import OptionParser
    parser = OptionParser(usage=usage())

    parser.set_defaults(syncsite=None, syncslice=None,
                        ondest=None, skipwhitelist=False, skipsliceips=False,
                        url=session.API_URL, debug=False, verbose=False, )

    parser.add_option("", "--dryrun", dest="debug", action="store_true",
                        help=("Only issues 'Get*' calls to the API.  "+
                              "Commits nothing to the API"))
    parser.add_option("", "--verbose", dest="verbose", action="store_true",
                        help="Print all the PLC API calls being made.")
    parser.add_option("", "--url", dest="url", 
                        help="PLC url to contact")

    parser.add_option("", "--on", metavar="hostname", dest="ondest", 
                        help="only act on the given host")

    parser.add_option("", "--syncsite", metavar="site", dest="syncsite", 
                help="only sync sites, nodes, pcus, if needed. (saves time)")
    parser.add_option("", "--syncslice", metavar="slice", dest="syncslice", 
                help="only sync slices and attributes of slices. (saves time)")

    parser.add_option("", "--skipwhitelist", dest="skipwhitelist", 
                action="store_true", 
                help=("dont try to white list the given slice. (saves time)"))
    parser.add_option("", "--skipsliceips", dest="skipsliceips", 
                action="store_true",
                help="dont try to assign ips to slice. (saves time)")

    (options, args) = parser.parse_args()
    if len(sys.argv) == 1:
        usage()
        parser.print_help()
        sys.exit(1)

    print "setup plc session"
    session.setup_global_session(options.url, options.debug, options.verbose)

    # always setup the configuration for everything (very fast)
    print "loading slice & site configuration"
    for sslice in slice_list:
        for site in site_list:
            for host in site['nodes']:
                h = site['nodes'][host]
                sslice.add_node_address(h)

    # begin processing arguments to apply filters, etc
    if ( options.syncsite is not None or 
         options.syncslice is not None ):

        if options.syncsite is not None:
            for site in site_list: 
                # sync everything when syncsite is None, 
                # or only when it matches
                if (options.syncsite == "all" or 
                    options.syncsite == site['name']):
                    print "Syncing: site", site['name']
                    site.sync(options.ondest)

        if options.syncslice:
            print options.syncslice
            for sslice in slice_list: 
                if (options.syncslice == "all" or 
                    options.syncslice == sslice['name']):
                    print "Syncing: slice", sslice['name']
                    sslice.sync(options.ondest, 
                               options.skipwhitelist, 
                               options.skipsliceips)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
