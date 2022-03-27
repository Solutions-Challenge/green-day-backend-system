from flask import jsonify, json, request, Blueprint
import base64
from numpy import array
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


def get_top(data, top_num):
    detection_classes_as_text = data['detection_classes_as_text']
    detection_scores = data['detection_scores']
    detection_boxes = data['detection_boxes']
    output = []
    for x in range(len(detection_scores)):
        if x == top_num:
            break
        output.append({
                'class': detection_classes_as_text[x],
                'score': detection_scores[x],
                'bbox': detection_boxes[x]
            })

    return output


@mach_learn.route('/predict', methods=['POST'])
def predict():
    if request.method == "POST":
        files = request.files.getlist('files[]')

        for file in files:
            if file is None or file.filename == "":
                return jsonify({'error': 'no file found'})
            if not allowed_file(file.filename):
                return jsonify({'error': 'format not supported'})

            image = base64.b64encode(file.read()).decode("utf-8")
            img_src = 'data:{};base64,{}'.format(file.content_type, image)

            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)

            REQ = requests.post(
                "https://material-analyzer-gkv32wdswa-ue.a.run.app/v1/models/default:predict",
                data=json.dumps({
                    'instances': [{
                        'image_bytes': {
                            'b64': image
                        },
                        'key': file.name
                    }]
                }),
                headers={"Authorization": "Bearer {}".format(creds.token)})
            
            response = json.loads(REQ.content)

            predictions = response.get('predictions', [{}])[0]
            
            predict = get_top(predictions, 5)
            
            ANS = {"payload": []}

            

            if True:
                for i in range(len(predict)):
                    print(data[predict[i]["class"]]["mapData"])
                    if predict[i]["class"] in data:
                        ANS['payload'].append({
                            "ml": {
                                "key": data[predict[i]["class"]]["mapData"]["key"],
                                "name": data[predict[i]["class"]]["mapData"]["name"],
                                "color": data[predict[i]["class"]]["mapData"]["color"],
                                "icon": data[predict[i]["class"]]["mapData"]["icon"],
                            },
                            "imageObjectDetection": {
                                "boundingBox": {
                                    "normalizedVertices": [
                                        {
                                            "x": predict[i]["bbox"][0],
                                            "y": predict[i]["bbox"][1]
                                        },
                                        {
                                            "x": predict[i]["bbox"][2],
                                            "y": predict[i]["bbox"][3]
                                        }
                                    ]
                                },
                                "score": predict[i]["score"]
                            },
                            "displayName": predict[i]["class"]
                        })
            return jsonify({"success": ANS})
            # return jsonify({"success": ANS})
        return jsonify({"error": "prediction failed"})

# {
#   "payload": [
#     {
#       "imageObjectDetection": {
#         "boundingBox": {
#           "normalizedVertices": [
#             {
#               "x": 0.034553755,
#               "y": 0.015524037
#             },
#             {
#               "x": 0.941527,
#               "y": 0.9912563
#             }
#           ]
#         },
#         "score": 0.9997793
#       },
#       "displayName": "Salad"
#     },
#     {
#       "imageObjectDetection": {
#         "boundingBox": {
#           "normalizedVertices": [
#             {
#               "x": 0.11737197,
#               "y": 0.7098793
#             },
#             {
#               "x": 0.510878,
#               "y": 0.87987
#             }
#           ]
#         },
#         "score": 0.63219965
#       },
#       "displayName": "Tomato"
#     }
#   ]
# }