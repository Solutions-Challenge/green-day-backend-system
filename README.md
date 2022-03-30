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

https://cloud.google.com/docs
https://cloud.google.com/storage/docs
https://firebase.google.com/docs/admin/setup
https://firebase.google.com/docs/firestore



## 💻 Running Locally
First export your service account using
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

## 📧 Contact Us
Contact us at nextchart.beachrock@gmail.com for anything!