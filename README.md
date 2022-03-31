# RecycleMe


<div>
    <a href="https://play.google.com/store/apps/details?id=com.aankur01.greendayfrontend">
        <img src="./assets/images/README/GooglePlay.png" alt="drawing" width="150"/>
    </a>
    <a href="https://apps.apple.com/us/app/recycleme-usa/id1615887126">
        <img src="./assets/images/README/app-store.png" alt="drawing" width="150"/>
    </a>
</div>

## ⚙️ Google Cloud Set Up
Running this backend locally or launching to Cloud Run requires a google cloud account with its respective services activated. 

Refer to the Google Cloud and Firebase documention to set up your service account. 

- https://cloud.google.com/docs
- https://cloud.google.com/storage/docs
- https://firebase.google.com/docs/admin/setup
- https://firebase.google.com/docs/firestore

## 💻 Running Locally
First install the neccessary python libraries using
```
$ pip install -r requirements.txt
```
Export your service account using
```
$ export GOOGLE_APPLICATION_CREDENTIALS=service_account.json
```

Then to set up the Flask variables
```
$ export FLASK_APP=main
```

Finally to run simply
```
$ flask run
```

Or you can skip step 2 and 3 and instead do
```
$ python main.py
```
Note that this method will make the backend behave differently to flask run so beware!

## ☁️ Launching to Cloud Run
If you have your credentials and your Cloud account all you have to do is run the deploy script
```
$ ./deploy.sh
```

You can also modify the variables to change the requirements of your server as you please

```
CLOUD_REGION: The region you want to run your backend (ex: us-east1)
MIN_INSTANCES: The minimum number of instances you want to ramp down from
MAX_INSTANCES: The maximum number of instances you want to server
```

Note that min_instances can be 0 which will make your services slower if you have  

## Function Overview
All requests are made through x-www-form-urlencoded format

## user_database.py
**/database/createUser \[POST\] - Creates an entry for a user in our database**

Parameters: 
id_token: JWT token given by the user


**/database/deleteUser \[DELETE\] - Deletes all user data, cloud photos, and posted trashcans for a user**

Parameters: 
id_token: JWT token given by the user

## user_image_database.py 

**/database/addImg \[POST\] - Adds an image to user's cloud storage**

Parameters:
- 'id_token': JWT token given by user
- 'data': The json containing the photo meta data
- 'image_base64': The raw base 64 code of the image

**/database/getImg \[POST\] - Returns the URL of photo and json with metadata**

Parameters:
- 'id_token': JWT token given by user
- 'image_id': The name of the photo


**/database/getImgKeys \[POST\] - Returns all image_ids associated with user account**

Parameters:
- 'id_token': JWT token given by user

**/database/deleteImg \[POST\] - Deletes a picture from user database entry and user photos if photo is associated with account**

Parameters:
- 'id_token': JWT token given by user 
- 'image_id': The name of the photo
- 'data': The bounding box data 

## trashcan_database.py
**/database/createTrashcanCoords \[POST\] - Creates a trashcan in our database**

Parameters:
- 'latitude': X coordinate
- 'longitude': Y coordinate

**/database/getUserOwnedTrashcans \[POST\] - Gets all trashcans made by one user**

Parameters:
- 'id_token': The JWT token given by the user

**/database/deleteTrashcan \[DELETE\] - Deletes a trashcan from the database** 

Parameters:
- 'id_token': JWT token 
- 'image_id': Name of trashcan

**/database/getTrashcan \[POST\] - Given a trashcan id return the trashcan data from the database**

Parameters:
- 'id_token': JWT token 
- 'image_id': Name of trashcan

**/database/getTrashcanImage \[POST\] - Given a trashcan id returns the url of an image of the trashcan**

Parameters:
- 'image_ids': A list of trashcan ids 

**/database/queryTrashcanLocation \[POST\] - Given an latitude and longitude, return all trashcan ids in a location**

Parameters:
- 'latitude': X coordinate
- 'longitude': Y coordinate

## business_database.py
**/database/createBusinessEntry \[POST\] - Adds a business entry in the database along with relevant data**

Parameters:
- id_token: JWT token authenticating the business
- business_data: Textified Json with business data

Note this is the current accepted business data that the backend takes in. You can modify with your discretion.
``` json
business_data = {
    "name": None,
    "imageid": None,
    "category": None,
    "recyclingTypes": None,
    "location": None,
    "street": None,
    "city": None,
    "county": None,
    "state": None,
    "zipcode": None,
    "phone": None,
    "website": None,
    "timeAvailability": None,
    "lat": None,
    "lng": None
}
```
**/database/updateBusinessEntry \[POST\] - Updates the business data given relevant parameters**

Parameters:
- 'id_token': JWT token authenticating the business
- 'data': A json containing the tokens we want to update

**/database/deleteBusiness \[DELETE\] - Deletes a business entry from the database**

Parameters: 
- 'id_token': JWT token authenticating the business

**/database/getBusinessData \[POST\] - Returns all relevant data that a business has**

Parameters: 
- 'uid': A unique identifier for the business

**/database/queryBusiness \[POST\] - Returns all businesses in an county or county equivalent**

Parameters:
- latitude: X coordinate
- longitude: Y coordinate

**/database/addBusinessImage \[POST\] - Adds an image for a business to Google Cloud Storage**

Parameters:
- 'id_token': JWT token authenticating the business
- 'image_id': A unique name for the image
- 'image_base64': A base64 encoded image we want to add to the database


**/database/getBusinessImages \[POST\] - Returns all photo urls associated with a business**

Parameters:
- 'uid': A unique identifier for a business

**/database/deleteBusinessImages \[POST\] - Deletes images associated with a business**

Parameters:
- 'id_token': JWT token authenticating the business
- 'image_ids': A json containing a list of image_ids the business wants to delete


## 📧 Contact Us
Contact us at nextchart.beachrock@gmail.com for anything!z