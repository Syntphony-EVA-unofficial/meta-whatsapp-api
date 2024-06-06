
## Get the code to deploy your own instance
git clone https://github.com/Syntphony-EVA-unofficial/meta-whatsapp-api.git

# Deploy
There is already a Dockerfile in the project you need to build, push, deploy and run. Instructions are common but you can follow this command secuence also.

## for install a new project
gcloud auth login
gcloud projects create $PROJECT_ID 
gcloud config set project $PROJECT_ID 
gcloud services enable speech.googleapis.com --project=$PROJECT_ID 
gcloud services enable run.googleapis.com --project=$PROJECT_ID 

# for cloudrun 
gcloud services disable containerscanning.googleapis.com 
gcloud services enable artifactregistry.googleapis.com

Disable the container scanning if optional.

gcloud artifacts repositories create REPO-NAME --repository-format=docker --location=us-central1 --description="My repository Description"

## getting credentials service account

#gcloud iam service-accounts create YOUR_SERVICE_ACCOUNT_NAME --display-name="My Service Account"

#gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:YOUR_SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/speech.user"

gcloud iam service-accounts keys create ./key.json --iam-account YOUR_SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com

# docker
#docker build -t ARTIFACT_REGISTRY_REPO/IMAGE:TAG .

#docker push ARTIFACT_REGISTRY_REPO/IMAGE_NAME:tag

#gcloud run deploy SERVICE_NAME --image REPO/IMAGE:tag --region us-central1 --platform managed



