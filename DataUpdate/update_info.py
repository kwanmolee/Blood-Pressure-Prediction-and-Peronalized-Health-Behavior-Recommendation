## ---------------------- for updating the user info --------------------------------

import requests
import csv
import json
import pandas as pd
import zlib, json
from base64 import b64encode, b64decode
from time import gmtime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from time import localtime
import datetime
from datetime import datetime, timedelta
import os
import csv
import requests
import pandas as pd
import csv
import io
import json
import collections
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pickle
import sys
import argparse

## ---------------------- read the user info --------------------------------

class load_data:
    def __init__(self):
        pass
    
    def read_df(self, sup_path, user_id):
        DF = {}
        user_id = int(user_id)
        if user_id:
            file_pth = "{0}/{1:03d}".format(sup_path, user_id)
        else:
            # user 0 's id is just 0 rather than 000
            file_pth = "{0}/{1}".format(sup_path, user_id)
        for filename in os.listdir(file_pth):
            if filename == ".ipynb_checkpoints":
                continue
            if filename not in ["step_daily_trend", "step_count"]:
                path = "{0}/{1}/{1}.csv".format(file_pth, filename)
                df = pd.read_csv(path)
                df = df.drop(columns = ["Unnamed: 0"])
            else:
                # there are many versions of step daily trend and step count
                ## read all files -> drop duplicates -> combine into one data frame
                data = []
                attr_pth = "{0}/{1}".format(file_pth, filename)
                for f in os.listdir(attr_pth):
                    if f == ".ipynb_checkpoints":
                        continue
                    path = "{0}/{1}".format(attr_pth, f)
                    df = pd.read_csv(path)
                    df = df.drop(columns = ["Unnamed: 0"])
                    data.append(df)
                df = pd.concat(data)
                df = df.drop_duplicates()
                time = "start_time" if filename == "step_count" else "day_time"
                df = df.sort_values(by = [time])
                df.index = range(len(df))

            DF[filename] = df
            time = "start_time" if filename not in ["step_daily_trend", "calories_burned"] else "day_time"
            DF[filename][time] = pd.to_datetime(DF[filename][time])
        return DF

    def save_user_record(self, sup_path):
        users = {}
        user = set(os.listdir(sup_path))
        info = pd.DataFrame(index = range(len(user)), columns = ["user", "refresh_token", "heart_rate", "step_count", "sleep", "sleep_stage", \
            "floors_climbed", "step_daily_trend", "exercise", "calories_burned"])
        
        i = 0
        for user_id in os.listdir(sup_path):
            print("Start Processing {} ...".format(user_id))
            if not user_id[0].isdigit():
                continue
            user.remove(user_id)
            DF = self.read_df(sup_path, user_id)
            users[user_id] = DF
            info["user"][i] = user_id
            info["refresh_token"][i] = "valid" if DF else "invalid"
            for attr in DF:
                time = "start_time" if attr not in ["step_daily_trend", "calories_burned"] else "day_time"
                t = DF[attr][time]
                s, e = t.iloc[0], t.iloc[-1]
                info[attr][i] = "{} - {}".format(s, e)
            i += 1
        
        for user_id in user:
            info["user"][i] = user_id
            info["refresh_token"][i] = "invalid or empty"
            i += 1
        
        info = info.sort_values(by = ["user"])
        info.to_csv(path_or_buf = "samsung_data_info.csv")
        print("\tupdating info done ...")
        return info

def main():
    sup_path = "samsung"
    data = load_data()
    df = data.save_user_record(sup_path)

if __name__ == "__main__":
    main()
