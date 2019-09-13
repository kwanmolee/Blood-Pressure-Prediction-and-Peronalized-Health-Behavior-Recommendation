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

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

------------------------            Process Samsung Data                      ------------------------

Attributes:
    - heart_rate: start time
    - step_count: start time
    - step_daily_trend: day time
    - sleep: start time
    - sleep_stage: start time
    - floors_climbed: start time
    - calories_burned: day time
    - TODO: exercise: NOT completed yet (different binning data need to be decompressed)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class samsung_data():
    def __init__(self, attribute, token, offset = False):
        """
        @ attribute - str
        @ token - str, access token
        @ offset - bool/str, next_offset token returned by request
                 - if False, read the earliest data
                 - if str, read the next data stream
        """
        self.attribute = attribute
        self.offset = offset
        prefix = "shealth" if attribute in ["calories_burned", "step_daily_trend"] else "health"
        self.url = "https://data-api-stg.samsunghealth.com/health/v1/users/me/com.samsung.{0}.{1}".format(prefix, attribute)
        self.headers = {'Authorization':token}
        
        self.data = {"limit": "2000"} # first read / read without offset
        if self.offset:
            self.params = {"offset": self.offset} # read with offset
    
    def request2list(self):
        """
        request data and get the records (stored in lists)
        convert the integer time sequence into datetime
        """
        if self.offset:
            self.r = requests.get(self.url, headers = self.headers, params = self.params)
        else:
            self.r = requests.get(self.url, headers = self.headers, data = self.data)
        r_list = json.loads(self.r.text)["records"]
        self.r_list = self.convert_datetime(r_list)
    
    def convert_datetime(self, x):
        """
        UTC -> PST local time
        convert integer time sequence into datetime 
        calories_burned, step_daily_trend -> day time(00:00AM UTC)
        all other attributes -> start time(according to event)
        decompress binning data if there are any

        @ x - list[dict], data records
        @ return - list[dict], time converted
        """
        assert isinstance(x, list)
        
        # different data have different time attributes
        if self.attribute == "step_daily_trend":
            time_attributes = ["create_time", "day_time", "update_time"]
        elif self.attribute == "calories_burned":
            time_attributes = ["active_time", "create_time", "day_time", "update_time"]
        else:
            time_attributes =  ["create_time", "update_time","start_time", "end_time", "time_offset"]
        
        for row in x:
            for time in time_attributes:
                row[time] = "{0}-{1}-{2} {3:02d}:{4:02d}:{5:02d}".format(*localtime(int(row[time])/1000))
            if "binning_data" in row:
                new_bin = zlib.decompress(b64decode(row["binning_data"]), wbits = 47).decode("utf-8") 
                row["binning_data"] = json.loads(new_bin)
                
                try: # for step, no time data inside
                    for new_row in row["binning_data"]:
                        for time in ["start_time", "end_time"]:
                            new_row[time] = '{0}-{1}-{2} {3:02d}:{4:02d}:{5:02d}'.format(*localtime(int(new_row[time])/1000))                  
                except:
                    pass
        return x
    
    def convert_df(self):
        """
        list converted to dataframe for one data attribute each time
        self.new_list - list, 
        TODO: exercise not completed yet
        """
        self.request2list()
        self.new_list = []
        for x in self.r_list:
            if "binning_data" not in x:
                if self.attribute != "exercise":
                    self.new_list += [x]
                else:
                    self.unpack_exercise(x)
            else: # decompress the data
                if self.attribute == "heart_rate":
                    self.unpack_heart_rate(x)
                elif self.attribute == "step_daily_trend":
                    self.unpack_step_daily_trend(x)
        
        self.df = pd.DataFrame.from_dict(self.new_list)
        if self.attribute not in ["step_daily_trend", "calories_burned"]:
            self.df["start_time"] = pd.to_datetime(self.df["start_time"])
            self.df = self.df.sort_values(by =["start_time"])
        else:
            self.df.day_time = pd.to_datetime(self.df.day_time)
            self.df = self.df.sort_values(by =["day_time"])
        self.df.index = range(len(self.df))
    
    def unpack_heart_rate(self, x):
        """
        decompress the binning data for heart rate
        binning data attributes: start_time, end_time, update_time, heart_rate, heart_rate_min, heart_rate_max
        @ x - list[dict], containing compressed binning data
        @ new_list - list[dict], containing decompressed data
        """
        other_attribute = ["create_time", "time_offset", "heart_beat_count", "datauuid", "deviceuuid", "pkg_name"]
        for y in x["binning_data"]:
            bin_dic = {}
            for v in other_attribute:
                bin_dic[v] = x[v]
            bin_dic["max"] = y["heart_rate_max"]
            bin_dic["min"] = y["heart_rate_min"]
            bin_dic["update_time"] = y["end_time"]
            for v in y:
                if v == "heart_rate_max" or v == "heart_rate_min":
                    continue
                bin_dic[v] = y[v]
            self.new_list += [bin_dic]
    
    def unpack_step_daily_trend(self, x):
        """
        decompress the binning data for heart rate
        attributes in binning data : calorie, count, distance, speed
        @ x - list[dict], containing compressed binning data
        @ new_list - list[dict], containing decompressed data
        """
        
        bin_attribute = ["calorie", "count", "distance", "speed"]
        for y in x["binning_data"]:     
            if set(y.values()) == {0.0}:
                continue          
            bin_dic = {}
            for v in x:
                if v not in bin_attribute and v != "binning_data":
                    bin_dic[v] = x[v]
            for v in y:
                bin_dic[v] = y[v]
            self.new_list += [bin_dic]

    def unpack_exercise(self, x):
        names = ["live_data", "location_data", "additional", "start_time"]
        if "live_data" in x:
            b = zlib.decompress(b64decode(x["live_data"]), wbits = 47).decode("utf-8") 
            bins = json.loads(b)
            for b in bins:
                b_dic = {}
                for name in x:
                    if name not in names:
                        b_dic[name] = x[name]
                for nm in b:
                    b_dic[nm] = b[nm]
                if "additional" in x:
                    ad = json.loads(zlib.decompress(b64decode(x["additional"]), wbits = 47).decode("utf-8"))
                    b_dic["additional"] = ad
                if "location_data" in x:
                    ld = json.loads(zlib.decompress(b64decode(x["location_data"]), wbits = 47).decode("utf-8"))
                    b_dic["location_data"] = ld
                try:
                    b_dic["start_time"] = "{0}-{1}-{2} {3:02d}:{4:02d}:{5:02d}".format(*localtime(int(b_dic["start_time"])/1000))
                except:
                    pass
                self.new_list.append(b_dic)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

