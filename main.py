import re
from flask import Flask, json, request, jsonify
import torch
import clip
from PIL import Image
import numpy as np
import os
from flask_cors import CORS
from data import data
from data import mapData
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth
import base64
import datetime
storage_client = storage.Client()

cred = credentials.Certificate("greenday-6aba2-firebase-adminsdk-wppee-88cc844ed3.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)

CORS(app)

materials = ["Picture of a Wooden Object", "Picture of a Metallic Object", "Picture of Plastic", "Picture of Cardboard", "Picture of Paper", "Picture of Glass", "Picture of an Electronic device", "Picture of a Human", "Picture of Rubber or Latex Gloves", "Picture of an Animal", "Picture of a Plant"]
plastics = ["Picture of Styrofoam", "Picture of Plastic Bag", "Picture of a Plastic Wrapper or Plastic Film", "Picture of Bubble Wrap"]
papers = ["Picture of Shredded Paper", "Picture of Soiled Paper", "Picture of Clean Paper"]
glasses = ["Picture of Broken Glass", "Picture of Ceramic", "Picture of Glassware"]
cardBoards = ["Picture of Cardboard which doesn't contain food", "Picture of a Cardboard which contains pizza"]

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def generate_download_signed_url_v4(bucket_name, blob_name):
    """Generates a v4 signed URL for downloading a blob.

    Note that this method requires a service account key file. You can not use
    this if you are using Application Default Credentials from Google Compute
    Engine or from the Google Cloud SDK.
    """
    # bucket_name = 'your-bucket-name'
    # blob_name = 'your-object-name'

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        # This URL is valid for 15 minutes
        expiration=datetime.timedelta(minutes=2),
        # Allow GET requests using this URL.
        method="GET",
    )

    return url
def upload_blob_from_memory(bucket_name, contents, destination_blob_name):
    """Uploads a file to the bucket."""

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The contents to upload to the file
    # contents = "these are my contents"

    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(contents)

     
    return "{} with contents uploaded to {}.".format(destination_blob_name, bucket_name)

def download_blob_into_memory(bucket_name, blob_name):
    """Downloads a blob into memory."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # blob_name = "storage-object-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(blob_name)
    contents = blob.download_as_string()

    return {"picture": contents, "success": "Downloaded storage object {} from bucket {}.".format(blob_name, bucket_name)}

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

    return "Blob {} deleted.".format(blob_name)

def blob_exists(bucket_name, filename):
   bucket = storage_client.get_bucket(bucket_name)
   blob = bucket.blob(filename)
   return blob.exists()

# as a percentage
MARGIN_OF_ERROR=0.1

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'json']
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def categorize(img, types, top_predictions):
    image = preprocess(img).unsqueeze(0).to(device)
    text = clip.tokenize(types).to(device)
    with torch.no_grad():

        logits_per_image, logits_per_text = model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()

    largestProbIndex = np.argmax(probs[0])
    
    ans = [largestProbIndex]
    for i in range(len(probs[0])):
        if i != largestProbIndex:
            if probs[0][largestProbIndex] - probs[0][i] < MARGIN_OF_ERROR:
                ans.append(i)

    mats = []
    for x in ans:
        top_predictions.append({
            "Material": types[x],
            "percentage": probs[0][x]
        })
        mats.append(types[x])    
    return mats

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
            return jsonify({'failure': "ID token is invalid"})
        
        new_user = auth.get_user(user['uid'])
        data = {
            'email': new_user.email
        }

        docref = db.collection(u'users').document(user['uid'])
        
        doc = docref.get()

        if doc.exists:
            return jsonify({'error': "User already exists"})

        docref.set(data)
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
            return jsonify({'failure': "ID token is invalid"})
        uid = user["uid"]

        photo_ref = db.collection('users').document(uid).collection("photos")
        user_ref = db.collection('users').document(uid)
        
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

        delete_collection(user_ref.collection('photos'), 1000)
        user_ref.delete()
        

        return jsonify({'success': {
            'code': 'User data was deleted and {} photo(s) deleted'.format(len(array)),
            'photos': tuple(array)
        }})
    else:
        return jsonify({'error': 'not DELETE request'})

"""
    // THIS DOESN'T CHECK IF DATA IS CORRECTLY FORMATTED
    /database/addPic [POST]
    INPUT:
    'id_token': JWT token given by user
    'data': The json containing the photo meta data
    'image_base64': The raw base 64 code of the image

    PURPOSE:
    Adds a picture to user entry in firebase and google cloud storage along with metadata

"""
@app.route('/database/addPic', methods=['POST'])
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
        photo_id = data['key']

        bucket_name = 'greenday-user-photos'
        if blob_exists(bucket_name, photo_id):
            return jsonify({"error": "Photo already exists within database"})

        # users/user/photos/photo_key/metadata
        db.collection('users').document(uid).collection("photos").document(photo_id).set(data)

        string = upload_blob_from_memory(bucket_name, image, photo_id)
        
        return jsonify({"success":string})
    else:
        return jsonify({'error': 'not POST request'})

"""
    /database/getPic [POST]
    INPUT:
    'id_token': JWT token given by user
    'photo_id': The name of the photo
    'meta_flag': If this is true only a photos metadata is given

    PURPOSE:
    Returns the base64 encoding of photo and json with metadata

