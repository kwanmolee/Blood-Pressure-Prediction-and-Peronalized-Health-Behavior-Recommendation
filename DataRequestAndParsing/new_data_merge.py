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
from slp_processing import *


class load_data:
    def __init__(self, user_id):
        sup_path = "samsung"
        self.attribute = ["heart_rate", "sleep_stage", "step_count"]
        
        #self.attribute = ["heart_rate", "sleep_stage", "step_daily_trend", "floors_climbed", "step_count", "calories_burned"]
        self.DF = self.read_df({}, sup_path, user_id)
    
    def read_df(self, DF, sup_path, user_id):
        user_id = int(user_id)
        for name in self.attribute:
            if name not in ["step_daily_trend", "step_count"]:
                path = "{0}/{1:03d}/{2}/{2}.csv".format(sup_path, user_id, name)
                df = pd.read_csv(path)
                df = df.drop(columns = ["Unnamed: 0"])
                #df.interpolate(method = "linear", inplace = True)
            else:
                data = []
                file = "{0}/{1:03d}/{2}".format(sup_path, user_id, name)
                for filename in os.listdir(file):
                    if filename == ".ipynb_checkpoints":
                        continue
                    path = "{0}/{1}".format(file, filename)
                    df = pd.read_csv(path)
                    df = df.drop(columns = ["Unnamed: 0"])
                    data.append(df)
                df = pd.concat(data)
                df = df.drop_duplicates()
                time = "start_time" if name == "step_count" else "day_time"
                df = df.sort_values(by =[time])
                df.index = range(len(df))
            DF[name] = df
            time = "start_time" if name not in ["step_daily_trend", "calories_burned"] else "day_time"
            DF[name][time] = pd.to_datetime(DF[name][time])
        return DF

class data_merge:
    def __init__(self, user_id):
        data = load_data(user_id)
        self.df = data.DF

    def merge(self):
        """
        heart rate: upsample 
        step count: upsample 
        sleep stage: discard invalid data （sleep hours less than 4 a day)
                     carry last valid observation forward
        """

        # sleep stage preprocessing
        slp = sleep_processing(self.df["sleep_stage"])
        slp.get_new_slp()
        self.duration = slp.duration
        ss = slp.new_slp


        t = "start_time"
        ss = ss.set_index(t)
        ss = ss.resample(rule = "T").mean()


        hr = self.df["heart_rate"]
        hr = hr.set_index(t)
        hr = hr.resample(rule = "T").mean() 

        sc = self.df["step_count"]
        sc = sc.set_index(t)
        sc = sc.resample(rule = "T").mean() 

        d1 = pd.merge_asof(sc, hr, on = t)
        d2 = pd.merge_asof(d1, ss, on = t)
        d2 = d2.drop(columns = ["sample_position_type"])
        return d2
    
    def interpolate(self, df):
        """
        heart rate: linear interpolation
        sleep stage: only fill the intervals between observed sleep stages
                     i.e. 0-10 AM, 12PM - 13PM, 21PM - 24PM are the boundaries of stages observed
                     then the final data we have will just be in above ranges
                     We will NOT carry the 10am data forward to fill the sleep stages between 10am-12pm
        step count: zero padding, no values interpolated 
        """
        new_df = df
        for attr in ["heart_beat_count", "heart_rate", "min", "max"]:
            new_df[attr] = new_df[attr].interpolate(method = "linear", order = 3)
        for attr in ["count", "distance", "speed", "calorie"]:
            new_df[attr] = new_df[attr].fillna(0)

        # if having no previous refernce data values, heart rate will just stay nan
        ## fill it to 0 so that it wouldnt affect the following computation like max hr
        new_df["heart_rate"] = new_df["heart_rate"].fillna(0)  
        return new_df
    
    def compute_calories(self, df):
        """
        compute the daily total calories based on calorie for every event in the step count
        """
        cal = pd.DataFrame(df, columns = ["start_time", "calorie"])
        cal["day"] = cal.start_time.dt.date
        c = cal.groupby("day").describe()
        c["total"] = c["calorie"]["count"] * c["calorie"]["mean"]
        df["total_calorie"] = 0
        df["day"] = df["start_time"].dt.date
        for i in range(len(df["day"].unique())):
            date = df["day"].unique()[i]
            df["total_calorie"][np.argwhere(df["day"] == date)[0]] = c["total"][np.argwhere(c.index == date)[0]]
        return df
    
    def summarize(self, df, age):
        df = self.compute_calories(df)        
        max_hr = 220 - age
        df["heart_rate_zone"] = df["heart_rate"] / max_hr
        df["end_time"] = df["start_time"] + timedelta(seconds = 59)
        return pd.DataFrame(df, columns = ["day", "start_time", "end_time", "heart_rate", "heart_rate_zone",\
                                           "min", "max", "heart_beat_count", "count", "distance", "speed",\
                                           "calorie", "total_calorie", "stage"])
    def compute_rest_hr(self, df):
        idx = np.argwhere(df["heart_rate"] > 0)
        df = df.iloc[idx.reshape(len(idx),)]
        days = set(df.day.unique())
        rest_hr = {}
        for d in days:
            idx = np.argwhere(df["day"] == d)
            df1 = df.iloc[idx.reshape(len(idx),)]
            idx = np.argwhere(np.logical_and(df1["count"] > 0, df1["start_time"].dt.hour < 11))
            df1 = df1.iloc[idx.reshape(len(idx),)]
            df1.index = range(len(idx))
            idx = np.argwhere(df1["start_time"].dt.hour > 6)
            idx = idx.reshape(len(idx), )
            if len(idx) > 1:
                try:
                    hr = df1["heart_rate"][idx[0]-1]
                except:
                    hr = df1["heart_rate"][idx[0]]
                rest_hr[d] = hr
        return rest_hr

    def final_merge_df(self):
        data = self.merge()
        new = self.interpolate(data)
        df = self.summarize(new)
        rest_hr = self.compute_rest_hr(df)
        df["rest_heart_rate"] = 0
        for d in rest_hr:
            idx = np.argwhere(df["day"] == d)
            df["rest_heart_rate"][idx.reshape(len(idx),)] = rest_hr[d]
        return pd.DataFrame(df, columns = ["day", "start_time", "end_time", "heart_rate", "rest_heart_rate", "heart_rate_zone",\
            "min", "max", "heart_beat_count", "count", "distance", "speed", "calorie", "total_calorie", "stage"])