------------------------            Read Samsung Data                       ------------------------


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class read_data():
    def __init__(self, token):
        """
        @ token - str, access token
        """
        self.DF = {}
        self.token = token
    
    def load_all_data(self, all_data, attribute, sc_token = None):
        """
        load the data till the latest version (only for those having "next_offset")
        @ all_data - list[dataframe]
        @ attribute - str, data type
        @ sc_token - bool/str, step coutnt next_offset (manually add if request failed)
        """
        offset = False if attribute != "step_count" else sc_token
        while 1:
            data = samsung_data(attribute = attribute, token = self.token, offset = offset)
            data.convert_df()
            all_data.append(data.df)
            try:
                offset = json.loads(data.r.text)["next_offset"]
            except:
                print("The latest data of {} has been loaded!".format(attribute))
                break
            
            
        return all_data
    
    def read_heart_rate(self):
        """
        load all heart rate data 
        concatanate them into one large dataframe
        """
        hr_data = []
        try:
            hr_data = self.load_all_data(hr_data, attribute = "heart_rate")
        except:
            test = samsung_data(attribute = "heart_rate", token = self.token)
            try:
                test.convert_df()
            except:
                print("{} - \nError reason: {}\n".format("heart rate", json.loads(test.r.text)))
                
        if hr_data:
            for i in range(len(hr_data)):
                hr_data[i] = pd.DataFrame(hr_data[i], columns = ["time_offset", "start_time", "end_time", \
                                           "create_time", "update_time", "heart_beat_count",\
                                          "heart_rate", "min", "max", "datauuid", "deviceuuid", "pkg_name"])
            hr_df = [hr_data[i] for i in range(len(hr_data))]
            self.hr = pd.concat(hr_df)
            self.hr.index = range(len(self.hr))
            self.DF["heart_rate"] = self.hr
    
    def read_sleep(self):
        sleep = samsung_data(attribute = "sleep", token = self.token)
        try:
            sleep.convert_df()
            self.slp = pd.DataFrame(sleep.df, columns = ["time_offset", "start_time", "end_time", \
                                   "create_time", "update_time", "comment", "datauuid", "deviceuuid", "pkg_name"])
            self.DF["sleep"] = self.slp
        except:
            print("{} - \nError reason: {}\n".format("sleep", json.loads(sleep.r.text)))
        
    
    def read_sleep_stage(self):
        """
        load all sleep stage data 
        concatanate them into one large dataframe
        """
        ss_data = []
        try:
            ss_data = self.load_all_data(ss_data, attribute = "sleep_stage")
        except:
            test = samsung_data(attribute = "sleep_stage", token = self.token)
            try:
                test.convert_df()
            except:
                print("{} - \nError reason: {}\n".format("sleep stage", json.loads(test.r.text)))
        if ss_data:
            for i in range(len(ss_data)):
                ss_data[i] = pd.DataFrame(ss_data[i], columns = ["time_offset", "start_time", "end_time", \
                                               "create_time", "update_time", "stage",\
                                              "sleep_id", "datauuid", "deviceuuid", "pkg_name"])
            ss_df = [ss_data[i] for i in range(len(ss_data))]
            self.ss = pd.concat(ss_df)
            self.ss.index = range(len(self.ss))
            self.DF["sleep_stage"] = self.ss

    
    def read_floors_climbed(self):
        floors = samsung_data(attribute = "floors_climbed", token = self.token)
        try:
            floors.convert_df()
            self.fs = pd.DataFrame(floors.df, columns = ["time_offset", "start_time", "end_time", \
                                   "create_time", "update_time", "floor", "datauuid", "deviceuuid", "pkg_name"])
            self.DF["floors_climbed"] = self.fs
        except:
            print("{} - \nError reason: {}\n".format("floors_climbed", json.loads(floors.r.text)))
    
    def read_step_daily_trend(self):
        step = samsung_data(attribute = "step_daily_trend", token = self.token)
        try:
            step.convert_df()
            self.sdt = pd.DataFrame(step.df, columns = ["day_time", "create_time", "update_time","calorie",\
                                           "count", "distance", "speed", "source_type","source_pkg_name",\
                                           "datauuid", "deviceuuid", "pkg_name"])
            self.DF["step_daily_trend"] = self.sdt
        except:
            print("{} - \nError reason: {}\n".format("step_daily_trend", json.loads(step.r.text)))
        
    
    def read_calories_burned(self):
        calories = samsung_data(attribute = "calories_burned", token = self.token)
        try:
            calories.convert_df()
            self.cal = pd.DataFrame(calories.df, columns = ["day_time", "create_time", "update_time","active_time",\
                                                   "active_calorie","rest_calorie","tef_calorie",\
                                                   "datauuid", "deviceuuid", "pkg_name"])
            self.DF["calories_burned"] = self.cal
        except:
            print("{} - \nError reason: {}\n".format("calories_burned", json.loads(calories.r.text)))

    def read_exercise(self):
        exercise = samsung_data(attribute = "exercise", token = self.token)
        try:
            exercise.convert_df()
            self.ex = pd.DataFrame(exercise.df, columns = ["start_time", "end_time", "create_time", "update_time","duration", \
                                   "exercise_type", "additional", "heart_rate", "max_heart_rate", \
                                   "min_heart_rate", "mean_heart_rate", "calorie", "count", "speed", "max_speed", "mean_speed", \
                                   "distance", "incline_distance", "decline_distance", "max_altitude", \
                                   "min_altitude", "cadence", "max_cadence", "location_data", "comment", "segment"])
            tmp = self.ex.drop(columns = ["additional", "location_data"])
            tmp = tmp.drop_duplicates()
            self.ex = self.ex.iloc[tmp.index]
            self.ex.index = range(len(self.ex))
            self.DF["exercise"] = self.ex
        except:
            print("{} - \nError reason: {}\n".format("exercise", json.loads(exercise.r.text)))
        
    
    def read_step_count(self):
        """
        load all step count data 
        if first request returns empty records, find the next_offset to get next request
        concatanate them into one large dataframe
        """
        sc_data = []
        records = None
        records, curr, prev = None, None, None
        flag = 0
        offset_flag = 0
        
        test = samsung_data(attribute = "step_count", token = self.token)
        try:
            test.convert_df()
            if "next_offset" in json.loads(test.r.text).keys():
                offset_flag = 1
            flag = 1
            
        except:
            if "next_offset" in json.loads(test.r.text).keys():
                offset_flag = 1
                flag = 1
            else:
                print("{} - \nError reason: {}\n".format("step count", json.loads(test.r.text)))
        
        if flag:
            ## find the valid next_offset if first request returns empty records
            if offset_flag:
                while not records:
                    if curr:
                        prev = curr
                    sc = samsung_data(attribute = "step_count", token = self.token, offset = curr)
                    sc.request2list()
                    txt = json.loads(sc.r.text)
                    records, curr = txt["records"], txt["next_offset"]
            sc_data = self.load_all_data(sc_data, attribute = "step_count", sc_token = prev)
            
        if sc_data:
            for i in range(len(sc_data)):
                sc_data[i] = pd.DataFrame(sc_data[i], columns = ["time_offset", "start_time", "end_time", \
                                           "create_time", "update_time", "count", "distance", "speed",\
                                            "calorie", "sample_position_type", "datauuid", "deviceuuid", "pkg_name"])
            sc_df = [sc_data[i] for i in range(len(sc_data))]
            self.sc = pd.concat(sc_df)
            self.sc.index = range(len(self.sc))
            self.DF["step_count"] = self.sc
    
    def read_all(self):
        """
        try reading all data
        if fail, print out error and reasons
        """
        print("1\n")
        self.read_step_count()
        print("Reading finished for step count\n")
        
        print("2\n")
        self.read_step_daily_trend()
        print("Reading finished for step daily trend\n")
        
        print("3\n")
        self.read_heart_rate()
        print("Reading finished for heart rate\n")

        print("4\n")
        self.read_sleep()
        print("Reading finished for sleep\n")
        
        print("5\n")
        self.read_sleep_stage()
        print("Reading finished for sleep stage\n")
        
        print("6\n")
        self.read_floors_climbed()
        print("Reading finished for floors climbed\n")
        
        print("7\n")
        self.read_calories_burned()
        print("Reading finished for calories burned\n")

        print("8\n")
        self.read_exercise()
        print("Reading finished for exercise")


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

