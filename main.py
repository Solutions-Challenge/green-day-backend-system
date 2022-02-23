
from flask import Flask, json, request, jsonify

import os
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, firestore, auth
import googlemaps

gmaps = googlemaps.Client(key="AIzaSyAVR75_hunpkE3V1kbcJXfKHt1D2B3YgQs")
cred = credentials.Certificate("greenday-6aba2-firebase-adminsdk-wppee-88cc844ed3.json")
admin = firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

CORS(app)

import location_database
import user_image_database
import trashcan_database
import machine_learning
import business_database

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))
