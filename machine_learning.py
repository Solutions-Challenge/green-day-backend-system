from flask import jsonify, request, Blueprint
import base64
import requests
import google.auth
import google.auth.transport.requests

creds, project = google.auth.default(
    scopes=['https://www.googleapis.com/auth/cloud-platform'])

from data import data
from data import mapData

mach_learn = Blueprint("mach_learn", __name__)

# as a percentage
MARGIN_OF_ERROR = 0.1

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS

@mach_learn.route('/mapData', methods=['GET'])
def getData():
    return jsonify({'success': mapData})


@mach_learn.route('/predict', methods=['POST'])
def predict():
    if request.method == "POST":
        files = request.files.getlist('files[]')

        for file in files:
            if file is None or file.filename == "":
                return jsonify({'error': 'no file found'})
            if not allowed_file(file.filename):
                return jsonify({'error': 'format not supported'})

            encoded = base64.b64encode(file.read())
            image = encoded.decode("utf-8")

            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)

            REQ = requests.post(
                "https://automl.googleapis.com/v1beta1/projects/15765189134/locations/us-central1/models/IOD4460179913189621760:predict",
                json={
                    "payload": {
                        "image": {
                            "imageBytes": image
                        }
                    }
                },
                headers={"Authorization": "Bearer {}".format(creds.token)})
            
            
            ANS = REQ.json()

            if "payload" in ANS:
                for i in range(len(ANS["payload"])):
                    ANS["payload"][i]["ml"] = data[ANS["payload"][i]["displayName"]]["mapData"]

            return jsonify({"success": ANS})
        return jsonify({"error": "among us"})