------------------------            Extract User Token                       ------------------------

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def extract_user_token(path):
    """
    get user access token
    @ path - folder path for "STokenXXX.csv"
    """
    data = []
    with open(path, newline='') as f:
        cv = csv.reader(f)
        data = [",".join(row) for row in cv]
    # first row is for attributes 
    # second attribute - user token
    dic = {}
    name, val = data[0].split(","),  data[1].split(",")
    for i in range(len(name)):
        dic[name[i]] = val[i] 
    user_token = "{0} {1}".format(dic["token_type"], dic["access_token"])
    return user_token

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
    refressh_token = dic["refresh_token"]
    return refresh_token

def refresh_token(old_refresh_token, user_id, path, offset):
    from authlib.client import OAuth2Session
    from base64 import b64encode
    from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError
    import datetime
    import csv
    import time


    access_token_url = 'https://data-api-stg.samsunghealth.com/auth/v1/token'
    CLIENT_ID = 'edu.ucsd.health'
    CLIENT_SECRET = '96d21febbe42458c9673d940eada2523'
    session = OAuth2Session(CLIENT_ID, CLIENT_SECRET)
    token = session.refresh_token(url = access_token_url, refresh_token = old_refresh_token)
    print("User {} refresh token: \n{}".format(user_id, token))

    with open("{}/SToken{}_{}.csv".format(path, user_id, offset), 'wb') as f:
        pickle.dump(token, f)
    

    """
    with open("samsung_token/SToken%s.csv" %user_id, "w") as csv_file:
        fieldnames = ['token_type','refresh_token','access_token','scope','expires_in','expires_at']
        writer = csv.DictWriter(csv_file, fieldnames = fieldnames)
        writer.writeheader()
        writer.writerow(token)
    """
    print("Refreshing token done ...")

