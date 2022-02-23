from main import app
import torch
import torchvision
from flask import jsonify, request
from PIL import Image


import torch
import clip
import numpy as np

from data import data
from data import mapData

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


@app.route('/mapData', methods=['GET'])
def getData():
    return jsonify({'success': mapData})


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
