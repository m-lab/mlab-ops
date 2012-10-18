
import session as s
import sys
import pprint

def MakeSite(loginbase,name,abbreviated_name):
    site = s.api.GetSites({"login_base":loginbase})
    if len(site) == 0:
        print "MakeSite(%s,%s,%s)"%(loginbase,name,abbreviated_name)
        s.api.AddSite({"name":name,
                     "abbreviated_name":abbreviated_name,
                     "login_base": loginbase})
        site = s.api.GetSites({"login_base":loginbase})
    else:
        print "Confirmed: %s is in DB" % loginbase

    return site

def MakePerson(first_name, last_name, email):
    persons = s.api.GetPersons({"email":email,"enabled":True},["site_ids","email","person_id"])
    if len(persons)==0:
        print "Adding person %s" % email
        fields = {"first_name":first_name, "last_name":last_name, "email":email, "password":"clara_abcdefg"}
        personid = s.api.AddPerson(fields)
        s.api.UpdatePerson(personid, {'enabled': True})
        pipersonid = personid
    elif len(persons)==1:
        personid=persons[0]['person_id']
    else:
        personid=-1
    return personid

def AddPersonToSite(email,personid,role,loginbase):
    site = s.api.GetSites({"login_base":loginbase})
    if len(site) != 1:
        print "WARNING: problem with getting site info for loginbase=%s" % loginbase
    else:
        site = site[0]
        siteid = site["site_id"]
        if personid not in site['person_ids']:
            print "Added %s (%d) to site %d (%s)" % ( email, personid, siteid, loginbase)
            s.api.AddPersonToSite(personid,siteid)
            s.api.AddRoleToPerson(role,personid)
        else:
            print "Confirmed %s (%d) is %s for site %s" % ( email, personid, role, loginbase)

def MakeNode(login_base, hostname):
    node_list = s.api.GetNodes(hostname)
    if len(node_list) == 0:
        print "Adding Node %s to site %s" % (host, site['login_base'])
        node_id = s.api.AddNode(login_base, { 'boot_state' : 'reinstall',
                                            'model' : 'unknown',
                                            'hostname' : hostname,} )
    else:
        node_id = node_list[0]['node_id']       

    return node_id
 
def MakePCU(login_base, node_id, pcu_fields):
    pcu_list = s.api.GetPCUs({'hostname' : pcu_fields['hostname']})
    if len(pcu_list) == 0:
        print "Adding PCU to %s: %s", (host, pcu_fields )
        pcu_id = s.api.AddPCU(loginbase, pcu_fields)
        s.api.AddNodeToPCU(node_id, pcu_id, 1)
    else:
        if node_id in pcu_list[0]['node_ids']:
            print "Confirmed PCU %s is associated with node %d" % (pcu_list[0]['hostname'], node_id)
            pcu_id = pcu_list[0]['pcu_id']
        else:
            print "ERROR: need to add pcu node_id %s" % node_id
    return pcu_id

def PutNodeInNodegroup(hostname, node_id, nodegroup_name):
    node_list = s.api.GetNodes(node_id, ['nodegroup_ids', 'node_tag_ids'])
    nodegroup_list = s.api.GetNodeGroups({'groupname' : nodegroup_name}, ['nodegroup_id'])
    if len(nodegroup_list) > 0 and len(node_list) > 0:
        # NB: both are in the DB.
        # if node not in nodegroup then add it
        if nodegroup_list[0]['nodegroup_id'] not in node_list[0]['nodegroup_ids']:
            print "ADDING: %s to nodegroup %s" % (host, nodegroup_name)
            s.api.AddNodeTag(host, 'deployment', nodegroup_name)
        else:
            print "Confirmed: %s is in nodegroup %s"  % (hostname, nodegroup_name)
    else:
        print "ERROR: could not find node_id or nodegroup %s,%s" % (node_id, nodegroup_name)
        sys.exit(1)

        #node_tags = node_list[0]['node_tag_ids'] 
        #db_tags = []
        #for t in api.GetNodeTags(node_tags):
        #    db_tags.append( (t['tagname'], t['value'], t['node_tag_id']) )
        #    tags = sitevals['nodetags']
        #
        #     ok_tags = []
        #
        #     for (n,v,id) in db_tags:
        #        if (n,v) not in tags:
        #            api.DeleteNodeTag(id)
        #        else:
        #            ok_tags.append((n,v))
        #
        #     for (n,v) in tags:
        #        if (n,v) not in ok_tags:
        #            api.AddNodeTag(host, n, v)

def MakeInterfacesV6(hostname, node_id, interface, ipaddrs):
    if 'v6prefix' in hostnetworks[host]:
        v6prefix = hostnetworks[host]['v6prefix']
    else:
        v6prefix = None
    if 'v6gw' in hostnetworks[host]:
        v6gw = hostnetworks[host]['v6gw']
    else:
        v6gw = None

    #ip6setup(node['hostname'], v6prefix, v6gw)

