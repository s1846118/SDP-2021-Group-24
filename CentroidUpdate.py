from geojson import Point as geoPt
from geojson import Polygon as GeoPolygon
from geojson import Feature, FeatureCollection, dump, LineString
import json
from shapely.geometry import Polygon, Point
import random
from sklearn.cluster import KMeans
import numpy as np 
import pandas as pd
# 2Opt for finding path solution 
from py2opt.routefinder import RouteFinder
from numpy.linalg import norm
from itertools import combinations 

# DONE - Import prd-drawn polygon which represents the edge of the body of water. Note Argument must be GEOJSON file containing only polygon lake edge.
def importLakeCords(path):
    with open(path, 'r') as f:
        data = f.read()
    
    lakeStr = json.loads(data)
    coords = lakeStr['features'][0]['geometry']['coordinates'][0]

    return coords

# TODO - Find area of polygon. CAN DO LATER 

# TODO - K  = floor(How many 20m^2 goes into this area?). CAN DO LATER

# DONE IN MAIN FUNCTION - Run K-means clustering on our randomly generated points. 
# Create a numpy array containing the geojson points
# Run Sklearn.KMeans

# DONE IN MAIN FUNCTION - Create GeoJson points of the centroids of each cluster.

# DONE PARTLY IN MAIN FUNCTION - Create distance matrix and run 2-opt to find path.
def euc_dist(pt1, pt2):
    np_pt1 = np.array(pt1)
    np_pt2 = np.array(pt2)

    c = np_pt1 - np_pt2

    return np.linalg.norm(c)

def createDistTable(centroidDict):
    distTable = []
    size = len(centroidDict.keys())
    for x in range(size):
        distTable.append([])
    # Distances are euclidean distance between points 
    for x in centroidDict.keys():
        for y in centroidDict.keys():
            distTable[x].append(euc_dist(centroidDict[x], centroidDict[y]))
    
    return distTable

# TODO - Run TSP(2-opt) algorithm on this graph to find the optimal path.
def cost_change(cost_mat, n1, n2, n3, n4):
    return cost_mat[n1][n3] + cost_mat[n2][n4] - cost_mat[n1][n2] - cost_mat[n3][n4]


def two_opt(route, cost_mat):
    best = route
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route) - 2):
            for j in range(i + 1, len(route)):
                if j - i == 1: continue
                if cost_change(cost_mat, best[i - 1], best[i], best[j - 1], best[j]) < 0:
                    best[i:j] = best[j - 1:i - 1:-1]
                    improved = True
        route = best
    return best

# DONE IN MAIN - Create geojson line string object which represents path around the lake.

# DONE IN MAIN - OUTPUT geojson file containing the first path plan

# DONE IN MAIN - Write csv file containing the randomly generated points and centroid centers, the will be required for running the algorithm again...

