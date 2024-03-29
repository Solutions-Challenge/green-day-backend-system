from auth_server import db
from flask import Flask, json, request, jsonify, Blueprint
from google_storage_functions import *
from user_database import verify_user
from firebase_admin import auth
import base64

userimg_data = Blueprint("userimg_data", __name__)

@userimg_data.route('/database/addImg', methods=['POST'])
def add_picture():
    """
    // THIS DOESN'T CHECK IF DATA IS CORRECTLY FORMATTED
    INPUT:
    'id_token': JWT token given by user
    'data': The json containing the photo meta data
    'image_base64': The raw base 64 code of the image

    PURPOSE:
    Adds a picture to user entry in firebase and google cloud storage along with metadata

    """
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        data = json.loads(request.form['data'].strip())
        image = request.form['image_base64'].strip()

        image = base64.b64decode((image))

        # Verify auth token and find user in database
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})

        uid = user["uid"]
        image_id = data['key']

        bucket_name = 'greenday-user-photos'
        if blob_exists(bucket_name, image_id):
            return jsonify({"error": "Photo already exists within database"})

        # users/user/photos/image_id/metadata
        db.collection('users').document(uid).collection(
            "photos").document(image_id).set(data)

        string = upload_blob_from_memory(bucket_name, image, image_id)

        return jsonify({"success": string})
    else:
        return jsonify({'error': 'not POST request'})

@userimg_data.route('/database/getImg', methods=['POST'])
def get_picture():
    """
    INPUT:
    'id_token': JWT token given by user
    'image_id': The name of the photo

    PURPOSE:
    Returns the base64 encoding of photo and json with metadata

    """
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()

        # Verify auth token and find user in database
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        # users/user/photos/image_id/metadata
        docref = db.collection('users').document(
            uid).collection("photos").document(image_id)

        # Check if image_id entry exists
        doc = docref.get()
        if not doc.exists:
            return jsonify({'error': "Picture doesn't exist for this user"})

        # Generates a url to the photo from Google Cloud Storage
        picture = generate_download_signed_url_v4(
            'greenday-user-photos', image_id)

        return jsonify({
            "success": {
                "photo": str(picture),
                "photo-meta": doc.to_dict()
            }
        })
    else:
        return jsonify({'error': 'not POST request'})

@userimg_data.route('/database/getImgKeys', methods=['POST'])
def get_image_keys():
    """
    INPUT:
    'id_token': JWT token given by user

    PURPOSE:
    Returns all image_ids associated with user account

    """
    if request.method == "POST":
        id_token = request.form['id_token'].strip()

        # Verify our auth token and find uid to put photo data into database
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        # /users/user_id/photos
        docref = db.collection('users').document(uid).collection("photos")
        docs = docref.stream()

        # Returns every photo_id the user owns 
        array = []
        for doc in docs:
            array.append(doc.id)

        return jsonify({'success': array})
    else:
        return jsonify({'error': 'not POST request'})

@userimg_data.route('/database/deleteImg', methods=['DELETE'])
def delete_picture():
    """
    //THIS DOESNT CHECK IF DATA IS VALID OR NOT
    INPUT:
    'id_token': JWT token given by user 
    'image_id': The name of the photo
    'data': The bounding box data 

    PURPOSE:
    Deletes a picture from user database entry and user photos if photo is associated with account

    """
    if request.method == 'DELETE':
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()

        # Validates the user id token
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        # /users/user_id/photos/image_id
        photo_ref = db.collection('users').document(
            uid).collection("photos").document(image_id)

        # Validates the photos existence
        photo = photo_ref.get()
        if not photo.exists:
            return jsonify({"error": "Picture doesn't exist or user doesn't own photo"})

        # Deletes the photo reference from Firestore and Google Cloud Storage
        photo_ref.delete()
        delete_blob("greenday-user-photos", image_id)

        return jsonify({'success': "Picture was deleted"})
    else:
        return jsonify({'error': 'not DELETE request'})

@userimg_data.route('/database/addItem', methods=['POST'])
def add_item():
    """
    !THIS FUNCTION IS DEPRECIATED DO NOT USE 
    //THIS DOESNT CHECK IF DATA IS VALID OR NOT
    INPUT:
    'id_token': JWT token given by user 
    'image_id': The name of the photo
    'data': The bounding box data 

    PURPOSE:
    This adds a json to the MULTI array which holds data for bounding boxes

    """
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()
        data = json.loads(request.form['data'].strip())

        # Verify our auth token and find uid to put photo data into database
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        # Gets photo by
        photo_ref = db.collection('users').document(
            uid).collection("photos").document(image_id)
        doc = photo_ref.get()

        if not doc.exists:
            return jsonify({"error": "Picture doesn't exist or user doesn't own photo"})

        new_json = doc.to_dict()
        new_json['multi'].append(data)
        photo_ref.set(new_json)

        return jsonify({'success': "Item was added"})
    else:
        return jsonify({'error': 'not GET request'})
