from flask import Flask, request, jsonify
import torch
import clip
from PIL import Image
import numpy as np

app = Flask(__name__)

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
materials = ["wood", "metal", "plastic", "cardboard", "person", "paper", "food"]
plastics = ["Polyethylene Terephthalate", "High-Density Polyethylene", "Polyvinyl Chloride", "Low-Density Polyethylene", "Polypropylene", "Polystyrene"]
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

            image = preprocess(img).unsqueeze(0).to(device)
            text = clip.tokenize(materials).to(device)

            with torch.no_grad():

                logits_per_image, logits_per_text = model(image, text)
                probs = logits_per_image.softmax(dim=-1).cpu().numpy()

            material = materials[np.argmax(probs[0])]

            if material == "plastic":
                text = clip.tokenize(plastics).to(device)

                with torch.no_grad():

                    logits_per_image, logits_per_text = model(image, text)
                    probs = logits_per_image.softmax(dim=-1).cpu().numpy()

                material = plastics[np.argmax(probs[0])]
            
            return jsonify({"material": material})


        except:
            return jsonify({'error': 'error during prediction'})