def refresh(path, specified = None):
    for filename in os.listdir(path):
        if filename == specified:       
            subpath = "{}/".format(path) + filename
            user_id = filename.split(".")[0][-3:]
            old_refresh_token = get_old_refresh_token(subpath)
            #print("{} refresh token :".format(user_id))
            save_path = "samsung_token"
            refresh_token(old_refresh_token, user_id, save_path, offset = 1)

#path = "samsung_token"
#refresh(path, specified = "SToken099.csv", offset = 1)

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

------------------------            Load and Save User Data                      ------------------------

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def save_user_data(path, main_folder):
    # check file validity
    extension = path.split(".")[-1]
    if extension != "csv":
        print("This is not a csv file!")
        return 
    file = path.split(".")[0].split("/")[-1]
    # get user id
    i, user_id = len(file) - 1, ""
    while file[i].isdigit():
        user_id += file[i]
        i -= 1
    user_id = user_id[::-1]
    
    if not user_id:
        print("This is not a valid user id!")
        return 
    
    # read user token 
    user_token = extract_user_token(path)
    
    # request data with token and create dataframe 
    print("\n------- reading data for user {} ---------\n".format(user_id))
    
    # create folder OR update file for user
    if not main_folder:
        main_folder = "samsung"
        if not os.path.exists(main_folder):
            os.mkdir(main_folder)

    user_folder = "{0}/{1}".format(main_folder, user_id)
    if not os.path.exists(user_folder):
        os.mkdir(user_folder)
    r = read_data(token = user_token)
    r.read_all()
    for name in r.DF:
        attribute_folder = "{0}/{1}".format(user_folder, name)
        if not os.path.exists(attribute_folder):
            os.mkdir(attribute_folder)
        if name == "step_daily_trend" or name == "step_count":
            version = len(os.listdir(attribute_folder))
            r.DF[name].to_csv(path_or_buf = "{0}/{1}_{2}.csv".format(attribute_folder, name, version))
        else:
            r.DF[name].to_csv(path_or_buf = "{0}/{1}.csv".format(attribute_folder, name))
            
    print("File {0}: Successful convertion and saving!".format(file + ".csv"))

