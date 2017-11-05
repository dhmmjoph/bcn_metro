#coding: utf-8

'''
File: get_distances.py
Author: John Holbrook
Site: http://johnholbrook.us
Github: dhmmjoph
Description: Generates a .tsv file with the distance and time (supplied by Google Maps)
			 for a bunch of routes, which are specified in another .tsv file. A slight
			 complication is that the Google Maps Distance Matrix API's free plan
			 only allows 2500 requests per day. So, this program reads all the routes
			 from the input file ('list_of_routes.tsv'), gets the distance and time for
			 the first 2300 of them, appends that info to a different file ('distances.tsv',
			 which is created if it doesn't already exist), and writes the remaining routes
			 back to the input file. Thus, by running the program repeatedly on successive days,
			 you can get all the info needed without exceeding the API usage limits.
Date: 21 April 2017
'''

import csv
import os.path
import googlemaps

#set up google maps api
gmaps_key = open("gmaps_key.dat", "r").read()
gmaps = googlemaps.Client(key=gmaps_key)

#read in the list of uncomputed routes
with open("list_of_routes.tsv", 'r') as f:
	reader = csv.reader(f, delimiter="\t")
	all = []
	for row in reader:
		all += [row]

#if the file doesn't exist, create it and write the first row (headers)
if not os.path.isfile("distances.tsv"):
	with open("distances.tsv", "w") as f:
		f.write("waypoint1\twaypoint2\tdistance_m\tduration_s\n")

#now write the first 2300 routes to the output file
with open("distances.tsv", "a") as f:#'a' for append mode
	for route in all[:2300]:
		waypoint1 = route[0]
		waypoint2 = route[1]
		print "%s to %s" % (waypoint1, waypoint2)
		route = gmaps.distance_matrix(origins=[waypoint1],
                                      destinations=[waypoint2],
                                      mode='transit', # Change this to 'walking' for walking directions,
                                                      # 'bicycling' for biking directions, etc.
                                      language='English',
                                      units='metric')
		# 'distance' is in meters
		distance = route['rows'][0]['elements'][0]['distance']['value']
		# 'duration' is in seconds
		duration = route['rows'][0]['elements'][0]['duration']['value']
		#now write the info to the file	
		f.write("%s\t%s\t%s\t%s\n" % (waypoint1, waypoint2, distance, duration))

#now write the remaining routes back to list_of_routes.tsv
with open("list_of_routes.tsv", 'w') as f:#we want to overwrite the file
	for route in all[2300:]:
		f.write("%s\t%s\n" % (route[0], route[1]))

