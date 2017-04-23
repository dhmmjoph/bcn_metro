'''
File: optimize_routes.py
Modified by: John Holbrook
Site: http://johnholbrook.us
Github: dhmmjoph
Description: This file is based on Randall Olson's code for using Paretto optimization to
			 compute optimal road trips. I have modified it (*very* lightly) so that instead
			 of generating .html files containing visual depictions of the route, it simply
			 prints to the terminal all the waypoints in the longest route, in the order they're
			 visited.
Date: 21 April 2017
'''
'''
COPYRIGHT DISCLAIMER
Adapted from work that is (c) Randall S Olson (http://www.randalolson.com/)
Licensed under the CC BY 4.0 License (https://creativecommons.org/licenses/by/4.0/)
and/or the MIT License (https://opensource.org/licenses/mit-license.html)
The original version of this work is available at 
https://github.com/rhiever/Data-Analysis-and-Machine-Learning-Projects/blob/master/pareto-optimized-road-trip/optimized-state-capitols-trip.ipynb
'''
import pandas as pd
import numpy as np
import random
import copy
from tqdm import tqdm

from deap import algorithms
from deap import base
from deap import creator
from deap import tools


waypoint_distances = {}
waypoint_durations = {}
all_waypoints = set()

waypoint_data = pd.read_csv('my-waypoints-dist-dur.tsv', sep='\t')

for i, row in waypoint_data.iterrows():
	# Distance = meters
	waypoint_distances[frozenset([row.waypoint1, row.waypoint2])] = row.distance_m
	
	# Duration = hours
	waypoint_durations[frozenset([row.waypoint1, row.waypoint2])] = row.duration_s / (60. * 60.)
	all_waypoints.update([row.waypoint1, row.waypoint2])

import random
import numpy as np
import copy
from tqdm import tqdm

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

creator.create('FitnessMulti', base.Fitness, weights=(1.0, -1.0))
creator.create('Individual', list, fitness=creator.FitnessMulti)

toolbox = base.Toolbox()
toolbox.register('waypoints', random.sample, all_waypoints, random.randint(2, 20))
toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.waypoints)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)

def eval_capitol_trip(individual):
	"""
		This function returns the total distance traveled on the current road trip
		as well as the number of waypoints visited in the trip.
		
		The genetic algorithm will favor road trips that have shorter
		total distances traveled and more waypoints visited.
	"""
	trip_length = 0.
	individual = list(individual)
	
	# Adding the starting point to the end of the trip forces it to be a round-trip
	individual += [individual[0]]
	
	for index in range(1, len(individual)):
		waypoint1 = individual[index - 1]
		waypoint2 = individual[index]
		trip_length += waypoint_distances[frozenset([waypoint1, waypoint2])]
		
	return len(set(individual)), trip_length

def pareto_selection_operator(individuals, k):
	"""
		This function chooses what road trips get copied into the next generation.
		
		The genetic algorithm will favor road trips that have shorter
		total distances traveled and more waypoints visited.
	"""
	return tools.selNSGA2(individuals, int(k / 5.)) * 5

def mutation_operator(individual):
	"""
		This function applies a random change to one road trip:
		
			- Insert: Adds one new waypoint to the road trip
			- Delete: Removes one waypoint from the road trip
			- Point: Replaces one waypoint with another different one
			- Swap: Swaps the places of two waypoints in the road trip
	"""
	possible_mutations = ['swap']
	
	if len(individual) < len(all_waypoints):
		possible_mutations.append('insert')
		possible_mutations.append('point')
	if len(individual) > 2:
		possible_mutations.append('delete')
	
	mutation_type = random.sample(possible_mutations, 1)[0]
	
	# Insert mutation
	if mutation_type == 'insert':
		waypoint_to_add = individual[0]
		while waypoint_to_add in individual:
			waypoint_to_add = random.sample(all_waypoints, 1)[0]
			
		index_to_insert = random.randint(0, len(individual) - 1)
		individual.insert(index_to_insert, waypoint_to_add)
	
	# Delete mutation
	elif mutation_type == 'delete':
		index_to_delete = random.randint(0, len(individual) - 1)
		del individual[index_to_delete]
	
	# Point mutation
	elif mutation_type == 'point':
		waypoint_to_add = individual[0]
		while waypoint_to_add in individual:
			waypoint_to_add = random.sample(all_waypoints, 1)[0]
		
		index_to_replace = random.randint(0, len(individual) - 1)
		individual[index_to_replace] = waypoint_to_add
		
	# Swap mutation
	elif mutation_type == 'swap':
		index1 = random.randint(0, len(individual) - 1)
		index2 = index1
		while index2 == index1:
			index2 = random.randint(0, len(individual) - 1)
			
		individual[index1], individual[index2] = individual[index2], individual[index1]
	
	return individual,


toolbox.register('evaluate', eval_capitol_trip)
toolbox.register('mutate', mutation_operator)
toolbox.register('select', pareto_selection_operator)

