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
import datetime
import googlemaps
storage_client = storage.Client()

cred = credentials.Certificate(
    "greenday-6aba2-firebase-adminsdk-wppee-88cc844ed3.json")
firebase_admin.initialize_app(cred)
gmaps = googlemaps.Client(key="AIzaSyAVR75_hunpkE3V1kbcJXfKHt1D2B3YgQs")

db = firestore.client()

app = Flask(__name__)

CORS(app)

materials = ["Imgture of a Wooden Object", "Imgture of a Metallic Object", "Imgture of Plastic", "Imgture of Cardboard", "Imgture of Paper", "Imgture of Glass",
             "Imgture of an Electronic device", "Imgture of a Human", "Imgture of Rubber or Latex Gloves", "Imgture of an Animal", "Imgture of a Plant"]
plastics = ["Imgture of Styrofoam", "Imgture of Plastic Bag",
            "Imgture of a Plastic Wrapper or Plastic Film", "Imgture of Bubble Wrap"]
papers = ["Imgture of Shredded Paper",
          "Imgture of Soiled Paper", "Imgture of Clean Paper"]
glasses = ["Imgture of Broken Glass",
           "Imgture of Ceramic", "Imgture of Glassware"]
cardBoards = ["Imgture of Cardboard which doesn't contain food",
              "Imgture of a Cardboard which contains pizza"]

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

def most_frequent(List):
    if List == []:
        return None
    counter = 0
    num = List[0]

    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency > counter):
            counter = curr_frequency
            num = i

    return num

"""
    INPUT:
    latitude: X coordinate
    longitude: Y coordinate
    OUTPUT:
    {
        "subsection-2": level 2 admin zone if exists else post-code else admin 1 zone,
        "subsection-1": level 1 admin zone,
        "postcode": code,
        "country": country
    }

    PURPOSE:
    Returns a normalized global address system so we can effectively partition our data
"""
def extract_location_data(latitude, longitude):
    addresses = gmaps.reverse_geocode((latitude, longitude))

    sub1 = []
    sub2 = []
    admin1 = []
    admin2 = []
    code = []
    country = []
    locality = []

    for address in addresses:
        for t in address['address_components']:
            if "sublocality_level_1" in t['types']:
                #print("sub1", t['long_name'])
                sub1.append(t['long_name'])
            if "sublocality_level_2" in t['types']:
                #print('sub2', t['long_name'])
                sub2.append(t['long_name'])
            if "administrative_area_level_2" in t['types']:
                #print('admin2', t['long_name'])
                admin2.append(t['long_name'])
            if "administrative_area_level_1" in t['types']:
                #print('admin1', t['long_name'])
                admin1.append(t['long_name'])
            if "country" in t['types']:
                #print('country', t['long_name'])
                country.append(t['long_name'])
            if "postal_code" in t['types']:
                #print('code', t['long_name'])
                code.append(t['long_name'])
            if "locality" in t['types']:
                #print('code', t['long_name'])
                locality.append(t['long_name'])

    sub1 = most_frequent(sub1)
    sub2 = most_frequent(sub2)
    admin1 = most_frequent(admin1)
    admin2 = most_frequent(admin2)
    country = most_frequent(country)
    code = most_frequent(code)
    locality = most_frequent(locality)

    return {
        "admin2": admin2 if admin2 != None else sub2,
        "admin1": admin1 if admin1 != None else sub1,
        "postcode": code,
        "country": country,
        "locality": locality
    }

"""
    INPUT:
    latitude: X coordinate
    longitude: Y coordinate

    PURPOSE:
    Returns a geolocation based on coordinates

    Notes:
    admin2 is a level 2 admin zone which is US county or it's equivalent [100 sq mi, 40000sq mi]
    admin1 is a level 1 admin zone which is a US state or US state equivalent. Size is too large to be relavant.
    postcode: Is like a universal zipcode for each country [~1 sq mi, 10000 sq mi] Most are on the smaller side and the largest ones are the least populated
    country: Is self explanatory 
    locality: A town or city inside a county essentially a level 3 admin zone [1 sq mi, 100 sq mi] 
    
    Relative Size
    postcode ~ locality < admin2 < admin1 < counttry
"""
@app.route('/location/reverseGeolocation', methods=['POST'])
def reverse_geolocation():
    latitude = float(request.form['latitude'].strip())
    longitude = float(request.form['longitude'].strip())
    geolocation = gmaps.reverse_geocode((latitude, longitude))

    return jsonify({"success": geolocation})

