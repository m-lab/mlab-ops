#!/usr/bin/env python

import cgi
import html
import time
import re

name_map = { 'ndt'      : 'ndt.iupui',
             'neubot'   : 'neubot.mlab',
             'mobiperf' : '1.michigan',
             'npad'     : 'npad.iupui',
             'glasnost' : 'broadband.mpisws',
             'all'      : '', }

def parse():
    name = {}
    plugin_output = {}
    current_state = {}
    state_type = {}
    state = 0
    DB="/var/spool/nagios/status.dat"
    #DB="status.dat"

    request = cgi.FieldStorage() 

    curr_plugin_output = '';
    curr_name = '';
    curr_state = 0;
    curr_state_type = 0;
    curr_service_host = '';
    curr_service_descr = '';

    f = open(DB, 'r')
    for line in f.readlines():
        line = line.strip()

        # state 0 to state 1
        if ( state == 0 and "hoststatus {" in line):
            curr_name = '';
            curr_plugin_output = '';
            curr_state = 0;
            curr_state_type = 0;
            state = 1;
            continue

        # state 0 to state 2
        if ( state == 0 and "servicestatus {" in line ):
            curr_service_host = '';
            curr_service_descr = '';
            curr_name = '';
            curr_plugin_output = '';
            curr_state = 0;
            curr_state_type = 0;
            state = 2;
            continue

        # state 1 to state 0
        if ( state == 1 and "}" in line ):
            if curr_name != "":
                name[curr_name] = 1;
                plugin_output[curr_name] = curr_plugin_output;
                current_state[curr_name] = curr_state;
                state_type[curr_name] = curr_state_type;
            state = 0;

        # state 2 to state 0
        if ( state == 2 and "}" in line ):
            if ( curr_service_host != "" and curr_service_descr != "" ):
                curr_name = curr_service_host+'/'+curr_service_descr;
                name[curr_name] = 1;
                plugin_output[curr_name] = curr_plugin_output;
                current_state[curr_name] = curr_state;
                state_type[curr_name] = curr_state_type;
            state = 0;

        # nothing to do while we're in state 0
        if state == 0:
            continue

        # state 1, we're in a hoststatus
        if ( state == 1 ):
            m = re.search(r'host_name=(?P<host_name>.*)', line)
            if m is not None:
                test_name = m.group('host_name')
                if ( request.has_key('slice_name') and name_map.has_key(request['slice_name'].value) ):
                    prefix=name_map[request['slice_name'].value]
                    if ( re.search(prefix+"\.mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org", test_name) ):
                        curr_name = test_name
                continue

            m = re.search(r'plugin_output=(?P<plugin_output>.*)', line)
            if m is not None:
                curr_plugin_output = m.group('plugin_output')
                continue

            m = re.search(r'state_type=(?P<state_type>\d)', line)
            if m is not None:
                curr_state_type = m.group('state_type')
                continue
 
            m = re.search(r'current_state=(?P<current_state>\d)', line)
            if m is not None:
                curr_state = m.group('current_state')
                continue

        # state 2, we're in a servicestatus
        if ( state == 2 ):
            m = re.search(r'host_name=(?P<host_name>.*)', line)
            if m is not None:
                curr_service_host = m.group('host_name')
                continue

            m = re.search(r'service_description=(?P<service_description>.*)', line)
            if m is not None:
                tmp_descr = m.group('service_description')
                if ( request.has_key('service_name') and 
                     request['service_name'].value == tmp_descr ):
                        curr_service_descr = tmp_descr
                continue

            m = re.search(r'plugin_output=(?P<plugin_output>.*)', line)
            if m is not None:
                curr_plugin_output = m.group('plugin_output')
                continue

            m = re.search(r'state_type=(?P<state_type>\d)', line)
            if m is not None:
                curr_state_type = m.group('state_type')
                continue

            m = re.search(r'current_state=(?P<current_state>\d)', line)
            if m is not None:
                curr_state = m.group('current_state')
                continue

    f.close()

    for n in sorted(name.keys()):
        print n,
        if ( request.has_key('show_state') and request['show_state'].value == "1" ):
            print current_state[n]+' '+state_type[n],
        if ( request.has_key('plugin_output') and request('plugin_output') == "1" ):
            print plugin_output[n],
        print "";

def main():
    #print "
    #print "X-Open-Error: yes\n\n";
    #print "Content-Type: text/plain\n";
    print "Content-Type: text/plain";
    print "X-Database-Mtime: %s\n" % int(time.time())
    parse()

    #h = html.HTML()
    #h = h.html(newlines=True)
    #h.head("test")
    #b = h.body(newlines=True)
    #b.h1("this is a title")
    #b.h2("second header")
    #print h

if __name__ == "__main__":
    main()
