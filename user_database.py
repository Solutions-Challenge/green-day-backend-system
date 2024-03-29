from auth_server import db
from flask import request, jsonify, Blueprint
from google_storage_functions import *
from firebase_admin import auth

user_data = Blueprint('user_data', __name__)


def user_exists(user_id):
    """
    INPUT:
    user_id: A unique identifier for each user

    PURPOSE:
    Takes a user_id and checks if there is a database entry in Firestore
    """
    user_ref = db.collection('users').document(user_id)
    user_exist = user_ref.get()

    return user_exist


def delete_collection(coll_ref, batch_size):
    """
    INPUT:
    coll_ref: A reference to the collection we want to delete
    batch_size: Since this is a recursive function this acts a limit to the recursion depth 

    PURPOSE:
    Recursively deletes a collection its sub collections and documents
    """
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)


def verify_user(id_token):
    """
    INPUT:
    id_token: A JWT token given by the user
    
    PURPOSE:
    Verifies a JWT token and reutnrs the decoded token. 
    """

    # verify_id_token throws an exception when the auth token is invalid or old
    try:
        decoded_token = auth.verify_id_token(id_token)

        # Since an anonymous user shouldn't be able to access our database services
        # We act as if anonymous JWT tokens are invalid
        if decoded_token['firebase']['sign_in_provider'] == "anonymous":
            return False
    except:
        return False
    return decoded_token

@user_data.route('/database/createUser', methods=['POST'])
def create_user():
    """
    INPUT: 
    'id_token': JWT token given by user

    PURPOSE: 
    Creates a user entry in firebase
    
    """
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()

        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})

        docref = db.collection(u'users').document(user['uid'])

        doc = docref.get()
        docref.set({"email":user['email']})
        if doc.exists:
            return jsonify({'error': "User already exists"})

        return jsonify({"success": "User was created"})
    else:
        return jsonify({'error': 'not POST request'})


@user_data.route('/database/deleteUser', methods=['DELETE'])
def delete_user_data():
    """
    INPUT:
    'id_token': JWT token given by user

    PURPOSE:
    Delete user from database and all photos associated with account

    """
    if request.method == "DELETE":
        id_token = request.form['id_token'].strip()

        # Verifies if the user token is valid and not anonymous
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        # Gets the reference to user itself. 
        user_ref = db.collection('users').document(uid)

        # Checks if the user exists
        user_doc = user_ref.get()
        if not user_doc.exists:
            return jsonify({'error': "User doesn't exist"})

        # Gets the reference to user owned photos and trashcans 
        photo_ref = user_ref.collection("photos")
        owned_trashcan_ref = user_ref.collection("owned_trashcans")

        # Deletes all user owned photos from cloud storage
        user_images = []
        
        for image_id in photo_ref.stream():
            user_images.append(image_id.id)
            try:
                delete_blob("greenday-user-photos", image_id.id)
            except:
                pass
        delete_collection(user_ref.collection('photos'), 1000)
        

        # Deletes all user owned trashcans 
        user_trashcans = []
        for owned_trashcan in owned_trashcan_ref.stream():
            # Gets the trash can from its entry in trashcan 
            trashcan_ref = owned_trashcan.to_dict()['user_ref']
            trashcan = trashcan_ref.get().to_dict()

            location_ref = trashcan['location_ref']
            image_id = trashcan['image_id']

            # Attempts to delete the image from the database
            # However if someone muddles with the photos without the api
            # This could cause errors
            try:
                delete_blob("trashcan_images", image_id)
                user_trashcans.append(image_id)
            except:
                pass
            
            trashcan_ref.delete()
            location_ref.delete()
        
        delete_collection(user_ref.collection('owned_trashcans'), 1000)

        user_ref.delete()

        return jsonify({'success': {
            'code': 'User data was deleted, {} photo(s) deleted, and {} trashcan(s) deleted'.format(len(user_images), len(user_trashcans))
        }})
    else:
        return jsonify({'error': 'not DELETE request'})
