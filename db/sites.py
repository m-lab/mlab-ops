#!/usr/bin/python

import pprint
from planetlab.types import *

# NOTE: The legacy network remap is used to re-order the automatically
#   generated, sequential list of ipaddresses to a legacy order to preserve 
#   slice-and-IP assignments.  Otherwise, slices would be assigned to new 
#   IPs, and for now, we wish to preserve the slice-node-ip mapping.
# An appropriate time to remove this and re-assign IPs to slices would be
#   after a major update & reinstallation, such as LXC kernel update.
legacy_network_remap = {
#'SITE' : { HOST_INDEX : 'natural-order-index-list', }
 'ams01': {1: '11,10,0,1,5,4,3,2,9,8,7,6',
           2: '7,8,10,9,11,0,1,2,3,4,5,6',
           3: '1,0,3,2,10,9,6,11,5,4,8,7'},
 'ams02': {1: '7,5,11,10,9,8,4,6,2,3,0,1',
           2: '0,7,8,9,10,3,4,5,6,11,2,1',
           3: '11,3,9,8,5,4,7,6,1,0,10,2'},
 'ath01': {1: '8,9,2,3,0,1,6,7,4,5,11,10',
           2: '0,7,8,9,10,4,3,2,1,11,6,5',
           3: '5,4,7,6,9,8,11,10,0,1,2,3'},
 'atl01': {1: '3,9,10,11,4,5,1,0,8,2,6,7',
           2: '8,10,4,3,6,5,0,2,1,9,7,11',
           3: '10,8,4,5,0,1,2,3,9,11,7,6'},
 'dfw01': {1: '0,1,2,3,4,5,6,7,8,9,11,10',
           2: '6,5,9,10,7,8,2,1,11,3,4,0',
           3: '2,3,0,1,7,6,5,4,11,10,9,8'},
 'ham01': {1: '7,6,5,4,3,2,1,0,8,9,10,11',
           2: '1,2,10,9,11,6,5,8,7,3,4,0',
           3: '8,9,6,7,4,5,2,3,1,0,10,11'},
 'lax01': {1: '4,5,6,0,1,2,3,8,9,11,10,7',
           2: '10,1,6,5,7,0,8,9,11,4,3,2',
           3: '7,6,5,4,11,10,9,8,2,3,0,1'},
 'lga01': {1: '11,10,9,8,7,6,5,4,3,2,1,0',
           2: '11,10,9,8,7,6,5,4,3,2,1,0',
           3: '4,3,11,10,9,8,7,6,5,2,1,0'},
 'lga02': {1: '3,2,5,4,7,6,9,8,11,10,0,1',
           2: '1,2,0,5,6,3,4,7,8,11,10,9',
           3: '9,11,7,6,5,4,3,2,1,0,10,8'},
 'lhr01': {1: '11,10,9,7,4,5,2,3,0,1,6,8',
           2: '0,7,9,10,3,4,5,6,8,11,2,1',
           3: '9,8,5,4,7,6,1,0,3,2,10,11'},
 'mia01': {1: '10,11,8,9,7,6,3,2,5,4,1,0',
           2: '11,10,9,8,7,6,0,3,5,4,1,2',
           3: '6,7,8,9,2,3,4,5,10,11,1,0'},
 'nuq01': {1: '10,9,8,7,6,5,4,3,2,1,0,11',
           2: '1,2,3,4,5,6,7,8,9,10,11,0',
           4: '2,11,10,9,8,7,6,5,4,3,1,0'},
 'ord01': {1: '7,3,5,4,0,2,9,8,1,6,11,10',
           2: '10,9,11,0,1,2,3,4,5,6,7,8',
           3: '5,4,8,10,11,1,9,6,7,3,2,0'},
 'par01': {1: '8,9,10,11,7,6,5,4,3,2,1,0',
           2: '10,9,11,6,5,1,2,3,4,7,8,0',
           3: '8,9,6,7,4,5,2,3,1,0,10,11'},
 'sea01': {1: '10,2,3,0,1,11,5,9,8,7,6,4',
           2: '11,2,1,7,8,9,10,3,4,5,6,0',
           3: '7,1,0,3,2,5,4,10,6,9,8,11'}
}
Network.legacy_network_remap = legacy_network_remap

