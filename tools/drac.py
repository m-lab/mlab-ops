#!/usr/bin/env python

import sys
import os
import subprocess
import time

DEBUG=False

def system(cmd):
    ## NOTE: use this rather than os.system() to catch 
    ##       KeyboardInterrupt correctly.
    if DEBUG: print cmd
    return subprocess.call(cmd, stdout=sys.stdout, 
                           stderr=sys.stderr, shell=True)

def usage():
    print """
    usage:
        All commands take a host specification.  A host spec is a FQHN, or a
        shorter pattern.  For example, "mlab1.nuq01", or "mlab1d.nuq01"
        without quotes are valid host specs and may be used interchangably.

        drac.py <host spec>

            Take hostname argument and print out associated PCU information.
            <hostname> may be a pattern, such as '*.site.measurement-lab.org'.
            Acts like the original 'drac-password.py' script.

        drac.py reboot <drac host spec>

            Use DRAC to reboot <hostname>

        drac.py shell <drac host spec>

            Take the drac-hostname argument and log into the DRAC interface via
            SSH.  Then, control is returned to the user to enter DRAC commands
            in the shell. i.e. reboot, or get system info, etc.

        drac.py console5 <drac host spec>
        drac.py console6 <drac host spec>

            Take the drac-hostname argument and open the JavaWebStart Virtual 
            Console.  This depends upon correct configuration of JavaWebStart, 
            which is platform dependent.  Check that 'javaws' is in your path.

            console5 is for  DRAC5
                ams01, ams02, atl01, dfw01, ham01, iad01, lax01, lga01, lga02, 
                lhr01, mia01, nuq01, ord01, par01, sea01, 

            console6 is for iDRAC6
                arn01, ath01, ath02, dub01, hnd01, mad01, mil01, syd01, syd02, 
                tpe01, vie01, wlg01, 

            unknown
                svg01, 

            unsupported (hpilo)
                trn01

            Not all systems have been tested. There may not be 100% coverage
            for MLab DRAC's.

        drac.py getsysinfo <drac host spec>

            Take the hostname argument and log into the DRAC interface via
            SSH.  Then run 'racadm getsysinfo'.
            <hostname> may be a pattern, such as '*.site.measurement-lab.org'.

        drac.py resetpassword <drac host spec> <newpassword>

            Take the drac-hostname and set a new password.
            The current password is taken from the PCU entry in the PLC 
            database.  Then, this command will log into the DRAC interface 
            and reset the password there.  Finally, it will update PLC's PCU 
            entry.
"""
    sys.exit(1)

def hspec_to_pcu(host_spec):
    f = host_spec.split(".")
    suffix = "measurement-lab.org"

    if len(f) == 2: ## short form.
        if f[0][-1] == 'd':  ## already a pcu name.
            return host_spec + "." + suffix
        else:
            return "%sd.%s." % (f[0],f[1]) + suffix

    elif len(f) == 4: ## long form
        if f[0][-1] == 'd':   ## already a pcu name.
            return host_spec
        else:
            f[0] = f[0]+"d"
            return ".".join(f)
    else:
        return host_spec
    return None

def hspec_to_node(host_spec):
    f = host_spec.split(".")
    suffix = "measurement-lab.org"

    if len(f) == 2: ## short form.
        if f[0][-1] == 'd':  ## already a pcu name.
            return "%s.%s." % (f[0][:-1],f[1]) + suffix
        else:
            return host_spec + "." + suffix

    elif len(f) == 4: ## long form
        if f[0][-1] == 'd':   ## already a pcu name.
            f[0] = f[0][:-1]
            return ".".join(f)
        else:
            return host_spec
    else:
        return host_spec
    return None


option="list"
if len(sys.argv) == 1:
    usage()

elif len(sys.argv) == 2:
    if sys.argv[1] in ["help", "-h", "--help"]:
        usage()
    host_spec = sys.argv[1]

elif len(sys.argv) == 3:
    option = sys.argv[1]
    host_spec = sys.argv[2]

elif len(sys.argv) == 4:
    option = sys.argv[1]
    host_spec = sys.argv[2]
    newpasswd = sys.argv[3]

## NOTE: Make sure the session is setup correctly.
## Use os.system() b/c the custom system() function
## doesn't flush stdout correctly. :-/
print "Verifying PLC Session...\n"
os.system("./plcquery.py --action=checksession")