def main():
    
    # In theory this data would come from some other class once the boat has made the journey or be system argument
    trashFound = [[-3.161460, 55.952601], [-3.160464, 55.953057], [-3.160613, 55.951984], [-3.160931, 55.952591], [-3.161129, 55.951779], [-3.162361, 55.951572]]

    centroids = pd.read_csv('nStMargarets_centroids.csv').to_numpy()[:,1:]
    rand_pts = pd.read_csv('StMargarets_rand.csv').to_numpy()[:,1:].tolist()
    init_loc = pd.read_csv('StMargarets_initial.csv').to_numpy()[:,1:]

    startingLoc = (init_loc.tolist()[0][0], init_loc.tolist()[0][1])
    print(startingLoc[0])

    print(init_loc.tolist()[0])
    # Adding the trash
    for x in range(600):
        rand_pts.append(trashFound[x % 5])
    # Convert back to numpy array 
    x_updated = np.array(rand_pts)


    # Task 1 + Make GeoJson polygon from list of pts.
    LakeCords = importLakeCords(
        "C:\\Users\\adamh\\OneDrive - University of Edinburgh\\Year3\\Semester 2\\System design project\\Navigation\\Example lochs\\StMargaretsLochSplit.GEOJSON")

    geojsonLakePts = [[]]
    for cord in LakeCords: 
        geojsonLakePts[0].append((cord[0], cord[1]))

    # GeoJson lake as polygon
    geoJsonLakePoly = GeoPolygon(geojsonLakePts)

    # Task 2
    PointsInLake = x_updated.tolist()
    # Convert to GEOJSON point
    ListGeoJsonPts = []
    for pts in PointsInLake:
        ListGeoJsonPts.append(geoPt((pts[0], pts[1])))
    

    # Running KMeans on new data set with trash.
    kmeans = KMeans(n_clusters = 10, random_state = 0, max_iter = 1000, init = centroids, n_init=1).fit(x_updated)

    # Task 6 - Get centroids and create geojson points from them...
    centroids = kmeans.cluster_centers_
    # Creating geojson points
    geojsonCentroidList = []
    centroidList = centroids.tolist()
    for centroid in centroidList:
        geojsonCentroidList.append(geoPt((centroid[0], centroid[1])))

    # Task 7 - Dictionary to identify each centroid because networkx lib is shit 
    counter = 0
    centroid_dict = {}
    for c in centroidList:
        centroid_dict[counter] = c
        counter +=1

    names = []
    for num in centroid_dict.keys():
        names.append(num)
    table = createDistTable(centroid_dict)
    
    #route_finder = RouteFinder(table, names, iterations=20)
    # Route we will take on journey 1. 
    #best_distance, best_route = route_finder.solve()
    best_route = two_opt(names, table)

    print("The best route for EdVarka to take is: ", best_route)

    # We now want to make GeoJson line string representing the path EdVarka should be taking 
    linestrList = []
    linestrList.append(startingLoc)
    for node in best_route:
        linestrList.append((centroid_dict[int(node)][0], centroid_dict[int(node)][1]))
    linestrGeoJson = GeoPolygon([linestrList])
    linestrList.append(startingLoc)

    # For testing we write our list of randomly generated points and lake polygon to GeoJson file.
    features = []
    features.append(Feature(geometry=geoJsonLakePoly))
    # Adding line string path 
    features.append(Feature(geometry=linestrGeoJson, properties={'fill-opacity':0.0}))

    #Add starting location as red marker
    pt = geoPt((startingLoc[0], startingLoc[1]))
    features.append(Feature(geometry=pt, properties={'marker-color':'#cc0000'}))

    #KEEP THIS TO SHOW THE MARKERS WHICH INITIALISE THE CENTROIDS
    #for pt in listGeoJsonPts:
    #   features.append(Feature(geometry=pt))

    for pts in geojsonCentroidList:
        features.append(Feature(geometry=pts, properties={'marker-color':'#0000ff'}))

    # Trash on itteration 2
    for trash in [0,1,2]:
        pt = geoPt((trashFound[trash][0], trashFound[trash][1]))
        features.append(Feature(geometry=pt, properties={'marker-color':'#ffa500'}))

    # Trash on itteration 3
    for x in [3,4,5]:
        pt = geoPt((trashFound[x][0], trashFound[x][1]))
        features.append(Feature(geometry=pt, properties={'marker-color':'#00ff00'}))

    feature_collection = FeatureCollection(features)

    # Standard file writing for our geojson
    f = open('nthJourneyStMargaretsLake.geojson', 'w')
    with open('nthJourneyStMargaretsLake.geojson', 'w') as f:
        f.seek(0)
        dump(feature_collection, f)

    # Task 10 - Standar file writing for saving our centroid centers, data set X and exact path taken(Not needed as path probably will change).
    random_df = pd.DataFrame(data = x_updated)
    centroids_df = pd.DataFrame(data = centroids, columns=['lng', 'lat'])
    # Add pandas df of starting loc...
    cordStartLoc = np.array([startingLoc[0], startingLoc[1]]).reshape(1,2)
    initial_df = pd.DataFrame(data = cordStartLoc)

    #random_df.to_csv('StMargarets_rand.csv')
    centroids_df.to_csv('nStMargarets_centroids.csv')
    #initial_df.to_csv('StMargarets_initial.csv')


if __name__ == '__main__':
    main()