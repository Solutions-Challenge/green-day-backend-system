from flask import request, jsonify, Blueprint
from auth_server import gmaps
loc_data = Blueprint('loc_data', __name__)

def most_frequent(List):
    if List == []:
        return None
    counter = 0
    num = List[0]

    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency > counter):
            counter = curr_frequency
            num = i

    return num

def extract_location_data(latitude, longitude):
    """
    ARGUMENTS:
    latitude:string = X coordinate  
    longitude:string = Y coordinate
    OUTPUT:
    {
        "admin2": level 2 admin zone if exists else post-code else admin 1 zone,
        "admin1": level 1 admin zone,
        "postcode": the global postal code of coordinates,
        "country": country
        "locality": Town or city equivalent
    }

    PURPOSE:
    Returns a normalized global address system so we can effectively partition our data
    """
    addresses = gmaps.reverse_geocode((latitude, longitude))

    sub1 = []
    sub2 = []
    admin1 = []
    admin2 = []
    code = []
    country = []
    locality = []

    for address in addresses:
        for t in address['address_components']:
            if "sublocality_level_1" in t['types']:
                #print("sub1", t['long_name'])
                sub1.append(t['long_name'])
            if "sublocality_level_2" in t['types']:
                #print('sub2', t['long_name'])
                sub2.append(t['long_name'])
            if "administrative_area_level_2" in t['types']:
                #print('admin2', t['long_name'])
                admin2.append(t['long_name'])
            if "administrative_area_level_1" in t['types']:
                #print('admin1', t['long_name'])
                admin1.append(t['long_name'])
            if "country" in t['types']:
                #print('country', t['long_name'])
                country.append(t['long_name'])
            if "postal_code" in t['types']:
                #print('code', t['long_name'])
                code.append(t['long_name'])
            if "locality" in t['types']:
                #print('code', t['long_name'])
                locality.append(t['long_name'])

    sub1 = most_frequent(sub1)
    sub2 = most_frequent(sub2)
    admin1 = most_frequent(admin1)
    admin2 = most_frequent(admin2)
    country = most_frequent(country)
    code = most_frequent(code)
    locality = most_frequent(locality)
    if country == None:
        return None

    if admin2 == None:
        admin2 = sub2
    if sub2 == None:
        admin2 = locality

    return {
        "admin2": admin2.lower() if admin2 != None else sub2.lower(),
        "admin1": admin1.lower() if admin1 != None else sub1.lower(),
        "postcode": code.lower(),
        "country": country.lower(),
        "locality": locality.lower()
    }

"""
    INPUT:
    latitude: X coordinate
    longitude: Y coordinate

    PURPOSE:
    Returns a geolocation based on coordinates

    Notes:
    admin2 is a level 2 admin zone which is US county or it's equivalent [100 sq mi, 40000sq mi]
    admin1 is a level 1 admin zone which is a US state or US state equivalent. Size is too large to be relavant.
    postcode: Is like a universal zipcode for each country [~1 sq mi, 10000 sq mi] Most are on the smaller side and the largest ones are the least populated
    country: Is self explanatory 
    locality: A town or city inside a county essentially a level 3 admin zone [1 sq mi, 100 sq mi] 
    
    Relative Size
    postcode ~ locality < admin2 < admin1 < counttry
"""
@loc_data.route('/location/reverseGeolocation', methods=['POST'])
def reverse_geolocation():
    latitude = float(request.form['latitude'].strip())
    longitude = float(request.form['longitude'].strip())
    geolocation = gmaps.reverse_geocode((latitude, longitude))

    return jsonify({"success": geolocation})