if option == "shell":
    pcuname = hspec_to_pcu(host_spec)
    cmd=("./plcquery.py --action=get --type pcu --filter hostname=%s "+
         "--fields hostname,username,password,model") % pcuname
    h_u_pw_model=os.popen(cmd, 'r').read().strip().split()
    hostname = h_u_pw_model[0]
    user     = h_u_pw_model[1]
    passwd   = h_u_pw_model[2]
    model    = h_u_pw_model[3]

    print "Login can be slow. When you receive a prompt, try typing"
    print " 'help' or 'racadm help' for a list of available commands."
    print " 'exit' will exit the shell and 'drac.py' script.\n"

    system("expect exp/SHELL.exp %s %s '%s'" % (hostname, user, passwd) )

elif option == "console6":
    pcuname = hspec_to_pcu(host_spec)
    cmd=("./plcquery.py --action=get --type pcu --filter hostname=%s "+
         "--fields hostname,username,password,model") % pcuname
    h_u_pw_model=os.popen(cmd, 'r').read().strip().split()
    hostname = h_u_pw_model[0]
    user     = h_u_pw_model[1]
    passwd   = h_u_pw_model[2]
    model    = h_u_pw_model[3]

    if model != "DRAC":
        print ("This model PCU (%s) is not supported for automatic "+
               "console loading.") %model
        sys.exit(1)

    print "Virtual Console depends on correct setup of JavaWebStart..."

    def sendLoginRequest(username, passwd):
        url = 'data/login'
        postData = ('user=' + escapeStr(username) + 
                    '&password=' + escapeStr(passwd))
        return postData

    def escapeStr(val):
        escstr=""
        val = val.replace("\\", "\\\\")
        tmp = [ i for i in val ]
        for i in range(0,len(val)):
            if tmp[i] in ['@','(',')',',',':','?','=','&','#','+','%']:
                dec = ord(tmp[i])
                escstr+= "@0"+ "%02x" % dec
            else:
                escstr+=tmp[i]
        return escstr

    date_s=int((time.time())*1000)
    postData = sendLoginRequest(user, passwd)
    print "Logging in.."
    cookies = "--insecure --cookie-jar .cookies.txt --cookie .cookies.txt" 
    system("curl -s %s -d '%s' https://%s/data/login > /tmp/out.login" % 
            (cookies, postData, hostname))
    if DEBUG: system("cat /tmp/out.login"); time.sleep(10)
    cmd = ("sed -e 's/.*forwardUrl>index.html\\(.*\\)<\\/forwardUrl.*/\\1/g'"+
           " /tmp/out.login | tr '?' ' '")
    token = os.popen(cmd, 'r').read().strip()
    print "Getting *.jnlp for Java Web Start."

    ## NOTE: handle the variations on a theme.
    if "ath01" in hostname or "syd01" in hostname:
        url = "viewer.jnlp(%s@0@%s)" % (hostname, date_s)
    elif len(token) > 10:
        url = "viewer.jnlp(%s@0@title@%s@%s)" % (hostname, date_s, token)
    else:
        url = "viewer.jnlp(%s@0@title@%s)" % (hostname, date_s)

    system("curl -s %s 'https://%s/%s' > /tmp/out.jnlp" % 
             (cookies, hostname, url))
    if DEBUG: system("cat /tmp/out.jnlp")
    print "Loading JavaWebStart."
    system("javaws /tmp/out.jnlp")

elif option == "console5":
    pcuname = hspec_to_pcu(host_spec)
    cmd=("./plcquery.py --action=get --type pcu --filter hostname=%s "+
         "--fields hostname,username,password,model") % pcuname
    h_u_pw_model=os.popen(cmd, 'r').read().strip().split()
    hostname = h_u_pw_model[0]
    user     = h_u_pw_model[1]
    passwd   = h_u_pw_model[2]
    model    = h_u_pw_model[3]

    if model != "DRAC":
        print ("This model PCU (%s) is not supported for automatic "+
               "console loading.") % model
        sys.exit(1)

    print "Virtual Console depends on correct setup of JavaWebStart..."

    def sendLoginRequest(username, passwd):
        postData = ('user=' + escapeStr(username) + 
                    '&password=' + escapeStr(passwd))
        return postData

    def escapeStr(val):
        escstr=""
        val = val.replace("\\", "\\\\")
        tmp = [ i for i in val ]
        for i in range(0,len(val)):
            if tmp[i] in ['@','(',')',',',':','?','=','&','#','+','%']:
                dec = ord(tmp[i])
                escstr+= "@0"+ "%02x" % dec
            else:
                escstr+=tmp[i]
        return escstr

    date_s=int((time.time())*1000)
    cookies = "--insecure --cookie-jar .cookies.txt --cookie .cookies.txt"

    login_url = "cgi-bin/webcgi/login"
    postData = sendLoginRequest(user, passwd)

    print "Logging in.."
    system("curl -s %s -d '%s' 'https://%s/%s' > /tmp/out.login" % 
            (cookies, postData, hostname, login_url))

    session_url="cgi-bin/webcgi/vkvm?state=1"
    print "Getting Virtual Console SessionID.."
    system("curl -s %s 'https://%s/%s' > /tmp/tmp.out" % 
            (cookies, hostname, session_url))
    cmd = ("cat /tmp/tmp.out | grep vKvmSessionId |"+
           " tr '<>' ' ' | awk '{print $5}' ")
    kvmSessionId = os.popen(cmd).read().strip()

    print "Getting *.jnlp for Java Web Start."
    jnlp_url="vkvm/%s.jnlp" % kvmSessionId
    system("curl -s %s 'https://%s/%s' > /tmp/out.jnlp" % 
            (cookies, hostname, jnlp_url))

    ret = system("grep 'was not found on this server' /tmp/out.jnlp >/dev/null")
    if ret == 0:
        print "Second attempt..."
        jnlp_url="cgi-bin/webcgi/vkvmjnlp?id=%s" % date_s
        system("curl -s %s 'https://%s/%s' > /tmp/out.jnlp" % 
                (cookies, hostname, jnlp_url))

    print "Loading JavaWebStart."
    system("javaws /tmp/out.jnlp")

