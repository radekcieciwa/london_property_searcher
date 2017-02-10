import requests
import math
from datetime import datetime, timedelta, date, time
from html import HTML

URL_SEARCH = 'http://api.rightmove.co.uk/api/rent/find'

R_Paddington = 70403
R_Chiswick = 85345
R_Lisson_Grove = 85264
R_Greenwich = 85358
R_MaidaVale = 85443
R_Islington = 87515

# QUERY
C_MAX_PRICE = 1600.0
C_MIN_PRICE = 1000.0
C_LIMIT = 300
C_BEDROOMS = 2
C_DESTINATION_LON = -0.1463241
C_DESTINATION_LAT = 51.5086111

class RM_API(object):
	Requests = requests.session()

	def search(self, min, max, area_id, daid):
		query = { 
			'minPrice': min, 
			'maxPrice': max, 
			'locationIdentifier' : "REGION^" + str(area_id), 
			'locIdAndSearchTypes' : "REGION^" + str(area_id) + "_RENT",
			'daid' : daid,
			'numberOfPropertiesRequested' : C_LIMIT,
			'sortType' : 6,
			'index' : 0,
			'includeLetAgreed' : False,
			'apiApplication' : 'IPHONE',
			'minBedrooms' : C_BEDROOMS,
			'maxBedrooms' : C_BEDROOMS
			}

		r = self.Requests.get(URL_SEARCH, params=query)
		return r.json()

class Property(object):
	price = 0.0
	property_id = 0
	phone = None
	address = None
	summary = None
	photo = None
	lon = 0.0
	lat = 0.0
	posted = 0.0

	def __init__(self, json):
		self.price = json['monthlyRent']
		self.property_id = json['identifier']
		self.phone = json['branch']['telephoneNumbers'][0]['number']
		self.address = json['address']
		self.summary = json['summary']
		self.photo = json['photoLargeThumbnailUrl']
		self.lon = json['longitude']
		self.lat = json['latitude']
		self.sort_date = date = datetime.fromtimestamp(json['sortDate'] / 1e3)

	def __repr__(self):
		return "price: "  + str(self.price) + " GBP ==> " + str(self.property_id) + ", time: " + str(self.time_ago()) + ", " + self.html_link() + "\n"

	def __cmp__(self, other):
		if hasattr(other, 'price'):
			return self.price.__cmp__(other.price)

	def html_link(self):
		return "http://www.rightmove.co.uk/property-to-rent/property-" + str(self.property_id) + ".html"

	def maps_link(self):
		return "https://www.google.pl/maps/@" + str(self.lat) + "," + str(self.lon) + ",16z"

	def time_ago(self):
		delta = datetime.utcnow() - self.sort_date
		return delta.seconds / 60

	def pitagoras_distance_from(self, lon, lat):
		return ((self.lon - lon)**2 +  (self.lat - lat)**2)**.5

	def km_distance_from(self, lon, lat):
		R = 6371 # Radius of the earth in km
		dLat = (lat - self.lat) * (math.pi/180)
  		dLon = (lon - self.lon) * (math.pi/180)
  		a = math.sin(dLat / 2.0) * math.sin(dLat / 2.0) + math.cos(self.lat * (math.pi/180)) * math.cos(lat * (math.pi/180)) *  math.sin(dLon/2) * math.sin(dLon/2)
  		c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  		d = R * c # Distance in km
  		return d

	def rating(self):
		price_rate = (min(self.price, C_MAX_PRICE) - C_MIN_PRICE) / (C_MAX_PRICE - C_MIN_PRICE) # 0-1, 0 is best 
		distance_rate = min(15.0, self.km_distance_from_work()) / 15.0	# 0-1, 0 is best 
		return 100 - int((price_rate + distance_rate) * 100 / 2) # 0 - 100, 100 is best 

	# helpers
	def km_distance_from_work(self):
		return self.km_distance_from(C_DESTINATION_LON, C_DESTINATION_LAT)

	# html
	@staticmethod
	def html_header():
		return ['rating', 'price [GBP]', 'distance [km]', 'site', 'maps', 'address', 'ago [mins]']

	def html_representation(self):
		return [
		str(self.rating()),
		str(self.price), 
		str('%.2f' % round(self.km_distance_from_work(), 2)),
		HTML.link('Source', self.html_link()), 
		HTML.link('Google Maps', self.maps_link()), 
		self.address, 
		str(self.time_ago())
		]

# GLOBAL
def distance_sorting_key(property):
	return property.km_distance_from_work()

def score_sorting_key(property):
	return property.rating()

def price_sorting_key(property):
	return property.price

# MAIN
api = RM_API()
json = api.search(C_MIN_PRICE, C_MAX_PRICE, R_Chiswick, '52E25FC2-0EA4-4B8C-95F3-DA9DD5F40F4B')
properties = [Property(property) for property in json['properties']]
sorted = sorted(sorted(properties, key=price_sorting_key), key=score_sorting_key, reverse=True)

# GENERATE HTML
html_data = [property.html_representation() for property in sorted]
htmlcode = HTML.table(html_data, header_row=Property.html_header())
print htmlcode

