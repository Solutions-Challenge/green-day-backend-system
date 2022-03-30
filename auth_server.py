# This file holds all of our server side auth keys 
# This prevents us from generating two instances of a specific credential

import firebase_admin
from firebase_admin import credentials, firestore, auth
import googlemaps

gmaps = googlemaps.Client(key="AIzaSyAVR75_hunpkE3V1kbcJXfKHt1D2B3YgQs")
admin = firebase_admin.initialize_app()
db = firestore.client()