def MakeInterfaceTags(hostname, node_id, interface, tagvalues):
    filter_dict = { "node_id" : node_id, 'ip' : interface['ip'] }
    interface_found = s.api.GetInterfaces(filter_dict)

    for tagname in tagvalues.keys():
        new_tags = { tagname : { "tag_type_id":None, "tag":None, "value": tagvalues[tagname] } }

    for name in new_tags.keys():
        # look up the tag type so we can pass the tagtypeid to AddTag later.
        tagtypes = s.api.GetTagTypes({"tagname":name})
        if len(tagtypes)==0:
            print "BUG: %s TagType does not exist.  Need to update MyPLC" % name
            sys.exit(1)
        else:
            new_tags[name]['tag_type_id'] = tagtypes[0]['tag_type_id']

        current_tags = s.api.GetInterfaceTags(interface_found[0]['interface_tag_ids'])
        for tag in current_tags:
            if new_tags.has_key(tag['tagname']):
                new_tags[tag['tagname']]['tag']=tag

        for k,v in new_tags.iteritems():
            tid = v['tag_type_id']
            if not v['tag']:
                # add setting
                print "ADD: tag %s->%s for %s" % (k,v['value'],interface['ip'])
                tag_id = s.api.AddInterfaceTag(interface_found[0]['interface_id'],tid,v['value'])
                if tag_id <= 0:
                    print "BUG: AddInterfaceTag(%d,%s) failed" % (iinterface_found[0]['interface_id'],v['value'])
                    sys.exit(1)
            else:
                # update setting
                tag = v['tag']
                if tag['value'] != v['value'] and k is not 'alias':
                    print "UPDATE: tag %s from %s->%s for %s" % (k,v['tag']['value'],v['value'],interface['ip'])
                    tag_id = tag['interface_tag_id']
                    s.api.UpdateInterfaceTag(tag_id,v['value'])
                else:
                    print "Confirmed: tag %s = %s for %s" % (k, v['value'], interface['ip'])

def InterfacesAreDifferent(declared, found):
    """ return True if the two dicts are different """
    if len(declared.keys()) == 0:
        return True
    for key in declared.keys():
        if key not in found:
            print "key not found in interface dict: %s" % key
            return True
        if declared[key] != found[key]:
            print ("values not equal in interface dict: declared[%s] "+
                   "== found[%s] :: %s == %s") % (key, key, declared[key], 
                                                    found[key])
            return True
    return False

def MakeInterface(hostname, node_id, interface, is_primary):
    primary_declared = interface
    filter_dict = {"node_id" : node_id, "is_primary" : is_primary, 'ip' : interface['ip']}
    interface_found = s.api.GetInterfaces(filter_dict)

    if len(interface_found) == 0:
        print "Adding: node network %s to %s" % (primary_declared['ip'], hostname)
        i_id = s.api.AddInterface(node_id, primary_declared)
    else:
        # TODO: clear any interface settings from primary interface
        if InterfacesAreDifferent(primary_declared, interface_found[0]):
            if len(primary_declared.keys()) == 0:
                print ("WARNING: found primary interface for %s in "+
                        "DB, but is NOT SPECIFIED in config!") % hostname
                pprint.pprint(interface_found[0])
            else:
                pprint.pprint( primary_declared )
                pprint.pprint( interface_found[0] )
                print "Updating: node network for %s to %s" % (
                            hostname, primary_declared)
                s.api.UpdateInterface(interface_found[0]['interface_id'], primary_declared)
        else:
            print "Confirmed: node network setup for %s for %s" % (hostname, interface['ip'])
        i_id = interface_found[0]['interface_id']

    # NOTE: everything that follows is only for non-primary interfaces.
    if is_primary is not True:
        goal = {
            "alias"  : str(i_id),
            "ifname" : "eth0"
        }
        MakeInterfaceTags(hostname, node_id, interface, goal)

