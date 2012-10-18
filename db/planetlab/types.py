#!/usr/bin/python

import pprint
from sync import *
import session

def breakdown(host_index, v4prefix):
    octet_list = v4prefix.split('.')
    assert(len(octet_list) == 4)
    net_prefix = ".".join(octet_list[0:3])
    net_offset = int(octet_list[3])
    mlab_offset = net_offset + ((host_index - 1) * 13) + 9
    return (net_prefix, net_offset, mlab_offset)

def pl_interface(host_index, v4prefix):
    (net_prefix, net_offset, mlab_offset) = breakdown(host_index, v4prefix)
    interface={}
    interface['type']       = 'ipv4'
    interface['method']     = 'static'
    interface['network']    = v4prefix
    interface['dns1']       = '8.8.8.8'
    interface['dns2']       = '8.8.4.4'
    interface['netmask']    = '255.255.255.192'
    interface['is_primary'] = True
    interface['gateway']    = '%s.%d' % (net_prefix, net_offset + 1)
    interface['broadcast']  = '%s.%d' % (net_prefix, net_offset + 63)
    interface['ip']         = '%s.%d' % (net_prefix, mlab_offset)
    return interface

def pl_v6_iplist(host_index, v6prefix, last_octet):
    mlab_offset = last_octet + ((host_index - 1) * 13) + 9
    return [ v6prefix+"%s"%ip for ip in range(mlab_offset + 1, mlab_offset + 13) ]

def pl_v6_primary(host_index, v6prefix, last_octet):
    mlab_offset = last_octet + ((host_index - 1) * 13) + 9
    return v6prefix+"%s"% mlab_offset

def pl_iplist(host_index, v4prefix):
    (net_prefix, net_offset, mlab_offset) = breakdown(host_index, v4prefix)
    return [ '%s.%s' % (net_prefix,ip) for ip in range(mlab_offset + 1, mlab_offset + 13) ]

def pl_dracip(host_index, v4prefix):
    (net_prefix, net_offset, mlab_offset) = breakdown(host_index, v4prefix)
    return '%s.%d' % (net_prefix, net_offset+3+host_index)

def pl_v6gw(v6prefix, v6gw=None):
    return v6prefix + "1" if v6gw is None else v6gw

class Network(dict):
    legacy_network_remap = None
    def __str__(self):
        return pprint.pformat(self)
    def __init__(self, **kwargs):
        if 'v4' not in kwargs:
            raise Exception("'v4' is a mandatory argument. i.e. 64.9.225.128")
        if 'v6' not in kwargs:
            raise Exception("'v6' is a mandatory argument. i.e. 2604:ca00:f000::")

        kwargs['v4'] = NetworkIPv4(prefix=kwargs['v4'])
        kwargs['v6'] = NetworkIPv6(prefix=kwargs['v6'], last_octet=kwargs['v4'].last())
        if 'remap' in kwargs:
            kwargs['v4']['remap'] = kwargs['remap']
            kwargs['v6']['remap'] = kwargs['remap']
            del kwargs['remap']

        super(Network, self).__init__(**kwargs)

class NetworkIPv6(dict):
    def __str__(self):
        return pprint.pformat(self)
    def __init__(self, **kwargs):
        if 'prefix' not in kwargs:
            raise Exception("'prefix' is a mandatory argument. i.e. 2604:ca00:f000::")
        if 'last_octet' not in kwargs:
            msg ="'last_octet' is a mandatory argument. i.e. if v4 "
            msg+="prefix is 192.168.10.64 then last_octet is 64"
            raise Exception(msg)
        if 'gw' not in kwargs:
            kwargs['gw'] = None
        super(NetworkIPv6, self).__init__(**kwargs)

    def ipv6_defaultgw(self):
        return pl_v6gw(self['prefix'], self['gw'])

    def ipv6addr(self, index):
        return pl_v6_primary(index, self['prefix'], int(self['last_octet']))

    def ipv6addr_secondaries(self, index):
        # NOTE: the natural, sorted order is re-ordered according to 
        #       legacy_network_remap if present.
        ipv6_list = pl_v6_iplist(index, self['prefix'], int(self['last_octet']))
        if ( Network.legacy_network_remap is not None and 
             self['name'] in Network.legacy_network_remap and
             index in Network.legacy_network_remap[self['name']] ):

            index_list = Network.legacy_network_remap[self['name']][index].split(",")
            re_order = [ ipv6_list[int(i)] for i in index_list ]
            return re_order
            
        return ipv6_list