def pareto_eq(ind1, ind2):
	return np.all(ind1.fitness.values == ind2.fitness.values)

pop = toolbox.population(n=1000)
hof = tools.ParetoFront(similar=pareto_eq)
stats = tools.Statistics(lambda ind: (int(ind.fitness.values[0]), round(ind.fitness.values[1], 2)))
stats.register('Minimum', np.min, axis=0)
stats.register('Maximum', np.max, axis=0)
# This stores a copy of the Pareto front for every generation of the genetic algorithm
stats.register('ParetoFront', lambda x: copy.deepcopy(hof))
# This is a hack to make the tqdm progress bar work
stats.register('Progress', lambda x: pbar.update())

# How many iterations of the genetic algorithm to run
# The more iterations you allow it to run, the better the solutions it will find
total_gens = 30000

pbar = tqdm(total=total_gens)
pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0., mutpb=1.0, ngen=total_gens, 
							   stats=stats, halloffame=hof, verbose=False)
pbar.close()
print hof[0]
print len(hof[0])
count = 1
for item in hof[0]:
	print "%i: %s" % (count, item)
	count += 1

def print_route(optimized_routes):
	# This line makes the road trips round trips
	optimized_routes = [list(route) + [route[0]] for route in optimized_routes]
	count = 1
	for stop in optimized_routes[-1]:
		print "Waypoint %i: %s" % (count, route)

def create_individual_road_trip_maps(optimized_routes):
	"""
		This function takes a list of optimized road trips and generates
		individual maps of them using the Google Maps API.
	"""
	
	# This line makes the road trips round trips
	optimized_routes = [list(route) + [route[0]] for route in optimized_routes]
	print optimized_routes[-1]

	for route_num, route in enumerate(optimized_routes):
		Page_1 = """
		<!DOCTYPE html>
		<html lang="en">
		  <head>
			<meta charset="utf-8">
			<meta name="viewport" content="initial-scale=1.0, user-scalable=no">
			<meta name="description" content="Randy Olson uses machine learning to find the optimal road trip across the U.S.">
			<meta name="author" content="Randal S. Olson">

			<title>An optimized road trip across the U.S. according to machine learning</title>
			<style>
			  html, body, #map-canvas {
				  height: 100%;
				  margin: 0px;
				  padding: 0px
			  }
			  #panel {
				  position: absolute;
				  top: 5px;
				  left: 50%;
				  margin-left: -180px;
				  z-index: 5;
				  background-color: #fff;
				  padding: 10px;
				  border: 1px solid #999;
			  }
			</style>
			<script src="https://maps.googleapis.com/maps/api/js?v=3"></script>
			<script>
				var routesList = [];
				var markerOptions = {icon: "http://maps.gstatic.com/mapfiles/markers2/marker.png"};
				var directionsDisplayOptions = {preserveViewport: true,
												markerOptions: markerOptions};
				var directionsService = new google.maps.DirectionsService();
				var map;

				function initialize() {
					var center = new google.maps.LatLng(41, 2);
					var mapOptions = {
						zoom: 5,
						center: center
					};
					map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
					for (var i = 0; i < routesList.length; i++) {
						routesList[i].setMap(map); 
					}
				}
				function calcRoute(start, end, routes) {
					var directionsDisplay = new google.maps.DirectionsRenderer(directionsDisplayOptions);
					var waypts = [];
					for (var i = 0; i < routes.length; i++) {
						waypts.push({
							location:routes[i],
							stopover:true});
						}

					var request = {
						origin: start,
						destination: end,
						waypoints: waypts,
						optimizeWaypoints: false,
						//travelMode: google.maps.TravelMode.TRANSIT
						travelMode: 'TRANSIT'
					};
					directionsService.route(request, function(response, status) {
						if (status == google.maps.DirectionsStatus.OK) {
							directionsDisplay.setDirections(response);
							directionsDisplay.setMap(map);
						}
					});

					routesList.push(directionsDisplay);
				}
				function createRoutes(route) {
					// Google's free map API is limited to 10 waypoints so need to break into batches
					var subset = 0;
					while (subset < route.length) {
						var waypointSubset = route.slice(subset, subset + 10);
						var startPoint = waypointSubset[0];
						var midPoints = waypointSubset.slice(1, waypointSubset.length - 1);
						var endPoint = waypointSubset[waypointSubset.length - 1];
						calcRoute(startPoint, endPoint, midPoints);
						subset += 9;
					}
				}

				"""
		Page_2 = """
				createRoutes(optimized_route);
				google.maps.event.addDomListener(window, "load", initialize);
			</script>
		  </head>
		  <body>
			<div id="map-canvas"></div>
		  </body>
		</html>
		"""

		with open('optimized-us-capitol-trip-{}-states.html'.format(route_num + 2), 'w') as output_file:
			output_file.write(Page_1)
			output_file.write('optimized_route = {};'.format(str(route)))
			output_file.write(Page_2)

#create_individual_road_trip_maps(reversed(hof))
#print_route(reversed(hof))