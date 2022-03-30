from flask import Flask, json, request, jsonify, Blueprint
from auth_server import db

from google_storage_functions import *
from user_database import verify_user
from location_database import extract_location_data
import json
import base64 

bus_data = Blueprint("bus_data", __name__)


def business_exists(user_id):
    """
    INPUT:
    user_id: The user id given by Firebase Auth

    PURPOSE:
    The validates the existence of the user id in Firestore
    """
    user_ref = db.collection('business').document(user_id)
    user_exist = user_ref.get()

    return user_exist



@bus_data.route('/database/createBusinessEntry', methods=['POST'])
def create_business_entry():
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
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        input_data = json.loads(request.form['data'].strip())

        # Verify the user 
        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

        # This is the expected data given by our website we can add more as necessary
        business_data = {
            "name": None,
            "imageid": None,
            "category": None,
            "recyclingTypes": None,
            "location": None,
            "street": None,
            "city": None,
            "county": None,
            "state": None,
            "zipcode": None,
            "phone": None,
            "website": None,
            "timeAvailability": None,
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

        # Gets the level 2 admin zone and sets the key to the level 2 admin zone
        # /location_data/country/admin2/location_ley/businesses/user_uid
        location_ref = db.collection(u'location_data').document(
            country).collection("admin2").document(location_key).collection("businesses").document(uid)

        location_ref.set({
            "latitude": latitude,
            "longitude": longitude,
            "business_ref": business_ref
        })
        
        # Adds a reference to the business in our locality partitioning system
        business_data['location_ref'] = location_ref
        business_ref.set(business_data)

        return jsonify({'success': "Business added!"})
    else:
        return jsonify({'error': 'not POST request'})

@bus_data.route('/database/updateBusinessEntry', methods=['POST'])
def update_business_entry():
    """
    INPUT:
    id_token: JWT token authenticating the business
    data: A json containing the tokens we want to update

    PURPOSE:
    Updates the values if a business wants to change their information

    NOTES:
    This will not update the location reference to a business 
    So if a business updates it's location it won't update in our partitioning system

    """
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        input_data = json.loads(request.form['data'].strip())

        # Verify the user 
        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']   

        # /business/business_id
        business_ref = db.collection('business').document(uid)

        # Verifies if the business exists
        business = business_ref.get()
        if not business.exists:
            return jsonify({'error': "Business doesn't exist"})

        # Extracts the data from the business reference
        business_data = business.to_dict()

        # Checks if the location ref exists
        # If it doesn't the business can't be found
        if "location_ref" not in business_data.keys():
            return jsonify({'error': 'Critical error there is no location ref to this location'})

        # We input intersection of the accepted data and the data we recieved
        inputted_business_data = set(business_data.keys())
        changed = dict()
        accepted_inputted = set(input_data).intersection(inputted_business_data)
        
        for x in accepted_inputted:
            if business_data[x] != input_data[x] and input_data[x] != None:
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
    """
    INPUT:
    id_token: JWT token authenticating the business

    PURPOSE:
    Deletes a business from our database
    """
    if request.method == "DELETE":
        id_token = request.form['id_token'].strip()
        
        # Verify the user 
        user = verify_user(id_token)
        if not user:
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']
        
        # /business/business_id 
        business_ref = db.collection('business').document(uid)

        # Verifies the business's existence
        business = business_ref.get()
        if not business.exists:
            return jsonify({'error': "Business doesn't exist"})

        business_data = business.to_dict()

        # Since the location reference might not always exist for incorrectly created businesses
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
    """
    INPUT:
    uid: A unique identifier for the business

    PURPOSE:
    Returns all data relevant to queried business
    """
    if request.method == 'POST':
        uid = request.form['uid'].strip()

        # /business/uid
        business_ref = db.collection('business').document(uid)

        # Verifies the business existence
        business = business_ref.get()
        if not business.exists:
            return jsonify({'error': "Business doesn't exist"})

        business_data = business.to_dict()

        # We pop this because we don't want to show the location reference
        if business_data.pop('location_ref', False) == False:
            return jsonify({'error': 'There is no location ref to this location'})
        
        return jsonify({"success":  business_data})
    else:
        return jsonify({'error': 'not POST request'})


@bus_data.route('/database/queryBusiness', methods=['POST'])
def query_business_ids():
    """
    INPUT:
    latitude: 
    longitude:

    PURPOSE:
    Returns all business ids in a certain admin2 zone which are county or county equivalents
    """
    if request.method == 'POST':
        latitude = float(request.form['latitude'].strip())
        longitude = float(request.form['longitude'].strip())

        # Returns location data for a certain latitude and longitude
        location_data = extract_location_data(latitude, longitude)

        # Queries the location data based on our database partitioning
        country = location_data['country']
        admin2 = "{}_{}".format(location_data['admin2'], location_data['admin1'])

        # /location_data/country/admin2/admin2_zone/businesses
        business_locations = db.collection('location_data').document(country).collection('admin2').document(admin2).collection('businesses')

        business_ids = []
        for business in business_locations.stream():
            business_ids.append(business.id)

        return jsonify({"success":  business_ids})
    else:
        return jsonify({'error': 'not POST request'})

@bus_data.route('/database/addBusinessImage', methods=['POST'])
def add_business_image():
    """
    INPUT:
    id_token: JWT token authenticating the business
    image_id: A unique name for the image
    image_base64: A base64 encoded image we want to add to the database

    PURPOSE:
    Returns all business ids in a certain admin2 zone which are county or county equivalents
    """
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()
        image = request.form['image_base64'].strip()
        image = base64.b64decode((image))

        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']   

        if not business_exists(uid):
            return jsonify({"error": "User doesn't exist"})

        if blob_exists("trashcan_images", image_id):
            return jsonify({"error": "Photo ID in use"})

        image_ref = db.collection("business").document(uid).collection("images").document(image_id)
        image_ref.set({'image_id': image_id})

        upload_blob_from_memory("greenday-business-images", image, image_id)

        return jsonify({"success": "Added image"})
    else:
        return jsonify({'error': 'not POST request'})

@bus_data.route('/database/getBusinessImages', methods=['POST'])
def get_business_images():
    """
    INPUT:
    uid: A unique identifier for a business

    PURPOSE:
    Returns a photo urls associated with a certain business
    """
    if request.method == 'POST':
        uid = request.form['uid'].strip()

        if not business_exists(uid):
            return jsonify({"error": "User doesn't exist"})
    
        business_image_stream = db.collection("business").document(uid).collection("images")

        image_urls = []
        for photo in business_image_stream.stream():
            image_urls.append(generate_download_signed_url_v4("greenday-business-images", photo.id))

        return jsonify({"success": image_urls})
    else:
        return jsonify({'error': 'not POST request'})

@bus_data.route('/database/deleteBusinessImages', methods=['DELETE'])
def delete_business_images():
    """
    INPUT:
    id_token: JWT token authenticating the business
    image_ids: A json containing a list of image_ids the business wants to delete

    PURPOSE:
    Deletes images associated with a business 
    """
    if request.method == 'DELETE':
        id_token = request.form['id_token'].strip()
        image_ids = json.loads(request.form['image_ids'].strip())

        # Verify the user 
        user = verify_user(id_token)
        if not user:
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

        if not business_exists(uid):
            return jsonify({"error": "User doesn't exist"})

        deleted_businesses = []
        for image_id in image_ids['image_ids']:
            # Obtains a reference to the image given the image id
            image_ref = db.collection("business").document(uid).collection("images").document(image_id)

            if image_ref.get().exists:
                deleted_businesses.append(image_id)
                delete_blob('greenday-business-images', image_id)
                
            image_ref.delete()

        return jsonify({"success": deleted_businesses})
    else:
        return jsonify({'error': 'not DELETE request'})