elif option == "getsysinfo":
    pcuname = hspec_to_pcu(host_spec)
    cmd=("./plcquery.py --action=get --type pcu --filter hostname=%s "+
         "--fields hostname,username,password,model") % pcuname
    lines= os.popen(cmd, 'r').readlines()
    for line in lines:
        h_u_pw_model= line.strip().split()
        hostname = h_u_pw_model[0]
        user     = h_u_pw_model[1]
        passwd   = h_u_pw_model[2]
        model    = h_u_pw_model[3]
        if model == "DRAC":
            system("expect exp/GETSYSINFO.exp %s %s '%s'" % 
                    (hostname, user, passwd) )
        else:
            print "%s is an unsupported PCU model" % model

elif option == "reboot":
    nodename = hspec_to_node(host_spec)
    cmd=("./plcquery.py --action=get --type node --filter hostname=%s "+
         "--fields pcu_ids") % nodename
    pcuids=os.popen(cmd, 'r').read().strip().split()
    for pcuid in pcuids:
        cmd=("./plcquery.py --action=get --type pcu --filter pcu_id=%s "+
             "--fields hostname,username,password,model") % pcuid
        h_u_pw=os.popen(cmd, 'r').read().strip().split()

        hostname = h_u_pw[0]
        user     = h_u_pw[1]
        passwd   = h_u_pw[2]
        model    = h_u_pw[3]
        if model == "DRAC":
            system("expect exp/REBOOT.exp %s %s '%s'" % 
                    (hostname, user, passwd) )
        else:
            print "%s is an unsupported PCU model" % model

elif option == "resetpassword":
    ## NOTE: be extra verbose for password resets, in case something goes
    ##       wrong, to see where.

    pcuname = hspec_to_pcu(host_spec)
    cmd=("./plcquery.py --action=get --type pcu --filter hostname=%s "+
         "--fields hostname,username,password,model") % pcuname
    print cmd
    h_u_pw_model=os.popen(cmd, 'r').read().strip().split()

    hostname = h_u_pw_model[0]
    user     = h_u_pw_model[1]
    passwd   = h_u_pw_model[2]
    model    = h_u_pw_model[3]

    if model != "DRAC":
        print "Unsupported PCU model '%s' for password reset." % model
        sys.exit(1)

    print ("expect exp/RESET_PASSWORD.exp %s %s '%s' '%s'" % 
            (hostname, user, passwd, newpasswd))
    ret = system("expect exp/RESET_PASSWORD.exp %s %s '%s' '%s'" % 
                    (hostname, user, passwd, newpasswd))
    if ret == 0:
        cmd = ("./plcquery.py --action=update --type pcu "+
               "--filter 'hostname=%s' "+
               "--fields 'password=%s'") % (hostname, newpasswd)
        print cmd
        system(cmd)

elif option == "list":

    nodename = hspec_to_node(host_spec)
    cmd=("./plcquery.py --action=get --type node "+
         "--filter hostname=%s --fields pcu_ids") % nodename

    pcuids=os.popen(cmd, 'r').read().strip().split()
    for pcuid in pcuids:
        cmd=("./plcquery.py --action=get --type pcu "+
             "--filter pcu_id=%s "+
             "--fields hostname,ip,username,password") % pcuid

        h_ip_u_p=os.popen(cmd, 'r').read().strip()
        f = h_ip_u_p.split()
        print "host:         %s" % nodename
        print "pcu hostname: https://%s" % f[0]
        print "pcu IP:       %s" % f[1]
        print "pcu username: %s" % f[2]
        print "pcu password  %s" % f[3]