def test_read(args):
    main_folder = args.main_folder
    path = args.path
    user_id = args.user_id

    if not main_folder:
        main_folder = "samsung"
        if not os.path.exists(main_folder):
            os.mkdir(main_folder)
    
    user_folder = "{0}/{1}".format(main_folder, user_id)
    if not os.path.exists(user_folder):
        os.mkdir(user_folder)

    user_token = extract_user_token(path)
    r = read_data(token = user_token)
    r.read_all()
    for name in r.DF:
        attribute_folder = "{0}/{1}".format(user_folder, name)
        if not os.path.exists(attribute_folder):
            os.mkdir(attribute_folder)
        if name == "step_daily_trend" or name == "step_count":
            version = len(os.listdir(attribute_folder))
            r.DF[name].to_csv(path_or_buf = "{0}/{1}_{2}.csv".format(attribute_folder, name, version))
        else:
            r.DF[name].to_csv(path_or_buf = "{0}/{1}.csv".format(attribute_folder, name))
    file = path.split("/")[-1]
    print("File {}: Successful convertion and saving!".format(file))

def main():
    parser = argparse.ArgumentParser(description = 'Samsung data loading and processing')
    parser.add_argument('--main_folder', default = 'samsung', help = 'write folder for all users')
    parser.add_argument('--path', default = 'samsung_token', help = 'read folder for all users')
    parser.add_argument('--user', default = None, help = 'update data for one user')
    args = parser.parse_args()
    path = args.path
    if args.user:
        save_user_data(path + "/" + args.user, main_folder = args.main_folder)
    else:
        for filename in os.listdir(path):
            if filename == "ipynb_checkpoints" or "SToken002.csv":
                continue
            save_user_data(path + "/" + filename, main_folder = args.main_folder) 

if __name__ == "__main__":
    main()
