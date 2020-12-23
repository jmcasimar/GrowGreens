import os
import io
import base64
import datetime
import numpy as np

from google.cloud import storage
from googleapiclient import discovery, http
from httplib2 import Http 
from oauth2client import file, client, tools

#Cron command for scheduling the task weekly
#0 0 * * 0 /home/pi/Documents/GrowGreens/Python/Grower/testinn.py

# process credentials for OAuth2 tokens

def endpoints(scopes):
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', scopes)
        creds = tools.run_flow(flow, store)

    # create API service endpoints
    HTTP = creds.authorize(Http())
    DRIVE  = discovery.build('drive',   'v3', http=HTTP)
    GCS    = discovery.build('storage', 'v1', http=HTTP)

    return [DRIVE, GCS]


def create_bucket(bucket_name, bucket_class="STANDARD", location="us"):
    """
    Create a new bucket in specific location with storage class
    bucket_name = "your-new-bucket-name
    bucket_class = storage classes: "STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"
    location = "us" by default
    
    returns bucket object with .name, .location, .class 
    """

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = bucket_class
    new_bucket = storage_client.create_bucket(bucket, location=location)

    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return new_bucket


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )




# Google Cloud Project ID. This can be found on the 'Overview' page at
# https://console.developers.google.com
PROJECT_ID = 'valledebravo'


# Parent Directory
parent = '/home/pi/Documents/GrowGreens/Python/Grower'
# Directory name 
folder_name = 'data'
study = ['sequence', 'thermal']

dirlist = sorted(os.listdir(os.path.join(parent, folder_name)))

filelist = os.listdir(os.path.join(parent, folder_name, dirlist[0], study[0]))

filename = filelist[0]

# Create unique filename to avoid name collisions in Google Cloud Storage
date = datetime.datetime.utcnow().strftime("%F_%H-%M-%S_") + dirlist[0]
basename, extension = filename.rsplit('.', 1)

unique_filename = "{0}-{1}.{2}".format(basename, date, extension)


bucket_name = date
print(bucket_name)

# Instantiate a client on behalf of the project
#client = storage.Client(project=PROJECT_ID)


"""
# Instantiate a bucket
bucket = client.bucket(CLOUD_STORAGE_BUCKET)
# Instantiate a blob
blob = bucket.blob(unique_filename)

# Upload the file
with open(filename, "rb") as fp:
    blob.upload_from_file(fp)

# The public URL for this blob
url = blob.public_url
"""

def list_buckets(project='valledebravo'):
    """Lists all buckets."""

    storage_client = storage.Client(project)
    #storage_client = storage.Client.from_service_account_json('/home/jcrog/vdeb_app/storage.json')

    buckets = storage_client.list_buckets()

    bucket_list = [bucket.name for bucket in buckets]

    return bucket_list


  
# Remove the Directory 
#os.rmdir(path) 
#print("Directory '%s' has been removed successfully" %directory) 


if __name__ == '__main__':
    
    SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly', 
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/devstorage.read_only',
    'https://www.googleapis.com/auth/devstorage.read_write',
    'https://www.googleapis.com/auth/devstorage.full_control',
    ]

    print(endpoints(scopes=SCOPES))
    
    # Parent Directory
    parent = '/home/pi/Documents/GrowGreens/Python/Grower'
    # Directory name 
    folder_name = 'data'
    dirlist = sorted(os.listdir(os.path.join(parent, folder_name)))
    
    
    
    """
    for i in len(dirlist):
        
        create_bucket(bucket_name=dirlist[i], bucket_class="STANDARD", location="us")
        
        cre
        
        
    """