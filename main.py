from flask import Flask, json, request, jsonify
from location_database import loc_data
from user_database import user_data
from trashcan_database import trash_data
from user_image_database import userimg_data
from machine_learning import mach_learn
from business_database import bus_data

import os
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

app.register_blueprint(loc_data)
app.register_blueprint(user_data)
app.register_blueprint(trash_data)
app.register_blueprint(userimg_data)
app.register_blueprint(mach_learn)
app.register_blueprint(bus_data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))
