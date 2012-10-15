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
        # TODO: add ip reordering as with ipv4, this will allow easier ip-to-slice mapping
        #if (self.legacy_network_remap is not None and 
        #    self['name'] in self.legacy_network_remap and
        #    index in self.legacy_network_remap[self['name']] ):
        #if 'remap' in self and index in self['remap']:
        #    l = pl_v6_iplist(index, self['prefix'], int(self['last_octet']))
        #    ip_list = [ l[int(i)] for i in self['remap'][index].split(",") ]
        #    return ip_list
        return pl_v6_iplist(index, self['prefix'], int(self['last_octet']))

class NetworkIPv4(dict):
    legacy_network_remap = None
    def __str__(self):
        return pprint.pformat(self)
    def __init__(self, **kwargs):
        if 'prefix' not in kwargs:
            raise Exception("'prefix' is a mandatory argument. i.e.  192.168.10.0")
        super(NetworkIPv4, self).__init__(**kwargs)

    def interface(self, index):
        return pl_interface(index, self['prefix'])

    def iplist(self, index):
        if (self.legacy_network_remap is not None and 
            self['name'] in self.legacy_network_remap and
            index in self.legacy_network_remap[self['name']] ):
        #if 'remap' in self and index in self['remap']:
            l = pl_iplist(index, self['prefix'])
            index_list = self.legacy_network_remap[self['name']][index].split(",")
            ip_list = [ l[int(i)] for i in index_list ]
            return ip_list
        else:
            return pl_iplist(index, self['prefix'])

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
        kwargs['login_base'] = 'mlab%s' % kwargs['name']
        kwargs['sitename'] = 'MLab - %s' % kwargs['name'].upper()

        if 'hosts' not in kwargs:
            kwargs['hosts'] = {}

            for i in range(1,kwargs['count']+1):
                p = PCU(name=kwargs['name'], index=i, net=kwargs['net'])
                h = Node(name=kwargs['name'], index=i, net=kwargs['net'], pcu=p, nodegroup=kwargs['nodegroup'])
                kwargs['hosts'][h.hostname()] = h 
        super(Site, self).__init__(**kwargs)

    def sync(self):
        site = MakeSite(self['login_base'], self['sitename'], self['sitename'])
        for person in self['pi']:
            p_id = MakePerson(*person)
            email = person[2]
            AddPersonToSite(email,p_id,"tech",self['login_base'])
            AddPersonToSite(email,p_id,"pi",self['login_base'])

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
        MakeInterfaceTags(self.hostname(), node_id, interface, self.v6interface_tags())
        for ip in self.iplist():
            interface['ip'] = ip
            interface['is_primary'] = False
            MakeInterface(self.hostname(), node_id, interface, interface['is_primary'])

class Attr(dict):
    def __str__(self):
        return pprint.pformat(self)
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

        # *ALL* K32 kernels will need the isolate_loopback enabled.
        LOOPBACK=Attr('MeasurementLabK32', isolate_loopback='1')
        if 'attr' not in kwargs:
            kwargs['attr'] = []
        kwargs['attr'] += [LOOPBACK]
            
        kwargs['attrlist'] = []
        kwargs['hostlist'] = []
        kwargs['ipv4'] = []
        kwargs['ipv6'] = []

        super(Slice, self).__init__(**kwargs)

    def add_host_address(self, host):
        h = host.hostname() 
        if self['index'] is not None:
            i = int(self['index'])
            ipv4=host.iplist()[i]
            ipv6=host.iplistv6()[i]
        else:
            ipv4=None
            ipv6=None
        self['attrlist'].append( (h, ipv4, ipv6) )
        

