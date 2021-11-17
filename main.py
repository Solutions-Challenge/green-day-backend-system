from flask import Flask, request, jsonify
import torch
import clip
from PIL import Image
import numpy as np
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
materials = ["wood", "metals", "plastic", "cardboard", "paper", "glass", "person"]
plastics = ["sterofoam", "hard plastic", "soft plastic", "plastic bags"]
papers = ["paper", "shredded paper"]
glasses = ["broken glass", "glass"]

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def categorize(img, types):
    image = preprocess(img).unsqueeze(0).to(device)
    text = clip.tokenize(types).to(device)

    with torch.no_grad():

        logits_per_image, logits_per_text = model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()

    return np.argmax(probs[0])

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

            material = materials[categorize(img, materials)]

            if material == "plastic":
                material = plastics[categorize(img, plastics)]
            
            if material == "paper":
                material = papers[categorize(img, papers)]
            
            if material == "glass":
                material = glasses[categorize(img, glasses)]

            return jsonify({"material": material})


        except:
            return jsonify({'error': 'error during prediction'})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))