# name : site prefix, used to generate PL site name, hostnames, etc
# net  : v4 & v6 network prefixes and definitions.

site_list = [
    Site(name='akl01', net=Network(v4='163.7.129.0',     v6='2404:0138:4009::')),
    Site(name='ams01', net=Network(v4='213.244.128.128', v6='2001:4C08:2003:2::')), 
    Site(name='ams02', net=Network(v4='72.26.217.64',    v6='2001:48c8:7::')), 
    Site(name='arn01', net=Network(v4='213.248.112.64',  v6='2001:2030:0000:001B::')), 
    Site(name='atl01', net=Network(v4='4.71.254.128',    v6='2001:1900:3001:C::')), 
    Site(name='ath01', net=Network(v4='83.212.4.0',      v6='2001:648:2ffc:2101::')), 
    Site(name='ath02', net=Network(v4='83.212.5.128',    v6='2001:648:2ffc:2102::')), 
    Site(name='dfw01', net=Network(v4='38.107.216.0',    v6='2001:550:2000::')), 
    Site(name='dub01', net=Network(v4='193.1.12.192',    v6='2001:770:B5::')), 
    Site(name='ham01', net=Network(v4='80.239.142.192',  v6='2001:2030:0000:0019::')), 
    Site(name='hnd01', net=Network(v4='203.178.130.192', v6='2001:200:0:b801::')), 
    Site(name='iad01', net=Network(v4='216.156.197.128', v6='2610:18:111:8001::')), 
    Site(name='lax01', net=Network(v4='38.98.51.0',      v6='2001:550:6800::')), 
    Site(name='lba01', net=Network(v4='109.239.110.0',   v6='2a00:1a80:1:8::')), 
    Site(name='lga01', net=Network(v4='74.63.50.0',      v6='2001:48c8:5:f::')), 
    Site(name='lga02', net=Network(v4='38.106.70.128',   v6='2001:550:1D00:100::')), 
    Site(name='lhr01', net=Network(v4='217.163.1.64',    v6='2001:4C08:2003:3::')), 
    Site(name='lju01', net=Network(v4='91.239.96.64',    v6='2001:67c:27e4:100::')), 
    Site(name='mad01', net=Network(v4='213.200.103.128', v6='2001:0668:001F:0016::')), 
    Site(name='mia01', net=Network(v4='4.71.210.192',    v6='2001:1900:3001:A::')), 
    Site(name='mil01', net=Network(v4='213.200.99.192',  v6='2001:0668:001F:0017::')), 
    Site(name='nuq01', net=Network(v4='64.9.225.128',    v6='2604:ca00:f000::'), count=4, exclude=[1,2,3]),
    Site(name='nuq02', net=Network(v4='149.20.5.64',     v6='2001:4F8:1:1001::')),
    Site(name='ord01', net=Network(v4='4.71.251.128',    v6='2001:1900:3001:B::')), 
    Site(name='par01', net=Network(v4='80.239.168.192',  v6='2001:2030:0000:001A::')), 
    Site(name='sea01', net=Network(v4='38.102.0.64',     v6='2001:550:3200:1::')), 
   #Site(name='svo01', net=Network(v4=None,              v6='2a01:798:0:13::')), 
    Site(name='svg01', net=Network(v4='81.167.39.0',     v6='2a01:798:0:13::'), nodegroup='MeasurementLabK32'),
    Site(name='syd01', net=Network(v4='203.5.76.128',    v6='2001:388:00d0::')), 
    Site(name='syd02', net=Network(v4='175.45.79.0',     v6='2402:7800:0:12::')), 
    Site(name='tpe01', net=Network(v4='163.22.28.0',     v6='2001:e10:6840:28::')), 
    Site(name='trn01', net=Network(v4='194.116.85.192',  v6='2001:7F8:23:307::')), 
    Site(name='vie01', net=Network(v4='213.208.152.0',   v6='2a01:190:1700:38::'), nodegroup='MeasurementLabK32'), 
    Site(name='wlg01', net=Network(v4='103.10.233.0',    v6='2404:2000:3000::')), 
]


