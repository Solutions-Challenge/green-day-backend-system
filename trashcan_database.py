from main import app, db
from flask import request, jsonify
import base64

from google_storage_functions import *
from user_database import verify_user, user_exists
from location_database import extract_location_data

"""
    INPUT:
    latitude: X coordinate
    longitude: Y coordinate

    PURPOSE:
    Adds a trashcan with picture to location database

    Notes:
    admin2 is a level 2 admin zone which is US county or it's equivalent [100 sq mi, 40000sq mi]
    admin1 is a level 1 admin zone which is a US state or US state equivalent. Size is too large to be relavant.
    postcode: Is like a universal zipcode for each country [~1 sq mi, 10000 sq mi] Most are on the smaller side and the largest ones are the least populated
    country: Is self explanatory 
    locality: A town or city inside a county essentially a level 3 admin zone [1 sq mi, 100 sq mi] 
    
    Relative Size
    postcode ~ locality < admin2 < admin1 < country
"""


@app.route('/database/createTrashcanCoords', methods=['POST'])
def create_trashcan_coords():
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        image = request.form['image_base64'].strip()
        image = base64.b64decode((image))

        image_id = request.form['image_id'].strip()
        latitude = request.form['latitude'].strip()
        longitude = request.form['longitude'].strip()
        recycling_types = request.form['recycling_types'].strip().split(' ')
        date = request.form['date_taken'].strip()

        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

        # Gets location data from coordinates
        # If country is valid then continue otherwise return error
        location_data = extract_location_data(latitude, longitude)
        if location_data == None:
            return jsonify({"error": "Country not found. Coordinates may be invalid"})

        if blob_exists("trashcan_images", image_id):
            return jsonify({"error": "Photo ID in use"})

        # Get the user ref and check if it exists
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        if not user_doc.exists:
            return jsonify({"error": "User does not exist"})

        # Refers to trashcan database where photo id and othe refs are stored
        trashcanref = db.collection('trashcans').document(image_id)

        # Extracts location data and assigns them
        location_key = location_data['postcode']
        country = location_data['country'].lower()

        if location_key == None:
            location_key = location_data['admin2'].lower()

        # Gets the level 2 admin zone and sets the key to zip code or level 2 admin zone name
        location_ref = db.collection(u'location_data').document(
            country).collection("postal_codes").document(location_key)
        # Helps me know where the postal code is

        # Sets the trashcan location data
        trashcan_location_ref = location_ref.collection(
            "trashcans").document(image_id)
        trashcan_location_ref.set({
            'latitude': latitude,
            'longitude': longitude,
            'ref': trashcanref
        })

        # Where the user owned trashcan ref exists
        user_trashcans_ref = db.collection('users').document(
            uid).collection('owned_trashcans').document(image_id)
        user_trashcans_ref.set({
            'user_ref': trashcanref
        })

        # Sets trashcan data
        trashcanref.set({
            'user': uid,
            'image_id': image_id,
            'location_ref': trashcan_location_ref,
            'user_ref': user_trashcans_ref,
            'recycling_types': recycling_types,
            'date_taken': date
        })

        string = upload_blob_from_memory("trashcan_images", image, image_id)

        return jsonify({'success': string})
    else:
        return jsonify({'error': 'not POST request'})


"""
    INPUT:
    id_token: The JWT token given by the user

    PURPOSE:
    Gets all trashcans that were taken by the user

    Output:
    The image_ids of every trashcan the user owns
"""


@app.route('/database/getUserOwnedTrashcans', methods=['POST'])
def get_trashcan_keys():
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()

        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

        if not user_exists(uid):
            return jsonify({"error": "user entry not created in database"})

        trashcans = db.collection('users').document(
            uid).collection('owned_trashcans').stream()
        trashcan_ids = []

        for trashcan in trashcans:
            trashcan_ids.append(trashcan.id)

        return jsonify({"success": trashcan_ids})
    else:
        return jsonify({"error": "not POST request"})


"""
    INPUT:
    id_token: JWT token 
    image_id: Name of trashcan

    PURPOSE:
    Deletes trashcan from location, user, and trashcan, and photo databases
"""


