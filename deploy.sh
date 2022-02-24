GOOGLE_PROJECT_ID=greenday-6aba2
GOOGLE_REPO=greenday
CLOUD_REGION=us-east1
IMAGE_NAME=multi
CLOUD_RUN_SERVICE=multi-service
MIN_INSTANCES=1
MAX_INSTANCES=3
SERVICE_ACCOUNT=greenday-service-account@greenday-6aba2.iam.gserviceaccount.com

docker build -t $GOOGLE_REPO/$IMAGE_NAME:latest .
docker tag $GOOGLE_REPO/$IMAGE_NAME:latest $CLOUD_REGION-docker.pkg.dev/$GOOGLE_PROJECT_ID/$GOOGLE_REPO/$IMAGE_NAME:latest

gcloud builds submit --tag $CLOUD_REGION-docker.pkg.dev/$GOOGLE_PROJECT_ID/$GOOGLE_REPO/$IMAGE_NAME:latest \
    --project=$GOOGLE_PROJECT_ID

gcloud auth configure-docker -q

gcloud run deploy $CLOUD_RUN_SERVICE \
    --image=$CLOUD_REGION-docker.pkg.dev/$GOOGLE_PROJECT_ID/$GOOGLE_REPO/$IMAGE_NAME:latest \
    --clear-env-vars \
    --service-account=$SERVICE_ACCOUNT \
    --region=$CLOUD_REGION \
    --max-instances=$MAX_INSTANCES \
    --min-instances=$MIN_INSTANCES \
    --cpu=2 \
    --memory=6G
