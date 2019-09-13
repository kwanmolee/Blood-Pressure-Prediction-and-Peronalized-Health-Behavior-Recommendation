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

class sleep_processing:
    def __init__(self, slp):
        self.slp = slp

    def get_new_slp(self):
        self.slp = pd.DataFrame(slp, columns = ["stage"])
        self.slp["stage"] = self.slp.stage - 40000
        self.slp["day"] = self.slp.index.date

        self.slp = self.discard(self.slp)
        self.duration, self.new_slp = self.process_sleep(sefl.slp)


    def discard(slp):
        days = set(slp.day.unique())
        drop_indices = np.array([])
        for d in days:
            idx = np.argwhere(slp["day"] == d)
            idx = idx.reshape(len(idx), )
            start, last = slp.index[idx[0]].time(), slp.index[idx[-1]].time()
            sh, sm, ss = start.hour, start.minute, start.second
            eh, em, es = last.hour, last.minute, last.second
            d = (eh - sh) * 60 + (em - sm)
            if d < 240:
                drop_indices = np.append(drop_indices, idx)
        drop_indices = drop_indices.astype(int)
        slp = slp.drop(index = slp.index[drop_indices])
        return slp

    def compute_duration(df):
        start, last = df.index[0].time(), df.index[-1].time()
        sh, sm, ss = start.hour, start.minute, start.second
        eh, em, es = last.hour, last.minute, last.second
        return (eh - sh) * 60 + (em + 1 - sm) 


    def process_sleep(slp):
        """
        the data is badly recorded, while a lot of 1(awaken value) discovered during sleeps tage
        hence, divid the data into morining, noon and evening to find out the exact sleep time
        
        compute daily sleep duration based on three periods: 
        morning(0AM - 10AM), noon(10AM - 13PM), evening(21PM - 24PM)
        """
        data = []
        days = set(slp.day.unique())
        durations = {}
        
        for d in days:
            # filter one day
            idx = np.argwhere(slp["day"] == d)
            df = slp.iloc[idx.reshape(len(idx), )]
            
            ## sleep data
            idx = np.argwhere(df["stage"] > 1)
            df = df.iloc[idx.reshape(len(idx), )]
            
            # cut time periods
            morning = np.argwhere(df.index.hour <= 10)
            noon = np.argwhere(np.logical_and(df.index.hour > 10, df.index.hour < 13))
            evening = np.argwhere(df.index.hour > 21)
            duration = 0
            
            if len(morning) >= 1:
                m = df.iloc[morning.reshape(len(morning),)]
                data.append(m.resample(rule = "T").asfreq())
                duration += self.compute_duration(m)        
            if len(noon) >= 1:
                n = df.iloc[noon.reshape(len(noon), )]
                data.append(n.resample(rule = "T").asfreq())
                duration += self.compute_duration(n) 
            if len(evening) >= 1:
                e = df.iloc[evening.reshape(len(evening),)]
                data.append(e.resample(rule = "T").asfreq())
                duration += self.compute_duration(e) 
            
            durations[d] = duration
        
        new_slp = pd.concat(data)
        new_slp.fillna(method = "ffill", inplace = True)
        new_slp["start_time"] = new_slp.index
        new_slp.index = range(len(new_slp))
        new_slp = new_slp.sort_values(by = ["start_time"])
        
        return durations, new_slp


