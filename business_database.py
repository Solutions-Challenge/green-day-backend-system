from flask import Flask, json, request, jsonify, Blueprint
from auth_server import db

from google_storage_functions import *
from user_database import verify_user, user_exists
from location_database import extract_location_data
import json

bus_data = Blueprint("bus_data", __name__)

"""
    INPUT:
    latitude: X coordinate
    longitude: Y coordinate
    id_token: JWT token authenticating the business
    business_data: Textified Json with business data

    PURPOSE:
    Adds a business with picture to location database

    Notes:
    This adds a county entry if it exists and the database will query by level 2 Admin zone ~ County Equivalents 

"""
@bus_data.route('/database/createBusinessEntry', methods=['POST'])
def create_business_entry():
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        input_data = json.loads(request.form['data'].strip())

        # Verify the user 
        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

        # This is the expected data we want add more necessary
        business_data = {
            "name": None,
            "pictureURL": None,
            "category": None,
            "recyclingTypes": None,
            "location": None,
            "phone": None,
            "website": None,
            "lat": None,
            "lng": None
        }

        # We input intersection of the accepted data and the data we recieved
        for x in set(input_data).intersection(set(business_data.keys())):
            business_data[x] = input_data[x]

        if (business_data['lat'] == None or business_data['lng'] == None):
            return jsonify({"error": "Latitude or longtitude wasn't given"})
        else:
            latitude = business_data['lat']
            longitude = business_data['lng']

        # Gets location data from coordinates
        # If country is valid then continue otherwise return error
        location_data = extract_location_data(latitude, longitude)
        if location_data == None:
            return jsonify({"error": "Country not found. Coordinates may be invalid"})

        # Get the business ref and check if it exists
        business_ref = db.collection("business").document(uid)
        user_doc = business_ref.get()
        if user_doc.exists:
            return jsonify({"error": "User already exists"})

        # Extracts location data and assigns them
        location_key = "{}_{}".format(location_data['admin2'], location_data['admin1'])
        country = location_data['country'].lower()

        """# Checks if country in coordinates matches given country
        if country.lower != (country.lower if business_data['country'] == None else business_data['country'].lower):
            return jsonify({"error": "Country extracted from coordinates doesn't match given country"})"""

        # Gets the level 2 admin zone and sets the key to the level 2 admin zone
        location_ref = db.collection(u'location_data').document(
            country).collection("admin2").document(location_key)

        location_ref.set({
            "latitude": latitude,
            "longitude": longitude,
            "business_ref": business_ref
        })
        
        business_data['location_ref'] = location_ref

        business_ref.set(business_data)

        return jsonify({'success': "Business added!"})
    else:
        return jsonify({'error': 'not POST request'})


@bus_data.route('/database/updateBusinessEntry', methods=['POST'])
def update_business_entry():
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        input_data = json.loads(request.form['data'].strip())

        # Verify the user 
        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

        business_ref = db.collection('business').document(uid)

        business = business_ref.get()
        if not business.exists:
            return jsonify({'error': "Business doesn't exist"})

        business_data = business.to_dict()

        if business_data.pop('location_ref', True):
            return jsonify({'error': 'Critical error there is no location ref to this location'})

        changed = dict()
        # We input intersection of the accepted data and the data we recieved
        accepted_inputted = set(input_data).intersection(set(business_data.keys()))
        for x in accepted_inputted:
            if business_data[x] != input_data[x]:
                business_data[x] = input_data[x]
                changed[x] = input_data[x]

        business_ref.set(business_data)

        return jsonify({"success": {
            "changed items": changed
        }})
    else:
        return jsonify({'error': 'not POST request'})

@bus_data.route('/database/deleteBusiness', methods=['DELETE'])
def delete_business_entry():
    if request.method == "DELETE":
        id_token = request.form['id_token'].strip()
        
        # Verify the user 
        user = verify_user(id_token)
        if not user:
            return jsonify({"error": "Auth token is invalid"})
        
        uid = user['uid']
        
        business_ref = db.collection('business').document(uid)

        business = business_ref.get()
        if not business.exists:
            return jsonify({'error': "Business doesn't exist"})

        business_data = business.to_dict()

        try:
            location_ref = business_data['location_ref']
            location_ref.delete()
        except:
            pass
        
        business_ref.delete()

        return jsonify({'success': 'Business deleted'})
    else:
        return jsonify({'error': 'not DELETE request'})

@bus_data.route('/database/getBusinessData', methods=['POST'])
def get_business_data():
    if request.method == 'POST':
        uid = request.form['uid'].strip()

        business_ref = db.collection('business').document(uid)

        business = business_ref.get()
        if not business.exists:
            return jsonify({'error': "Business doesn't exist"})

        business_data = business.to_dict()

        if business_data.pop('location_ref', False) == False:
            return jsonify({'error': 'Critical error there is no location ref to this location'})
        
        return jsonify({"success":  business_data})
    else:
        return jsonify({'error': 'not POST request'})
