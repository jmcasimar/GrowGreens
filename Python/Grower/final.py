###
### LIBRERIAS
###

try:
    
    import os
    import io
    from io import BytesIO
    import base64
    import datetime
    import natsort
    
    import numpy as np
    import pandas as pd

    from google.cloud import storage

except Exception as e:
    print("Faltan algunos módulos {}".format(e))
    

###
### FUNCIONES 
###


def bucket_naming(parent_dir, folder_name):
    # Create unique filename to avoid name collisions in Google Cloud Storage

    # list of directories
    dirlist = sorted(os.listdir(os.path.join(parent, folder_name)))
    # kinds of analysis

    bucket_seq =  ['sequence' +'-'+ dirlist[i] +'-'+ datetime.datetime.utcnow().strftime("%F_%H-%M-%S") for i in range(len(dirlist))]
    bucket_the = ['thermal' +'-'+ dirlist[j] +'-'+ datetime.datetime.utcnow().strftime("%F_%H-%M-%S") for j in range(len(dirlist))]
    
    seqpath = [parent + '/' + folder_name + '/' + dirlist[i] + '/' + 'sequence' for i in range(len(dirlist))]
    thepath = [parent + '/' + folder_name + '/' + dirlist[i] + '/' + 'thermal' for i in range(len(dirlist))]
    
    
    return seqpath, thepath, bucket_seq, bucket_the


def add_bucket_owner(bucket_name, user_email, creds):
    """Adds a user as an owner on the given bucket."""
    # bucket_name = "your-bucket-name"
    # user_email = "name@example.com"

    storage_client = storage.Client.from_service_account_json(creds)

    bucket = storage_client.bucket(bucket_name)

    # Reload fetches the current ACL from Cloud Storage.
    bucket.acl.reload()

    # You can also use `group()`, `domain()`, `all_authenticated()` and `all()`
    # to grant access to different types of entities.
    # You can also use `grant_read()` or `grant_write()` to grant different
    # roles.
    bucket.acl.user(user_email).grant_owner()
    bucket.acl.save()

    print(
        "Added user {} as an owner on bucket {}.".format(
            user_email, bucket_name
        )
    )



def create_bucket(creds, bucket_name, bucket_class="STANDARD", location="us"):
    """
    Create a new bucket in specific location with storage class
    bucket_name = "your-new-bucket-name
    bucket_class = storage classes: "STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"
    location = "us" by default
    
    returns bucket object with .name, .location, .class 
    """

    storage_client = storage.Client.from_service_account_json(creds)

    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = bucket_class
    new_bucket = storage_client.create_bucket(bucket, location=location)

    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return new_bucket


def upload_blob(creds, bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client.from_service_account_json(creds)
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )



def list_buckets(creds, project='valledebravo'):
    """Lists all buckets."""

    storage_client = storage.Client.from_service_account_json(creds)
    
    buckets = storage_client.list_buckets()

    bucket_list = [bucket.name for bucket in buckets]

    return bucket_list







if __name__ == '__main__':
    
    user_email = 'jcrog@sippys.com.mx'
    # Service Account credentials
    creds = 'valledebravo-abe4b2b56fc0.json'
    # Parent Directory
    parent = '/home/pi/Documents/GrowGreens/Python/Grower'
    # Directory name 
    folder_name = 'data'
    
    sequence, thermal, buckets_seq, buckets_the = bucket_naming(parent, folder_name)
    
    
    for i in range(len(sequence)):
        
        
        bucket = create_bucket(creds, buckets_seq[i], bucket_class="STANDARD", location="us")
        print(bucket)
        buckett = create_bucket(creds, buckets_the[i], bucket_class="STANDARD", location="us")
        
        
        seqphotos = natsort.natsorted(os.listdir(sequence[i]), reverse=False)
        thephotos = natsort.natsorted(os.listdir(thermal[i]), reverse=False)
        
        for j in range(len(seqphotos)):
            
            upload_blob(creds, buckets_seq[i], sequence[i] + '/' + seqphotos[j], seqphotos[j])
            upload_blob(creds, buckets_the[i], thermal[i] + '/' + thephotos[j], thephotos[j])
    



"""
    for i in range(5):#(len(sequence)):
        
        seqphotos = natsort.natsorted(os.listdir(sequence[i]), reverse=False)
        thephotos = natsort.natsorted(os.listdir(thermal[i]), reverse=False)
        
        #create_bucket(creds, buckets[i], bucket_class="STANDARD", location="us")
        print(buckets[i])
        
        for j in range(5):#(len(seqphotos)):
          
            #upload_blob(creds, buckets[i], sequence[i] + '/' + seqphotos[j], seqphotos[j])
            print(sequence[i] + '/' + seqphotos[j])
                                                                                                                        
    
    #basename, extension = filelist[0].rsplit('.', 1)    
    #unique_filename = "{0}-{1}.{2}".format(basename, date, extension)
    
    #print(buckets)



    #list_buckets(creds, project='valledebravo')
"""