@app.route('/database/addOpinion', methods=['POST'])
def add_recyling_opinions():
    if request.method == 'POST':
        pass
    else:
        return jsonify

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

        image_id = request.form['image_id'].strip()
        latitude = request.form['latitude'].strip()
        longitude = request.form['longitude'].strip()
        recycling_types = request.form['recyling_types'].strip()
        date = request.form['date_taken'].strip()

        user = verify_user(id_token)
        if (user == False):
            return jsonify({"error": "Auth token is invalid"})
        uid = user['uid']

        # Gets location data from coordinates
        location_data = extract_location_data(latitude, longitude)

        # If country is valid then continue otherwise return error
        try:
            country = location_data['country'].lower()
        except:
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
        locality = location_data['locality'].lower()
        if location_key == None:
            location_key = location_data['admin2'].lower()

        # Gets the level 2 admin zone and sets the key to zip code or level 2 admin zone name
        location_ref = db.collection(u'location_data').document(
            country).collection("postal_codes").document(location_key)
        # Helps me know where the postal code is
        location_ref.set({
            "locality": locality
        })

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

@app.route('/database/getTrashcan', methods=['POST'])
def get_trashcan():
    if request.method == 'POST':
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()
        doc_ref = db.collection('trashcans').document(image_id)
        user = verify_user(id_token)

        if (user == False):
            return jsonify({"error": "Auth token is invalid"})

        data = doc_ref.get()

        if not data.exists:
            return jsonify({"error:": "Data does not exist"})

        data = data.to_dict()

        if user['uid'] != data['user']:
            return jsonify({"error:": "User doesn't own trashcan"})

        loc_ref = data['location_ref']
        loc_ref_data = loc_ref.get().to_dict()
        latitude = loc_ref_data['latitude']
        longitude = loc_ref_data['longitude']

        recycling_types = data['recycling_types']
        image_base64 = download_blob_into_memory('trashcan_images', image_id)
        date = data['date_taken']
        return jsonify({
            "success": {
                'latitude': latitude,
                'longitude': longitude,
                'recycling_types': recycling_types,
                'image_base64': str(image_base64['picture']),
                'date_taken': date,
            }
        })
    else:
        return jsonify({"error": "not POST request"})


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
            return jsonify({'error': "ID token is invalid"})
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
    'meta_flag': If this is true only a photos metadata is given

    PURPOSE:
    Returns the base64 encoding of photo and json with metadata

"""


@app.route('/database/getImg', methods=['POST'])
def get_picture():
    if request.method == "POST":
        id_token = request.form['id_token'].strip()
        image_id = request.form['image_id'].strip()
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
            return jsonify({'error': "ID token is invalid"})
        uid = user["uid"]

        # users/user/photos/image_id/metadata
        docref = db.collection('users').document(
            uid).collection("photos").document(image_id)

        # Check if image_id entry exists
        doc = docref.get()
        if not doc.exists:
            return jsonify({'error': "Imgture doesn't exist for this user"})

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
def get_picture_keys():
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
            return jsonify({"error": "Imgture doesn't exist or user doesn't own photo"})

        photo_ref.delete()
        delete_blob("greenday-user-photos", image_id)

        return jsonify({'success': "Imgture was deleted"})
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
            return jsonify({"error": "Imgture doesn't exist or user doesn't own photo"})

        new_json = doc.to_dict()
        new_json['multi'].append(data)
        photo_ref.set(new_json)

        return jsonify({'success': "Item was added"})
    else:
        return jsonify({'error': 'not GET request'})


@app.route('/mapData', methods=['GET'])
def getData():
    return jsonify({'success': mapData})


materials = ["Picture of a Wooden Object", "Picture of a Metallic Object", "Picture of Plastic", "Picture of Cardboard", "Picture of Paper", "Picture of Glass",
             "Picture of an Electronic device", "Picture of a Human", "Picture of Rubber or Latex Gloves", "Picture of an Animal", "Picture of a Plant"]
plastics = ["Picture of Styrofoam", "Picture of Plastic Bag",
            "Picture of a Plastic Wrapper or Plastic Film", "Picture of Bubble Wrap"]
papers = ["Picture of Shredded Paper",
          "Picture of Soiled Paper", "Picture of Clean Paper"]
glasses = ["Picture of Broken Glass",
           "Picture of Ceramic", "Picture of Glassware"]
cardBoards = ["Picture of Cardboard which doesn't contain food",
              "Picture of a Cardboard which contains pizza"]

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# as a percentage
MARGIN_OF_ERROR = 0.1

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']


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


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == "POST":
        files = request.files.getlist('files[]')

        ans = []

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
                        top_predictions = [
                            i for i in top_predictions if i["Material"] != "Picture of Plastic"]
                        categorize(img, plastics, top_predictions)

                    if material == "Picture of Paper":
                        top_predictions = [
                            i for i in top_predictions if i["Material"] != "Picture of Paper"]
                        categorize(img, papers, top_predictions)

                    if material == "Picture of Glass":
                        top_predictions = [
                            i for i in top_predictions if i["Material"] != "Picture of Glass"]
                        categorize(img, glasses, top_predictions)

                    if material == "Picture of Cardboard":
                        top_predictions = [
                            i for i in top_predictions if i["Material"] != "Picture of Cardboard"]
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
