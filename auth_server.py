import firebase_admin
from firebase_admin import credentials, firestore, auth
import googlemaps

gmaps = googlemaps.Client(key="AIzaSyAVR75_hunpkE3V1kbcJXfKHt1D2B3YgQs")
cred = credentials.Certificate("service.json")
admin = firebase_admin.initialize_app(cred)
db = firestore.client()