@app.route('/database/deleteTrashcan', methods=['DELETE'])
def delete_trashcan():
    if request.method == 'DELETE':
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()
        user = verify_user(id_token)

        if (user == False):
            return jsonify({"error": "Auth token is invalid"})

        doc_ref = db.collection('trashcans').document(image_id)

        data = doc_ref.get()

        if not data.exists:
            return jsonify({"error:": "Data does not exist"})

        data = data.to_dict()
        if user['uid'] != data['user']:
            return jsonify({"error:": "User doesn't own trashcan"})

        loc_ref = data['location_ref']
        user_ref = data['user_ref']

        loc_ref.delete()
        user_ref.delete()
        doc_ref.delete()
        delete_blob('trashcan_images', image_id)
        return jsonify({"success": '{} deleted'.format(image_id)})
    else:
        return jsonify({"error": "not DELETE request"})


"""
    INPUT:
    id_token: JWT token 
    image_id: Name of trashcan

    PURPOSE:
    Gets trashcan from trashcan database if user owns it
"""


@app.route('/database/getTrashcan', methods=['POST'])
def get_trashcan():
    if request.method == 'POST':
        image_id = request.form['image_id'].strip()
        doc_ref = db.collection('trashcans').document(image_id)

        data = doc_ref.get()

        if not data.exists:
            return jsonify({"error": "Data does not exist"})

        data = data.to_dict()

        loc_ref = data['location_ref']
        loc_ref_data = loc_ref.get().to_dict()

        latitude = loc_ref_data['latitude']
        longitude = loc_ref_data['longitude']
        recycling_types = data['recycling_types']
        date = data['date_taken']
        return jsonify({
            "success": {
                'latitude': latitude,
                'longitude': longitude,
                'recycling_types': recycling_types,
                'date_taken': date,
                'image_id': image_id
            }
        })
    else:
        return jsonify({"error": "not POST request"})


"""
    INPUT:
    id_token: JWT token 
    image_id: Name of trashcan

    PURPOSE:
    Gets trashcan from trashcan database if user owns it
"""


@app.route('/database/getTrashcanImage', methods=['POST'])
def get_trashcan_image():
    if request.method == 'POST':
        image_id = request.form['image_id'].strip()
        doc_ref = db.collection('trashcans').document(image_id)

        data = doc_ref.get()

        if not data.exists:
            return jsonify({"error": "Data does not exist"})

        image_url = generate_download_signed_url_v4(
            'trashcan_images', image_id)

        return jsonify({
            "success": {
                'image_url': str(image_url)
            }
        })
    else:
        return jsonify({"error": "not POST request"})


"""
    INPUT:
    latitude: 
    longitude:

    PURPOSE:
    Querys known trashcans by coordinates
"""


@app.route('/database/queryTrashcanLocation', methods=['POST'])
def query_trashcan_location():
    if request.method == 'POST':
        latitude = request.form['latitude'].strip()
        longitude = request.form['longitude'].strip()
        radius = 0.03
        # So I don't have to calculate that pesky square root
        radius *= radius

        location_data = extract_location_data(latitude, longitude)
        if location_data == None:
            return jsonify({"error": "Country not found. Coordinates may be invalid"})

        postcode = location_data['postcode']
        country = location_data['country']
        trashcan_list = db.collection('location_data').document(country).collection(
            'postal_codes').document(postcode).collection("trashcans").stream()
        trashcans = []
        for trashcan in trashcan_list:
            loc_data = trashcan.to_dict()
            x1 = float(latitude)
            x2 = float(loc_data['latitude'])
            y1 = float(longitude)
            y2 = float(loc_data['longitude'])
            ys = y2 - y1
            xs = x2 - x1
            if radius < (ys * ys + xs * xs):
                continue

            trashcans.append(trashcan.id)
            #trash_ref = trashcan.to_dict()['ref'].get().to_dict()

        return jsonify({"Success": trashcans})
    else:
        return jsonify({"error": "not POST request"})
