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
    @ path - folder path for "STokenXXX.csv"
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
    access_token_url = 'https://data-api-stg.samsunghealth.com/auth/v1/token'
    CLIENT_ID = 'edu.ucsd.health'
    CLIENT_SECRET = '96d21febbe42458c9673d940eada2523'
    session = OAuth2Session(CLIENT_ID, CLIENT_SECRET)
    token = session.refresh_token(url = access_token_url, refresh_token = old_refresh_token)
    print("User {} refresh token: \n{}".format(user_id, token))

    with open("{}/SToken{}".format(path, user_id), 'wb') as f:
        pickle.dump(token, f)
    
    print("Refreshing token done ...")
    return token

def refresh(path, save_path):
    """
    refresh token to get the new one
    @ path - folder path in form of "STokenXXX.csv"
    @ save path - save path for pickle file
    """
    file = path.split(".")[0].split("/")[-1]
    i, user_id = len(file) - 1, ""
    while file[i].isdigit():
        user_id += file[i]
        i -= 1
    user_id = user_id[::-1]
    old_refresh_token = get_old_refresh_token(path)
    refresh_curr_token(old_refresh_token, user_id, save_path)

def pic2csv(sup_path, user_id, save_path):
    """
    convert pickle file to csv
    @ sup_path - main path for pickle files
    @ save path - main path for csv files
    """
    read_path = "{}/SToken{}".format(sup_path, user_id) 
    with open(read_path, "rb") as f:
        token = pickle.load(f)
    with open('{}/SToken{}_1.csv'.format(save_path, user_id), 'w') as f:
        w = csv.DictWriter(f, token.keys())
        w.writeheader()
        w.writerow(token)

def main():
    parser = argparse.ArgumentParser(description = 'Refresh Samsung Data')
    parser.add_argument('--path', default = 'samsung_token/SToken099.csv', help = 'write folder for all users')
    parser.add_argument('--user_id', default = '099', help = 'user id')
    #parser.add_argument('--main_path', default = 'samsung_token', help = 'write folder for all users')
    parser.add_argument('--pickle_path', default = 'samsung_pickle', help = 'pickle path for all users')
    parser.add_argument('--token_path', default = 'samsung_token', help = 'token path for all users')
    args = parser.parse_args()
    
    #for filename in os.listdir(args.main_path):
        #refresh(args.main_path + "/" + filename, args.pickle_path)
    refresh(args.path, args.pickle_path)
    pic2csv(args.pickle_path, args.user_id, args.token_path)

if __name__ == "__main__":
    main()

