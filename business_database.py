from main import app, db
from flask import Flask, json, request, jsonify

from google_storage_functions import *
from user_database import verify_user, user_exists
from location_database import extract_location_data
import json

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


@app.route('/database/createBusinessEntry', methods=['POST'])
def create_business_entry():
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        input_data = json.loads(request.form['data'].strip())

        # This is the expected data we want add more necessary
        business_data = {
            'name': None,
            'city': None,
            'full_address': None,
            'latitude': None,
            'longitude': None,
            'phone': None,
            'recycledType': None,
            'time': None,
            'websiteURL': None,
            'zipcode': None
        }

        # We input intersection of the accepted data and the data we recieved
        for x in set(input_data).intersection(set(business_data.keys())):
            business_data[x] = input_data[x]

        if (business_data['latitude'] == None or business_data['longitude'] == None):
            return jsonify({"error": "Latitude or longtitude wasn't given"})
        else:
            latitude = business_data['latitude']
            longitude = business_data['longitude']

        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

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
        location_key = location_data['admin2']
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

        business_ref.set(business_data)

        return jsonify({'success': "Business added!"})
    else:
        return jsonify({'error': 'not POST request'})


"""@app.route('/database/updateBusinessEntry', methods=['POST'])
def update_business_entry():
    id_token = request.form['id_token'].strip()
    input_data = json.loads(request.form['data'].strip())

    business_data = {
        'name': None,
        'city': None,
        'full_address': None,
        'latitude': None,
        'longitude': None,
        'phone': None,
        'recycledType': None,
        'time': None,
        'websiteURL': None,
        'zipcode': None
    }

    for x in set(input_data).intersection(set(business_data.keys())):
        business_data[x] = input_data[x]"""
