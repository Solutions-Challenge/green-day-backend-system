import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("greenday-6aba2-firebase-adminsdk-wppee-88cc844ed3.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def coords_to_county(latitude, longitude):
    url = "https://geo.fcc.gov/api/census/area?lat={}&lon={}&format=json".format(latitude, longitude)

    response = requests.get(url)

    if (response.json()['results'] == []):
        return 'failure'

    county = str(response.json()['results'][0]['county_name'])

    return county

def initialize_city(latitude, longitude):
    county = coords_to_county(latitude, longitude)
    if (county == 'failure'):
        return -1
        
    doc_ref = db.collection(u'counties').document(county).set()

    """
    db.collection('counties').document(county).collection('business').document("name A").set({
        'h' : 'h'
    })
    db.collection('counties').document(county).collection('trashcan-locations').document("h").set({
        'h' : 'b'
    })
    db.collection('counties').document(county).collection('opinions').document("h").set({})
    """

    return "Success"

def add_business(latitude, longitude, name, json={}):
    county = coords_to_county(latitude, longitude)
    if (county == 'failure'):
        return "no county found"

    doc_ref = db.collection(u'counties').document(county)

    doc = doc_ref.get()

    if not doc.exists: 
        return "no document found"

    db.collection('counties').document(county).collection('business').document(name).set(json)
    return "success"

def remove_business(latitude, longitude, name):
    county = coords_to_county(latitude, longitude)
    if (county == 'failure'):
        return "no county found"

    db.collection(u'counties').document(county).collection("business").document(name).delete()

def addCity(latitude, longitude):
    pass

lat = 37.7749
long = 122.4194

print(initialize_city(lat, -long))