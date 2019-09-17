"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

------------------------            Modules import                       ------------------------

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
import requests
import csv
import json
import pandas as pd
import zlib, json
from base64 import b64encode, b64decode
from time import gmtime
import numpy as np
from time import localtime
import time
import datetime
from datetime import datetime, timedelta
import os
import requests
import pandas as pd
import io
import collections
import pickle
import sys
import argparse
from authlib.client import OAuth2Session
from base64 import b64encode
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

------------------------            Refresh User Token                       ------------------------

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def get_old_refresh_token(path):
    """
    extract current refresh token to get the new one
    @ path - folder path 
    """
    data = []
    with open(path, newline='') as f:
        cv = csv.reader(f)
        data = [",".join(row) for row in cv]
    dic = {}
    name, val = data[0].split(","),  data[1].split(",")
    for i in range(len(name)):
        dic[name[i]] = val[i] 
    refresh_token = dic["refresh_token"]
    return refresh_token

def refresh_curr_token(old_refresh_token, user_id, path):
    """
    refresh token 
    @ path - main path for pickle files
    """    
    access_token_url = 'https://oauth.omronwellness.com/connect/token'
    CLIENT_ID = 'ucsd-api'
    CLIENT_SECRET = '86d80d51-849f-46e8-ab9b-a2b45abb82c6'
    session = OAuth2Session(CLIENT_ID, CLIENT_SECRET)
    token = session.refresh_token(url = access_token_url, refresh_token = old_refresh_token)
    print("User {} refresh token: \n{}".format(user_id, token))
    print("{}/{}".format(path, user_id))
    with open("{}/{}".format(path, user_id), 'wb') as f:
        pickle.dump(token, f)
    
    print("Refreshing token done ...")
    return token
def pic2csv(sup_path, user_id, save_path):
    """
    convert pickle file to csv
    @ sup_path - main path for pickle files
    @ save path - main path for csv files
    """
    read_path = "{}/{}".format(sup_path, user_id) 
    with open(read_path, "rb") as f:
        token = pickle.load(f)
    with open('{}/{}_2.csv'.format(save_path, user_id), 'w') as f:
        w = csv.DictWriter(f, token.keys())
        w.writeheader()
        w.writerow(token)
        
def refresh(path, save_path):
    """
    refresh token to get the new one
    @ path - folder path 
    @ save path - save path for pickle file
    """
    file = path.split(".")[0]
    i, user_id = 0, ""
    while file[i].isdigit():
        i += 1
    user_id = file[:i]
    if user_id == '015':
        old_refresh_token = get_old_refresh_token(path)
        refresh_curr_token(old_refresh_token, user_id, save_path)
        pic2csv('omron_pickle', user_id, 'omron_token')

#save token in omron_pickle and omron_token"
import glob
for files in glob.glob("*.csv"):
    refresh(files, 'omron_pickle')
    