"""
@app.route('/database/getPic', methods=['POST'])
def get_picture():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        photo_id = request.form['photo_id'].strip()
        meta_flag = request.form['meta_flag'].strip()
        
        if meta_flag.lower() == "false":
            meta_flag = False 
        elif meta_flag.lower() == 'true': 
            meta_flag = True 
        else:
            meta_flag = False

        # Verify auth token and find user in database
        user = verify_user(id_token)
        if not user:
            return jsonify({'failure': "ID token is invalid"})
        uid = user["uid"]

        # users/user/photos/photo_key/metadata
        docref = db.collection('users').document(uid).collection("photos").document(photo_id)
        
        # Check if photo_id entry exists
        doc = docref.get()
        if not doc.exists:
            return jsonify({'error': "Picture doesn't exist for this user"})
        
        # If meta flag is true it only downloads meta data and not the photo
        if (meta_flag == False):
            picture = download_blob_into_memory("greenday-user-photos", photo_id)['picture']
        else:
            picture = generate_download_signed_url_v4('greenday-user-photos', photo_id)

        return jsonify({
            "success:":{
                "photo": str(picture),
                "photo-meta": doc.to_dict()
            }
        })
    else:
        return jsonify({'error': 'not POST request'})

"""
    /database/getPicKeys [GET]
    INPUT:
    'id_token': JWT token given by user

    PURPOSE:
    Returns all photo_ids associated with user account

"""
@app.route('/database/getPicKeys', methods=['POST'])
def get_picture_keys():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        # Verify our auth token and find uid to put photo data into database
        user = verify_user(id_token)
        if not user:
            return jsonify({'failure': "ID token is invalid"})
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
    'photo_id': The name of the photo
    'data': The bounding box data 

    PURPOSE:
    Deletes a picture from user database entry and user photos if photo is associated with account

"""
@app.route('/database/deletePic', methods=['DELETE'])
def delete_picture():
    if request.method == 'DELETE':
        id_token = request.form['id_token'].strip()
        photo_id = request.form['photo_id'].strip()

        user = verify_user(id_token)
        if not user:
            return jsonify({'failure': "ID token is invalid"})
        uid = user["uid"]

        photo_ref = db.collection('users').document(uid).collection("photos").document(photo_id)
        
        photo = photo_ref.get()

        if not photo.exists:
            return jsonify({"failure": "Picture doesn't exist or user doesn't own photo"})
        
        photo_ref.delete()
        delete_blob("greenday-user-photos", photo_id)

        return jsonify({'success': "Picture was deleted"})
    else:
        return jsonify({'error': 'not DELETE request'}) 

"""
    //THIS DOESNT CHECK IF DATA IS VALID OR NOT
    /database/addItem
    INPUT:
    'id_token': JWT token given by user 
    'photo_id': The name of the photo
    'data': The bounding box data 

    PURPOSE:
    This adds a json to the MULTI array which holds data for bounding boxes

"""
@app.route('/database/addItem', methods=['POST'])
def add_item():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        photo_id = request.form['photo_id'].strip()
        data = json.loads(request.form['data'].strip())

        print(data)
        # Verify our auth token and find uid to put photo data into database
        user = verify_user(id_token)
        if not user:
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        # Gets photo by 
        photo_ref = db.collection('users').document(uid).collection("photos").document(photo_id)
        doc = photo_ref.get()

        if not doc.exists:
            return jsonify({"failure": "Picture doesn't exist or user doesn't own photo"})
 
        new_json = doc.to_dict() 
        new_json['multi'].append(data)
        photo_ref.set(new_json)

        return jsonify({'success': "Item was added"})
    else:
        return jsonify({'error': 'not GET request'})


@app.route('/mapData', methods=['GET'])
def getData():
    return jsonify({'success': mapData})


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == "POST":
        files = request.files.getlist('files[]')

        for file in files:
            top_predictions = []
            if file is None or file.filename == "":
                return jsonify({'error': 'no file found'})
            if not allowed_file(file.filename):
                return jsonify({'error': 'format not supported'})
            
            try:
                
                img = Image.open(file)

                mat = categorize(img, materials, top_predictions)

                for material in mat:
    
                    if material == "Picture of Plastic":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Plastic"]
                        categorize(img, plastics, top_predictions)
                    
                    if material == "Picture of Paper":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Paper"]
                        categorize(img, papers, top_predictions)
                    
                    if material == "Picture of Glass":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Glass"]
                        categorize(img, glasses, top_predictions)
                    
                    if material == "Picture of Cardboard":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Cardboard"]
                        categorize(img, cardBoards, top_predictions)
                
                temp = []
                for i in reversed(range(len(top_predictions))):
                    m = top_predictions[i]["Material"]
                    if m in data:
                        temp.append(data[m])
                ans.append(temp)
            except:
                return jsonify({'error': 'error during prediction'})

        return jsonify({'success': ans})
    return jsonify({'error': 'not POST request'})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
