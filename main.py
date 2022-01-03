from flask import Flask, json, request, jsonify
import torch
import clip
from PIL import Image
import numpy as np
import os
from flask_cors import CORS
from data import data

app = Flask(__name__)

CORS(app)

materials = ["Picture of a Wooden Object", "Picture of a Metallic Object", "Picture of Plastic", "Picture of Cardboard", "Picture of Paper", "Picture of Glass", "Picture of an Electronic device", "Picture of a Human", "Picture of Rubber or Latex Gloves", "Picture of an Animal", "Picture of a Plant"]
plastics = ["Picture of Styrofoam", "Picture of Plastic Bag", "Picture of a Plastic Wrapper or Plastic Film", "Picture of Bubble Wrap"]
papers = ["Picture of Shredded Paper", "Picture of Soiled Paper", "Picture of Clean Paper"]
glasses = ["Picture of Broken Glass", "Picture of Ceramic", "Picture of Glassware"]
cardBoards = ["Picture of Cardboard which doesn't contain food", "Picture of a Cardboard which contains pizza"]

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

BATCH_SIZE = 2

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def categorize(img, types, top_predictions):
    image = preprocess(img).unsqueeze(0).to(device)
    text = clip.tokenize(types).to(device)

    with torch.no_grad():

        logits_per_image, logits_per_text = model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()
        text_probs = logits_per_text.softmax(dim=-1).cpu().numpy()

    topThree = np.argpartition(probs[0], -BATCH_SIZE)[-BATCH_SIZE:]
    ans = []

    for i in range(BATCH_SIZE):
        top_predictions.append({
            "Material": types[topThree[i]],
            "percentage": probs[0][i]
        })
        ans.append(types[topThree[i]])
        

    return ans

@app.route('/predict', methods=['POST'])
def predict():

    top_predictions = []
    tests = 0

    if request.method == "POST":
        files = request.files.getlist('files[]')

        ans = []
        err = {"predictions": 0}

        for file in files:
            if file is None or file.filename == "":
                return jsonify({'error': 'no file found'})
            if not allowed_file(file.filename):
                return jsonify({'error': 'format not supported'})
            
            tests += 1
            
            try:
                
                img = Image.open(file)

                # err["predictions"] = tests

                # Looks like there is an error inside the categorize function
                mat = categorize(img, materials, top_predictions)


                for material in mat:
    
                    if material == "Picture of Plastic":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Plastic"]
                        categorize(img, plastics, top_predictions)
                    
                    if material == "Picture of Paper":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Paper"]
                        categorize(img, papers, top_predictions)
                    
                    if material == "Picture of Glass":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Glass"]
                        categorize(img, glasses, top_predictions)
                    
                    if material == "Picture of Cardboard":
                        top_predictions = [i for i in top_predictions if i["Material"]!="Picture of Cardboard"]
                        categorize(img, cardBoards, top_predictions)
                

                topThree = []

                for i in range(BATCH_SIZE):
                    topPredicted = max(top_predictions, key=lambda x:x['percentage'])
                    top_predictions.remove(topPredicted)
                    topThree.append(topPredicted)


                temp = []
                for i in reversed(range(len(topThree))):
                    m = topThree[i]["Material"]
                    if m in data:
                        temp.append(data[m])
                    else:
                        temp.append({
                            "Material": "NonebutAtLeastHere",
                            "Recyclability": "NonebutAtLeastHere"
                        })
                ans.append(temp)
            except:
                return jsonify({'error': err})

        return jsonify({'success': ans})
    return jsonify({'error': 'not POST request'})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))