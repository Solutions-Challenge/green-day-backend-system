from __main__ import app, db, auth
from flask import Flask, json, request, jsonify
from google_storage_functions import *
from user_database import verify_user

"""
    // THIS DOESN'T CHECK IF DATA IS CORRECTLY FORMATTED
    /database/addImg [POST]
    INPUT:
    'id_token': JWT token given by user
    'data': The json containing the photo meta data
    'image_base64': The raw base 64 code of the image

    PURPOSE:
    Adds a picture to user entry in firebase and google cloud storage along with metadata

"""
@app.route('/database/addImg', methods=['POST'])
def add_picture():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        data = json.loads(request.form['data'].strip())
        image = request.form['image_base64'].strip()

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


"""
    /database/getImg [POST]
    INPUT:
    'id_token': JWT token given by user
    'image_id': The name of the photo

    PURPOSE:
    Returns the base64 encoding of photo and json with metadata

"""
@app.route('/database/getImg', methods=['POST'])
def get_picture():
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

        picture = download_blob_into_memory(
            'greenday-user-photos', image_id)['picture']

        return jsonify({
            "success": {
                "photo": str(picture),
                "photo-meta": doc.to_dict()
            }
        })
    else:
        return jsonify({'error': 'not POST request'})


"""
    /database/getImgKeys [GET]
    INPUT:
    'id_token': JWT token given by user

    PURPOSE:
    Returns all image_ids associated with user account

"""


@app.route('/database/getImgKeys', methods=['POST'])
def get_image_keys():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        # Verify our auth token and find uid to put photo data into database
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        docref = db.collection('users').document(uid).collection("photos")
        docs = docref.stream()

        array = []
        for doc in docs:
            array.append(doc.id)

        return jsonify({'success': array})
    else:
        return jsonify({'error': 'not POST request'})


"""
    //THIS DOESNT CHECK IF DATA IS VALID OR NOT
    /database/addItem
    INPUT:
    'id_token': JWT token given by user 
    'image_id': The name of the photo
    'data': The bounding box data 

    PURPOSE:
    Deletes a picture from user database entry and user photos if photo is associated with account

"""


@app.route('/database/deleteImg', methods=['DELETE'])
def delete_picture():
    if request.method == 'DELETE':
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()

        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        photo_ref = db.collection('users').document(
            uid).collection("photos").document(image_id)

        photo = photo_ref.get()

        if not photo.exists:
            return jsonify({"error": "Picture doesn't exist or user doesn't own photo"})

        photo_ref.delete()
        delete_blob("greenday-user-photos", image_id)

        return jsonify({'success': "Picture was deleted"})
    else:
        return jsonify({'error': 'not DELETE request'})


"""
    //THIS DOESNT CHECK IF DATA IS VALID OR NOT
    /database/addItem
    INPUT:
    'id_token': JWT token given by user 
    'image_id': The name of the photo
    'data': The bounding box data 

    PURPOSE:
    This adds a json to the MULTI array which holds data for bounding boxes

"""
@app.route('/database/addItem', methods=['POST'])
def add_item():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()
        data = json.loads(request.form['data'].strip())

        print(data)
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

