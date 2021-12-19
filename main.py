from flask import Flask, request, jsonify
import torch
import clip
from PIL import Image
import numpy as np
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

materials = ["Picture of a Wooden Object", "Picture of a Metallic Object", "Picture of Plastic", "Picture of Cardboard", "Picture of Paper", "Picture of Glass", "Picture of an Electronic device", "Picture of a Human", "Picture of Rubber or Latex Gloves", "Picture of an Animal", "Picture of a Plant"]
plastics = ["Picture of Styrofoam", "Picture of Plastic Bag", "Picture of a Plastic Wrapper or Plastic Film", "Picture of Bubble Wrap"]
papers = ["Picture of Shredded Paper", "Picture of Soiled Paper", "Picture of Clean Paper"]
glasses = ["Picture of Broken Glass", "Picture of Ceramic", "Picture of Glassware"]
cardBoards = ["Picture of Cardboard which doesn't contain food", "Picture of a Cardboard which contains pizza"]

data = {
    "Picture of a Wooden Object": { 
        "Material": "Wood",
        "Recyclability": "Recyclable"
    },
    "Picture of a Metallic Object": {
        "Material": "Metal",
        "Recyclability": "Recyclable"
    },
    "Picture of an Electronic device": {
        "Material": "Electronic",
        "Recyclability": "Special-Case"
    },
    "Picture of a Human": {
        "Material": "Human",
        "Recyclability": "Special-Case"
    },
    "Picture of Rubber or Latex Gloves": {
        "Material": "Rubber",
        "Recyclability": "Not Recyclable"
    },
    "Picture of Styrofoam": {
        "Material": "Styrofoam",
        "Recyclability": "Not Recyclable"
    },
    "Picture of Plastic Bag": {
        "Material": "Plastic Bag",
        "Recyclability": "Not Recyclable"
    },
    "Picture of a Plastic Wrapper or Plastic Film":{
        "Material": "Plastic Wrapper or Film",
        "Recyclability": "Not Recyclable"
    },
    "Picture of Bubble Wrap": {
        "Material": "Bubble Wrap",
        "Recyclability": "Not Recyclable"
    },
    "Picture of Shredded Paper": {
        "Material": "Shredded Paper",
        "Recyclability": "Recyclable"
    },
    "Picture of Soiled Paper": {
        "Material": "Soiled Paper",
        "Recyclability": "Not Recyclable"
    },
    "Picture of Clean Paper": {
        "Material": "Clean Paper",
        "Recyclability": "Recyclable"
    },
    "Picture of Broken Glass": {
        "Material": "Broken Glass",
        "Recyclability": "Not Recyclable"
    },
    "Picture of Ceramic": {
        "Material": "Ceramic",
        "Recyclability": "Not Recyclable"
    },
    "Picture of Glassware": {
        "Material": "Glassware",
        "Recyclability": "Recyclable"
    },
    "Picture of Cardboard which doesn't contain food": {
        "Material": "Cardboard",
        "Recyclability": "Recyclable"
    },
    "Picture of a Cardboard which contains pizza": {
        "Material": "Pizza Box",
        "Recyclability": "Not Recyclable"
    },
    "Picture of an Animal": {
        "Material": "Animal",
        "Recyclability": "Special-Case"
    },
    "Picture of a Plant": {
        "Material": "Plant",
        "Recyclability": "Bio-degradable"
    }



}

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def categorize(img, types):
    image = preprocess(img).unsqueeze(0).to(device)
    text = clip.tokenize(types).to(device)

    with torch.no_grad():

        logits_per_image, logits_per_text = model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()
        text_probs = logits_per_text.softmax(dim=-1).cpu().numpy()

    print(types[np.argmax(text_probs[0])])
    print(types[np.argmax(probs[0])])

    return types[np.argmax(probs[0])]

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == "POST":
        file = request.files.get('file')

        if file is None or file.filename == "":
            return jsonify({'error': 'no file found'})
        if not allowed_file(file.filename):
            return jsonify({'error': 'format not supported'})

        try:
            
            img = Image.open(file)

            material = categorize(img, materials)

            if material == "Picture of Plastic":
                material = categorize(img, plastics)
            
            if material == "Picture of Paper":
                material = categorize(img, papers)
            
            if material == "Picture of Glass":
                material = categorize(img, glasses)
            
            if material == "Picture of Cardboard":
                material = categorize(img, cardBoards)

            return jsonify({"material": data[material]})


        except:
            return jsonify({'error': 'error during prediction'})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))