class NetworkIPv4(dict):
    def __str__(self):
        return pprint.pformat(self)
    def __init__(self, **kwargs):
        if 'prefix' not in kwargs:
            raise Exception("'prefix' is a mandatory argument. i.e.  192.168.10.0")
        super(NetworkIPv4, self).__init__(**kwargs)

    def interface(self, index):
        return pl_interface(index, self['prefix'])

    def iplist(self, index):
        ip_list = pl_iplist(index, self['prefix'])
        if (Network.legacy_network_remap is not None and 
            self['name'] in Network.legacy_network_remap and
            index in Network.legacy_network_remap[self['name']] ):
            index_list = Network.legacy_network_remap[self['name']][index].split(",")

            re_order = [ ip_list[int(i)] for i in index_list ]
            return re_order
        return ip_list 

    def drac(self, index):
        return pl_dracip(index, self['prefix'])

    def last(self):
        l = self['prefix'].split('.')[3]
        return int(l)

class Site(dict):
    def __str__(self):
        return pprint.pformat(self)
    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            raise Exception("'name' is a mandatory argument. i.e. nuq01, lga02")
        if 'net' not in kwargs:
            raise Exception("'net' is a mandatory argument.")

        if 'count' not in kwargs:
            kwargs['count'] = 3
        if 'nodegroup' not in kwargs:
            kwargs['nodegroup'] = 'MeasurementLab'
        if 'pi' not in kwargs:
            kwargs['pi'] = [ ("Stephen","Stuart","sstuart@google.com") ]

        kwargs['net']['v4']['name'] = kwargs['name']
        kwargs['net']['v6']['name'] = kwargs['name']
        kwargs['login_base'] = 'mlab%s' % kwargs['name']
        kwargs['sitename'] = 'MLab - %s' % kwargs['name'].upper()

        if 'nodes' not in kwargs:
            kwargs['nodes'] = {}

            for i in range(1,kwargs['count']+1):
                p = PCU(name=kwargs['name'], index=i, net=kwargs['net'])
                exclude_ipv6=True
                if ( 'exclude' not in kwargs or 
                    ('exclude' in     kwargs and i not in kwargs['exclude'])
                   ):
                    exclude_ipv6=False
                n = Node(name=kwargs['name'], index=i, net=kwargs['net'], 
                         pcu=p, nodegroup=kwargs['nodegroup'], exclude_ipv6=exclude_ipv6)
                kwargs['nodes'][n.hostname()] = n

        super(Site, self).__init__(**kwargs)

    def sync(self, onhost=None):
        site = MakeSite(self['login_base'], self['sitename'], self['sitename'])
        for person in self['pi']:
            p_id = MakePerson(*person)
            email = person[2]
            AddPersonToSite(email,p_id,"tech",self['login_base'])
            AddPersonToSite(email,p_id,"pi",self['login_base'])
        for hostname,node in self['nodes'].iteritems():
            if onhost is None or hostname == onhost:
                print node
                node.sync()

class PCU(dict):
    def __str__(self):
        #return pprint.pformat(self)
        return self.fields()
    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            raise Exception("'name' is a mandatory argument. i.e. FQDN")
        if 'net' not in kwargs:
            raise Exception("'net' is a mandatory argument.")
        if 'index' not in kwargs:
            raise Exception("'index' is a mandatory argument. i.e. 1,2,3")

        if 'username' not in kwargs:
            kwargs['username'] = 'admin'
        if 'password' not in kwargs:
            kwargs['password'] = 'changeme'
        if 'model' not in kwargs:
            kwargs['model'] = 'DRAC'
        super(PCU, self).__init__(**kwargs)

    def hostname(self):
        return "mlab%dd.%s.measurement-lab.org" % (self['index'], self['name'])

    def fields(self):
        return { 'username': self['username'],
                 'password': self["password"],      # password is updated later.
                 'model'   : self['model'],
                 'ip'      : self['net']['v4'].drac(self['index']),
                 'hostname': self.hostname() }
        
