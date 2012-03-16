#!/usr/bin/env python
import os
import sys
import csv
import math
from PIL import Image, ImageDraw

# file format info
LATITUDE_COLUMN = 72
LONGITUDE_COLUMN = 73
race_codes = { 'SE_T054_001' : 'Total population',
          'SE_T054_002' : 'Total population: White alone',
          'SE_T054_003' : 'Total population: Black or African American alone',
          'SE_T054_004' : 'Total population: American Indian and Alaska Native alone',
          'SE_T054_005' : 'Total population: Asian alone',
          'SE_T054_006' : 'Total population: Native Hawaiian and Other Pacific Islander alone',
          'SE_T054_007' : 'Total population: Some Other Race alone',
          'SE_T054_008' : 'Total population: Two or More Races' }


def distance_on_spherical_earth(lat1, long1, lat2, long2):

    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
        
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
        
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
        
    # Compute spherical distance from spherical coordinates.
        
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )

    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc * 6378100

# some maps (of the earth) use mercator projection, this is an "Okay Projection" that I made up.
# maybe it corresponds to some real accepted projection.
def ok_projection_aspect(left, right, top, bottom):
   degree_width  = (right - left)
   degree_height = (top - bottom)

   center_x = left + (right - left) / 2.0
   center_y = bottom + (top - bottom) / 2.0

   meter_width  = distance_on_spherical_earth(center_y, left, center_y, right)
   meter_height = distance_on_spherical_earth(bottom, center_x, top, center_x)

   return meter_width / meter_height


class GeoRaceData:
   races = {}
   samples = []
   header = []

   min_lat = None
   max_lat = None
   min_lng = None
   max_lng = None

   def __init__(self, socialexplorer_dot_com_csv_path):

      csv_file = file(socialexplorer_dot_com_csv_path, "r")
      race_csv = csv.reader(csv_file, delimiter=',', quotechar='"')
      self.header = None

      for line in race_csv:
	 if self.header == None:
	    self.header = line
	    for race_code in race_codes:
	       new_race = {}
	       new_race['code'] = race_code
	       new_race['title'] = race_codes[race_code]
	       new_race['csv_column'] = self.header.index(race_code)
	       self.races[race_code] = new_race
	 else:
	    latitude =  float(line[LATITUDE_COLUMN])
	    longitude = float(line[LONGITUDE_COLUMN])
            if self.min_lat == None:
	       self.min_lat = latitude
	       self.max_lat = latitude
	       self.min_lng = longitude
	       self.max_lng = longitude
            else:
	       self.min_lat = min(self.min_lat, latitude)
	       self.max_lat = max(self.max_lat, latitude)
	       self.min_lng = min(self.min_lng, longitude)
	       self.max_lng = max(self.max_lng, longitude)
	    sample = {}
	    sample['latlng'] = (latitude, longitude)
	    dominant_race_code = None
	    dominant_race_count = 0
	    for race_code in self.races:
	       race = self.races[race_code]
	       sample[race_code] = int(line[race['csv_column']])
	       if dominant_race_count < sample[race_code]:
		  dominant_race_count = sample[race_code]
		  dominant_race_code = race_code
	    sample['dominant_race_code'] = dominant_race_code
	    self.samples.append(sample)

   def degree_width(self):
      return self.max_lng - self.min_lng;

   def degree_height(self):
      return self.max_lat - self.min_lat;

   def latlng_to_fractional(self, latlng):
      return ( (latlng[1] - self.min_lng) / self.degree_width(),
               (latlng[0] - self.min_lat) / self.degree_height() )
   
   def get_image(self, width=512):
      aspect = ok_projection_aspect(self.min_lng, self.max_lng, self.max_lat, self.min_lat)
      height = int(float(width) / aspect)
      image = Image.new('RGBA', (width, height))
      draw = ImageDraw.Draw(image)

      for sample in self.samples:
         fractional_location = self.latlng_to_fractional(sample['latlng'])
         x = fractional_location[0] * width
         y = height - fractional_location[1] * height
         draw.point((x, y))

      return image
      
# if this script is run by itself (not included from another python file)
if __name__ == "__main__":
   if len(sys.argv) < 2:
      print "Usage: " + sys.argv[0] + " geo_race_csv_from_http://www.socialexplorer.com/"
      sys.exit(0)

   sys.stderr.write("Parsing CSV...")
   geo_race_data = GeoRaceData(sys.argv[1])
   sys.stderr.write(" Done.\n")

   image = geo_race_data.get_image()
   image.save("plot.jpg")
   print "Saved plot.jpg"
