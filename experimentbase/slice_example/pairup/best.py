#!/usr/bin/python

import math
import pprint

def distance(origin, destination):
    # The Haversine equation for distance around a sphere
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km - generally accepted radius of earth

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d

def main():
    f = open("sitesll.txt", 'r')
    lines = f.readlines()
    sites = {}
    for line in lines:
        fields = line.strip().split()
        sites[fields[0][6:]] = (float(fields[2]), float(fields[3]))

    pprint.pprint(sites)

    hits = {}
    for src_site in sorted(sites):
        hits[src_site] = 0

    for src_site in sorted(sites):
        sll = sites[src_site]
        results = []
        for dst_site in sorted(sites):
            dll = sites[dst_site]    
            if src_site != dst_site:
                results.append( (dst_site, distance(sll, dll)) )
        x=sorted(results, cmp=lambda x,y: int(x[1] - y[1]))
        for (i,j) in x[:3]:
            hits[i] += 1
            print src_site, i,j
        print ""
    pprint.pprint(hits)
    pass

if __name__ == "__main__":
    main()

