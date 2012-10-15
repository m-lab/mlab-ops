#!/usr/bin/env python

import getpass
import xmlrpclib
import os
import sys
import re

SESSION_DIR=os.environ['HOME'] + "/.ssh"
SESSION_FILE=SESSION_DIR + "/mlab_session"
API_URL = "https://boot.planet-lab.org/PLCAPI/"

api = None

def setup_global_session(url, debug, verbose):
    global api
    global API_URL
    API_URL=url
    api = getapi(debug, verbose)
    return api

class API:
    def __init__(self, auth, url, debug=False, verbose=False):
        self.debug = debug
        self.verbose = verbose
        self.auth = auth
        self.api = xmlrpclib.Server(url, verbose=False, allow_none=True)
    def __repr__(self):
        return self.api.__repr__()
    def __getattr__(self, name):
        run = True
        if self.debug and 'Get' not in name:
            # Do no run when debug=True & not a Get* api call
            run = False

        method = getattr(self.api, name)
        if method is None:
            raise AssertionError("method does not exist")

        #if self.verbose: 
        #    print "%s(%s)" % (name, params)

        def call_method(auth, *params):
            if self.verbose: 
                print "%s(%s)" % (name, params)
            return method(self.auth, *params)

        if run:
            return lambda *params : call_method(self.auth, *params)
        else:
            print "DEBUG: Skipping %s()" % name
            return lambda *params : 1

        #return lambda *params : call_method(*params)
        #return call_method(*params)

def refreshsession():
    # Either read session from disk or create it and save it for later
    print "PLC Username: ",
    sys.stdout.flush()
    username = sys.stdin.readline().strip()
    password = getpass.getpass("PLC Password: ")
    auth = {'Username' : username,
            'AuthMethod' : 'password',
            'AuthString' : password}
    plc = API(auth, API_URL)
    session = plc.GetSession(60*60*24*30)
    try:
        os.makedirs(SESSION_DIR)
    except:
        pass
    f = open(SESSION_FILE, 'w')
    print >>f, session
    f.close()

def getapi(debug=False, verbose=False):
    api = xmlrpclib.ServerProxy(API_URL, allow_none=True)
    auth = None
    authorized = False
    while not authorized:
        try:
            auth = {}
            auth['AuthMethod'] = 'session'
            auth['session'] = open(SESSION_FILE, 'r').read().strip()
            authorized = api.AuthCheck(auth)
            if not authorized:
                print "Need to refresh your PLC session file: %s" % SESSION_FILE
                sys.stdout.flush()
                refreshsession()
        except:
            #import traceback
            #traceback.print_exc()
            print "Need to setup a new PLC session file: %s" % SESSION_FILE
            sys.stdout.flush()
            refreshsession()

    assert auth is not None
    return API(auth, API_URL, debug, verbose)