#    goal = {
#        "alias"  : {"tag_type_id":None, "tag":None, "value":str(i_id)},
#        "ifname" : {"tag_type_id":None, "tag":None, "value":"eth0"}
#    }
#    if is_primary is not True:
#        for name in goal.keys():
#            tagtypes = s.api.GetTagTypes({"tagname":name})
#            if len(tagtypes)==0:
#                print "BUG: %s TagType does not exist.  Need to update MyPLC" % name
#                sys.exit(1)
#            else:
#                goal[name]['tag_type_id'] = tagtypes[0]['tag_type_id']
#
#            tags = s.api.GetInterfaceTags(interface_found[0]['interface_tag_ids'])
#            for tag in tags:
#                if goal.has_key(tag['tagname']):
#                    goal[tag['tagname']]['tag']=tag
#
#            for k,v in goal.iteritems():
#                tid = v['tag_type_id']
#                if not v['tag']:
#                    # add setting
#                    print "ADD: tag %s->%s for %s" % (k,v['value'],ipaddr)
#                    tag_id = s.api.AddInterfaceTag(interfaceid,tid,v['value'])
#                    if tag_id > 0:
#                        tag = s.api.GetInterfaceTags(tag_id)[0]
#                    else:
#                        print "BUG: AddInterfaceTag(%d,%s) failed" % (interfaceid,v['value'])
#                        sys.exit(1)
#                else:
#                    # update setting
#                    tag = v['tag']
#                    if tag['value'] <> v['value'] and k is not 'alias':
#                        print "UPDATE: tag %s from %s->%s for %s" % (k,v['tag']['value'],v['value'],interface['ip'])
#                        tag_id = tag['tag_id']
#                        s.api.UpdateInterfaceTag(tag_id,v['value'])
#                    else:
#                        print "Confirmed: tag %s = %s for %s" % (k, v['value'], interface['ip'])
#
#    #secondary_found = filter(lambda z: z['is_primary'] == False, s.api.GetInterfaces(node['interface_ids']))
    #alias_ips_in_db = [ x['ip'] for x in secondary_found ]
    #unspecified_ips_in_db = set(alias_ips_in_db) - set(ipaddrs)
    #if len(unspecified_ips_in_db) > 0:
    #    print "'iplist' : %s" % [ a for a in unspecified_ips_in_db ]
    #    print "WARNING: UNSPECIFIED IP addrs !!! found in DB for host %s" % (host)

def MakeSliceAttribute(slicename, attr):
    #{ 'attrtype': 'nodegroup',
    #  'disk_max': '50000000',
    #  'nodegroup': 'MeasurementLab' }

    tag_filter = {'name' : slicename}
    #print slicename, attr
    nd_id=None
    ng_id=None
    if attr['attrtype'] == None:
        # apply to all nodes
        ng=None
        nd=None
    elif attr['attrtype'] == "hostname":
        # apply to a node
        ng=None
        nd=attr[attr['attrtype']]
        nd_id = s.api.GetNodes({'hostname' : nd}, ['node_id'])[0]['node_id']
        tag_filter['node_id'] = nd_id
    elif attr['attrtype'] == "nodegroup":
        # apply to a nodegroup
        ng=attr[attr['attrtype']]
        ng_id = s.api.GetNodeGroups({'groupname' : ng}, 
                        ['nodegroup_id'])[0]['nodegroup_id']
        # NOTE: ']' means >=, '[' means <= 
        # HACK: these two directives work around a bug that prevents search 
        #       on strict match.  Need to submit patch.
        tag_filter[']nodegroup_id'] = ng_id
        tag_filter['[nodegroup_id'] = ng_id
        nd=None
    else:
        raise Exception("no attrtype in %s" % attr)

    sub_attr = {}
    for k in attr.keys():
        if k not in ['attrtype', attr['attrtype']]:
            sub_attr[k] = attr[k]
            # NOTE: GetSliceTags does not support nodegroup_id filtering :-/
            tag_filter['tagname'] = k
            sliceattrs = s.api.GetSliceTags(tag_filter)
            if len(sliceattrs) == 0:
                print "ADD: slice tag %s->%s for %s" % (k, attr[k], slicename)
                s.api.AddSliceTag(slicename, k, attr[k], nd, ng)
            elif len(sliceattrs) == 1:
                if ( sliceattrs[0]['node_id'] == nd_id and 
                     sliceattrs[0]['nodegroup_id'] == ng_id ):
                    #print "Confirmed: slice tag %s->%s on %s node:%s,%s" % (k, attr[k], slicename, nd, ng)
                    print "Confirmed: %s -> (%s,%s,%s,%s)" % (slicename, k, attr[k], nd, ng)
                else:
                    print "Uh-oh: slice tag %s->%s on %s missing ng_id:%s or nd_id:%s" % (
                                k, attr[k], slicename, ng_id, nd_id)
            else:
                # NOTE: this gets more complicated.
                print "ERR: There are multiple SliceTags that match: %s" % tag_filter
                for x in sliceattrs:
                    print x
                sys.exit(1)

    #assigned = filter(lambda attr: attr['node_id'] == node['node_id'], sliceattrs)
    #if len(assigned) != 0:
    #    print "Deleting: slice tag ip_addresses from %s on %s" % (slicename, node['hostname'])
    #    api.DeleteSliceTag(assigned[0]['slice_tag_id'])
    #api.AddSliceTag(slicename, 'ip_addresses', nnet['ip'], node['node_id'])

