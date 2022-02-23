from start import app, db, auth
from flask import request, jsonify
from google_storage_functions import *


def user_exists(user_id):
    user_ref = db.collection('users').document(user_id)
    user_exist = user_ref.get()

    return user_exist


def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)


def verify_user(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
    except:
        return False
    return decoded_token


"""
    /database/createUser [POST]
    INPUT:
    'id_token': JWT token given by user

    PURPOSE: 
    Creates a user entry in firebase
    
"""


@app.route('/database/createUser', methods=['POST'])
def create_user():
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()

        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})

        docref = db.collection(u'users').document(user['uid'])

        doc = docref.get()

        if doc.exists:
            return jsonify({'error': "User already exists"})

        return jsonify({"success": "User was created"})
    else:
        return jsonify({'error': 'not POST request'})


"""
    /database/deleteUser [DELETE]
    INPUT:
    'id_token': JWT token given by user

    PURPOSE:
    Delete user from database and all photos associated with account

"""


@app.route('/database/deleteUser', methods=['DELETE'])
def delete_user_data():
    if request.method == "DELETE":
        id_token = request.form['id_token'].strip()

        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        photo_ref = db.collection('users').document(uid).collection("photos")
        user_ref = db.collection('users').document(uid)
        trashcan_ref = db.collection('users').document(
            uid).collection("owned_trashcans")
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({'error': "User doesn't exists"})

        array = []

        for image_id in photo_ref.stream():
            array.append(image_id.id)
            try:
                delete_blob("greenday-user-photos", image_id.id)
            except:
                pass

        """for trashcan in photo_ref.stream():
        """
        delete_collection(user_ref.collection('photos'), 1000)
        user_ref.delete()

        return jsonify({'success': {
            'code': 'User data was deleted and {} photo(s) deleted'.format(len(array)),
            'photos': tuple(array)
        }})
    else:
        return jsonify({'error': 'not DELETE request'})
