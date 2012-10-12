#!/usr/bin/python

import pprint

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
    interface['dns2']       = '8.8.8.4'
    interface['netmask']    = '255.255.255.192'
    interface['is_primary'] = True
    interface['gateway']    = '%s.%d' % (net_prefix, net_offset + 1)
    interface['broadcast']  = '%s.%d' % (net_prefix, net_offset + 63)
    interface['ip']         = '%s.%d' % (net_prefix, mlab_offset)
    return interface

def pl_v6_iplist(host_index, v6prefix, last_octet):
    mlab_offset = last_octet + ((host_index - 1) * 13) + 9
    return [ v6prefix+"%s"%ip for ip in range(mlab_offset + 1, mlab_offset + 13) ]

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

    def gateway(self):
        return pl_v6gw(self['prefix'], self['gw'])

    def iplist(self, index):
        return pl_v6_iplist(index, self['prefix'], int(self['last_octet']))

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

        if 'hosts' not in kwargs:
            kwargs['hosts'] = {}

            for i in range(1,kwargs['count']+1):
                h = Host(name=kwargs['name'], index=i, net=kwargs['net'])
                p = PCU(name=kwargs['name'], index=i, net=kwargs['net'])
                kwargs['hosts'][h.hostname()] = { 'interface' : h.interface(),
                                                  'iplist'    : h.iplist(),
                                                  'iplistv6'  : h.iplistv6(),
                                                  'pcu'       : p.fields() }
                #kwargs['pcus'][p.hostname()] = p.fields()

        super(Site, self).__init__(**kwargs)

    def func(self):
        print self['name']


class PCU(dict):
    def __str__(self):
        return pprint.pformat(self)
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
        
class Host(dict):
    def __str__(self):
        return pprint.pformat(self)
    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            raise Exception("'name' is a mandatory argument. i.e. FQDN")
        if 'index' not in kwargs:
            raise Exception("'index' is a mandatory argument. i.e. 1,2,3")
        if 'net' not in kwargs:
            raise Exception("'net' is a mandatory argument.")
        super(Host, self).__init__(**kwargs)

    def interface(self):
        return self['net']['v4'].interface(self['index'])
    def iplist(self):
        return self['net']['v4'].iplist(self['index'])
    def iplistv6(self):
        return self['net']['v6'].iplist(self['index'])

    def hostname(self):
        return "mlab%d.%s.measurement-lab.org"  % (self['index'], self['name'])

site_list = [
    Site(name='nuq01', net=Network(v4='64.9.225.128', v6='2604:ca00:f000::')),
]

class AttributeSet(dict):
    def __str__(self):
        return pprint.pformat(self)
    def __init__(self, **kwargs):
        if 'slice' not in kwargs:
            raise Exception("'slice' is a mandatory argument. i.e. iupui_ndt")
        if ('nodegroup' not in kwargs and 
            'hostname'  not in kwargs and 
             'all'      not in kwargs):
            raise Exception("Either 'nodegroup' or 'hostname' or 'all' is a mandatory "+\
                            "argument. i.e. MeasurementLab, or "+\
                            "'mlab1.hnd01.measurement-lab.org', or all=True")
        super(AttributeSet, self).__init__(**kwargs)

attribute_list = {
    'iupui_ndt' : [ AttributeSet(slice='iupui_ndt', nodegroup='MeasurementLab', 
                                    capabilities='VXC_PROC_WRITE', 
                                    disk_max='50000000'),
    AttributeSet(slice='iupui_ndt', nodegroup='MeasurementLabK32', 
                                    disk_max='50000000')],
    'iupui_npad' : [
    AttributeSet(slice='iupui_npad', all=True, initscript='iupui_npad_initscript'),
    AttributeSet(slice='iupui_npad', nodegroup='MeasurementLab', 
                                     capabilities='VXC_PROC_WRITE', 
                                     disk_max='10000000'),

    AttributeSet(slice='iupui_npad', nodegroup='MeasurementLabK32', 
                                     disk_max='10000000',
                                     vsys='web100_proc_write',
                                     pldistro='mlab'),
    ]
}

#slice_list = [
#    Slice(name='gt_partha', index=0, attr=attr['gt_partha']),
#]

#h = Host(name='nuq01', index=1, ipv4='64.9.225.128', ipv6='2604:ca00:f000::')
for x in site_list: print x
pprint.pprint(attribute_list)
#print h
