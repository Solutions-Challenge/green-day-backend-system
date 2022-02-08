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
     
@app.route('/database/createUser', methods=['GET'])   
def create_user(id_token):
    user = verify_user(id_token)
    if not user:
        return jsonify({'failure': "ID token is invalid"})
    
    new_user = auth.get_user(user.uid)
    data = {
        'email': new_user.email
    }
    db.collection(u'users').document(user.uid).set(data)

@app.route('/database/deleteUser', methods=['GET'])
def delete_user_data(id_token):
    user = verify_user(id_token)
    if not user:
        return jsonify({'failure': "ID token is invalid"})
    uid = user["uid"]

    doc_ref = db.collection('users').document(uid)
    
    delete_collection(doc_ref.collection('photos'), 1000)
    doc_ref.delete()

@app.route('/database/addPic', methods=['POST'])
def add_picture():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        data = json.loads(request.form['data'].strip())
        image = request.form['image_base64'].strip()

        # Verify auth token and find user in database
        user = verify_user(id_token)
        if not user:
            return jsonify({'failure': "ID token is invalid"})

        uid = user["uid"]
        key = data['key']

        # users/user/photos/photo_key/metadata
        db.collection('users').document(uid).collection("photos").document(key).set(data)

        bucket_name = 'greenday-user-photos'
        
        bucket = storage_client.bucket(bucket_name)
        
        stats = storage.Blob(bucket=bucket, name=bucket_name).exists(storage_client)
        if not stats: 
            return jsonify({"error": "Key is already used"})
        string = upload_blob_from_memory(bucket_name, image, key)
        
        return jsonify({"success":string})
    else:
        return jsonify({'error': 'not GET request'})
  

@app.route('/database/getPic', methods=['GET'])
def get_picture():
    id_token = request.form['id_token'].strip()
    photo_id = request.form['photo_id'].strip()

    # Verify auth token and find user in database
    user = verify_user(id_token)
    if not user:
        return jsonify({'failure': "ID token is invalid"})
    uid = user["uid"]

    # users/user/photos/photo_key/metadata
    docref = db.collection('users').document(uid).collection("photos").document(photo_id)
    
    doc = docref.get()
    if not doc.exists:
        return "Picture doesn't exist for this user"
    
    picture = download_blob_into_memory("greenday-user-photos", photo_id)['picture']

    return jsonify({
        "success:":{
            "photo": str(picture),
            "photo-meta": doc
        }
    })

@app.route('/database/getPicMeta', methods=['GET'])
def get_picture_meta(id_token, key):
    # Verify auth token and find user in database
    user = verify_user(id_token)
    if not user:
        return jsonify({'failure': "ID token is invalid"})
    uid = user["uid"]

    # users/user/photos/photo_key/metadata
    docref = db.collection('users').document(uid).collection("photos").document(key)
    doc = docref.get()

    if not doc.exists:
        return jsonify({"failure": "Picture doesn't exist"})

    return doc.to_dict()

@app.route('/database/getPicKeys', methods=['GET'])
def get_picture_keys(id_token):
    # Verify our auth token and find uid to put photo data into database
    user = verify_user(id_token)
    if not user:
        return jsonify({'failure': "ID token is invalid"})
    uid = user["uid"]

    docref = db.collection('users').document(uid).collection("photos")
    docs = docref.stream()
    for doc in docs:
        print(doc.id)

@app.route('/database/deletePic', methods=['DELETE'])
def delete_picture():
    if request.method == 'DELETE':
        id_token = request.form['id_token'].strip()
        photo_id = request.form['photo_id'].strip()

        user = verify_user(id_token)
        if not user:
            return jsonify({'failure': "ID token is invalid"})
        uid = user["uid"]

        
        doc_ref = db.collection('users').document(uid).collection("photos").document(photo_id)
        
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({"failure": "Picture doesn't exist or user doesn't own photo"})
        
        doc_ref.delete()
        delete_blob("greenday-user-photos", photo_id)

        return jsonify({'success': "Picture was deleted"})
    else:
        return jsonify({'error': 'not DELETE request'}) 

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
            return jsonify({'failure': "ID token is invalid"})
        uid = user["uid"]

        # Gets photo by 
        doc_ref = db.collection('users').document(uid).collection("photos").document(photo_id)
        doc = doc_ref.get()

        new_json = doc.to_dict() 
        new_json['multi'].append(data)
        doc_ref.set(new_json)

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
