#!/usr/bin/python

from mlabconfig import hostnetworks
from mlabconfig import slices_with_ips
from planetlab import types
import sys
import pprint

hostname = sys.argv[1]
if hostname in hostnetworks.keys():
    lines = open('/home/soltesz/source/mlabops/inventory/logs/check_sliceips/%s.out'%hostname, 'r').readlines()
    ip_slices = [ line.strip().split(" ") for line in lines ]

    ideal_ip_list = types.pl_iplist(int(hostname[4]), hostnetworks[hostname]['primary']['network'])
    actual_ip_list = [ ip for ip,slice in ip_slices ]
    ideal_sl_list = slices_with_ips
    actual_sl_list = [ slice for ip,slice in ip_slices ]

    #slice_index = [ slices_with_ips.index(slice) for ip,slice in ip_slices ]
    z = [-1]*12

    #print "ideal"
    #for i,ip in enumerate(ideal_ip_list):
    #    print i, ideal_ip_list[i], ideal_sl_list[i]

    print "actual"
    for i,ip in enumerate(actual_ip_list):
        print i, actual_ip_list[i], actual_sl_list[i]
    print ""

    # ideal_index = lookup actual ip and find index into ideal ip list
    # z[ideal_index] = lookup actual slice and find index into ideal slice list
    for ip,slice in ip_slices:
        ideal_index = ideal_ip_list.index(ip)
        z[ideal_index] = ideal_sl_list.index(slice)

    #print z
    #print ideal_ip_list
    for p,i in enumerate(z):
        if i >= 0: print ideal_ip_list[p], i, ideal_sl_list[i]
    #print [ ideal_ip_list[i] for i in z ]



