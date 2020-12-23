import os
import io
from datetime import datetime

# Parent Directory
parent = '/home/pi/Documents/GrowGreens/Python/Grower'
# Directory name 
folder_name = 'data'
# list of directories
dirlist = sorted(os.listdir(os.path.join(parent, folder_name)))
# kinds of analysis
study = ['sequence', 'thermal']

filelist = os.listdir(os.path.join(parent, folder_name, dirlist[0], study[0]))
#print(filelist)

# Create unique filename to avoid name collisions in Google Cloud Storage

bucket_names = [study[i] +'-'+ dirlist[j] +'-'+ datetime.utcnow().strftime("%F_%H-%M-%S") for i in range(len(study))
                for j in range(len(dirlist))]

print(dirlist)
print(bucket_names[0])

"""
#basename, extension = filelist[0].rsplit('.', 1)    
#unique_filename = "{0}-{1}.{2}".format(basename, date, extension)
"""