class Node(dict):
    def __str__(self):
        return str({ 'interface' : self.interface(),
                     'iplist'    : self.iplist(),
                     'iplistv6'  : self.iplistv6(), 
                     'pcu'       : self['pcu'].fields()})
    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            raise Exception("'name' is a mandatory argument. i.e. FQDN")
        if 'index' not in kwargs:
            raise Exception("'index' is a mandatory argument. i.e. 1,2,3")
        if 'net' not in kwargs:
            raise Exception("'net' is a mandatory argument.")
        if 'exclude_ipv6' not in kwargs:
            raise Exception("'exclude_ipv6' is a mandatory argument.")

        kwargs['login_base'] = 'mlab%s' % kwargs['name']
        kwargs['slicelist'] = []
        super(Node, self).__init__(**kwargs)

    def interface(self):
        return self['net']['v4'].interface(self['index'])
    def iplist(self):
        return self['net']['v4'].iplist(self['index'])
    def iplistv6(self):
        return self['net']['v6'].ipv6addr_secondaries(self['index'])

    def hostname(self):
        return "mlab%d.%s.measurement-lab.org"  % (self['index'], self['name'])
    def v6interface_tags(self):
        goal = {
            "ipv6_defaultgw"       : self['net']['v6'].ipv6_defaultgw(),
            "ipv6addr"             : self['net']['v6'].ipv6addr(self['index']),
            "ipv6addr_secondaries" : " ".join(self['net']['v6'].ipv6addr_secondaries(self['index']))
        }
        # TODO: secondaries should be added after slices with ipv6 addresses
        # are added, right?
        return goal

    def addslice(self, slicename):
        if slicename not in self['slicelist']:
            self['slicelist'].append(slicename)

    def sync(self):
        node_id = MakeNode(self['login_base'], self.hostname())
        pcu_id  = MakePCU(self['login_base'], node_id, self['pcu'].fields())
        PutNodeInNodegroup(self.hostname(), node_id, self['nodegroup'])
        interface = self.interface()
        MakeInterface(self.hostname(), node_id, interface, interface['is_primary'])

        if not self['exclude_ipv6']:
            MakeInterfaceTags(self.hostname(), node_id, interface, self.v6interface_tags())

        for ip in self.iplist():
            interface['ip'] = ip
            interface['is_primary'] = False
            MakeInterface(self.hostname(), node_id, interface, interface['is_primary'])


class Attr(dict):
    #def __str__(self):
    #    #return pprint.pformat(self)
    #    return str(self)
    def __init__(self, *args, **kwargs):
        if len(args) != 1:
            raise Exception("The first argument should be the name of a NodeGroup, hostname, or None")

        if type(args[0]) == type(None):
            kwargs['attrtype'] = 'all'
            kwargs['all'] = True

        if type(args[0]) == str:
            if '.' in args[0]: 
                kwargs['attrtype'] = 'hostname'
                kwargs['hostname'] = args[0]
            else:
                kwargs['attrtype'] = 'nodegroup'
                kwargs['nodegroup'] = args[0]

        super(Attr, self).__init__(**kwargs)

class Slice(dict):
    def __str__(self):
        return "\n%s \n\t %s" % (self['name'], pprint.pformat(self))

    def __init__(self, *args, **kwargs):
        if 'name' not in kwargs:
            raise Exception("The first argument should be the name of a NodeGroup, hostname, or None")
        if 'index' not in kwargs:
            kwargs['index'] = None
        if 'ipv6' not in kwargs:
            # None means ipv6 is OFF by default
            kwargs['ipv6'] = None
        else:
            kwargs['ipv6'] = [ h+'.measurement-lab.org' for h in kwargs['ipv6'] ]

        # *ALL* K32 kernels will need the isolate_loopback enabled.
        LOOPBACK=Attr('MeasurementLabK32', isolate_loopback='1')
        if 'attrs' not in kwargs:
            kwargs['attrs'] = []
        kwargs['attrs'] += [LOOPBACK]
        kwargs['network_list'] = []

        super(Slice, self).__init__(**kwargs)

    def add_node_address(self, node):
        h = node.hostname() 
        if self['index'] is not None:
            i = int(self['index'])
            ipv4=node.iplist()[i]
            ipv6=node.iplistv6()[i]
        else:
            ipv4=None
            ipv6=None
        net_tuple = (h, ipv4, "")
        # the node has ipv6, and the hostname is in the slice's ipv6 list,
        # or, ipv6 == "all"
              #( (type(self['ipv6']) == type([]) and h[:11] in self['ipv6']) or 
        if ( not node['exclude_ipv6'] and 
              ( (type(self['ipv6']) == type([]) and h     in self['ipv6']) or 
                (type(self['ipv6']) == str      and "all" in self['ipv6']) )
           ):
            net_tuple = (h, ipv4, ipv6)
        self['network_list'].append( net_tuple )
        
    def sync(self, hostname=None, skipwhitelist=False, skipsliceips=False):
        # NOTE: SLICES ARE NOT CREATED HERE.
        #       USERS  ARE NOT ADDED TO SLICES HERE.
        for attr in self['attrs']:
            MakeSliceAttribute(self['name'], attr)
        for h,v4,v6 in self['network_list']:
            if hostname is None or h == hostname:
                if not skipsliceips:
                    val = v4 if v6=="" else v4+","+v6
                    attr = Attr(h, ip_addresses=val)
                    MakeSliceAttribute(self['name'], attr)
                if not skipwhitelist:
                    # add this slice to whitelist of all hosts.
                    WhitelistSliceOnNode(self['name'], h)
        return

