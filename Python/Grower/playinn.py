import os
import io
import base64
import datetime
import numpy as np

from google.cloud import storage
from googleapiclient import discovery, http
from httplib2 import Http 
from oauth2client import file, client, tools

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


def bucket_naming(parent_dir, folder_name):
    # Create unique filename to avoid name collisions in Google Cloud Storage

    # list of directories
    dirlist = sorted(os.listdir(os.path.join(parent, folder_name)))
    # kinds of analysis
    study = ['sequence', 'thermal']

    filelist = os.listdir(os.path.join(parent, folder_name, dirlist[0], study[0]))
    #print(filelist)

    bucket_names = [study[i] +'-'+ dirlist[j] +'-'+ datetime.datetime.utcnow().strftime("%F_%H-%M-%S") for i in range(len(study))
                    for j in range(len(dirlist))]
    
    return bucket_names


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


def list_buckets(project='valledebravo'):
    """Lists all buckets."""

    storage_client = storage.Client(project)
    #storage_client = storage.Client.from_service_account_json('/home/jcrog/vdeb_app/storage.json')

    buckets = storage_client.list_buckets()

    bucket_list = [bucket.name for bucket in buckets]

    return bucket_list





if __name__ == '__main__':
    
    # Parent Directory
    parent = '/home/pi/Documents/GrowGreens/Python/Grower'
    # Directory name 
    folder_name = 'data'
    
    SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly', 
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/devstorage.read_only',
    'https://www.googleapis.com/auth/devstorage.read_write',
    'https://www.googleapis.com/auth/devstorage.full_control',
    ]
    
    #storage_client = storage.Client(project='valledebravo')
    
    storage_client = storage.Client.from_service_account_json(
        'storage.json')

    # Make an authenticated API request
    buckets = list(storage_client.list_buckets())
    print(buckets)
    """
    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = bucket_class
    new_bucket = storage_client.create_bucket(bucket, location=location)

    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    """
    
    
    #drive = endpoints(scopes=SCOPES)[0]
    #gcs = endpoints(scopes=SCOPES)[1]
    
    names = bucket_naming(parent, folder_name)
    
    
    for i in len(names):
        print(i)
    #create_bucket(bucket_name, bucket_class="STANDARD", location="us")

    #upload_blob(bucket_name, source_file_name, destination_blob_name)

    #list_buckets(project='valledebravo')

"""
#basename, extension = filelist[0].rsplit('.', 1)    
#unique_filename = "{0}-{1}.{2}".format(basename, date, extension)
"""