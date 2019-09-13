from new_data_merge import *

class build_df:
    def __init__(self, user_id, age):
        m = data_merge(user_id)
        self.df = m.final_merge_df(age)
        #self.duration = m.duration

    def process_sleep(self, df):
        df["sleep"] = 0
        df["stage"].fillna(0, inplace = True)
        idx = np.argwhere(df["stage"] > 1)
        df["sleep"][idx.reshape(len(idx), )] = 1
        return df.groupby("day").describe()

    def compute_bed_time(self, df):
        days = set(df["day"].unique())
        time = {}
        for d in days:
            idx = np.argwhere(df["day"] == d)
            df1 = df.iloc[idx.reshape(len(idx),)]
            
            # initialzie up/bed time, if no values, just remain Nan
            up_time, bed_time = "Nan", "Nan"
            
            # get wake up time
            # 1. step count > 0, time no earlier than 6AM
            i = np.argwhere(np.logical_and(df1["count"] > 0, df1["start_time"].dt.hour > 6))
            if len(i):
                up_time = df1["start_time"].iloc[i.reshape(len(i),)[0]].time()
            else:
                # 2. if no values, pick last sleep time 
                i = np.argwhere(df1["stage"] > 1)
                df2 = df1.iloc[i.reshape(len(i),)]
                i = np.argwhere(np.logical_and(df2["start_time"].dt.hour < 12, df2["start_time"].dt.hour > 6))
                up_time = df2["start_time"].iloc[i.reshape(len(i), )[-1]].time()
                                      
            # get bed time
            # 1. pick last awake time by step count, step count == 1 can be viewed as in bed state
            i = np.argwhere(np.logical_and(df1["count"] > 1, df1["start_time"].dt.hour > 21))
            if len(i):
                bed_time = df1["start_time"].iloc[i.reshape(len(i),)[-1]].time()
            else:
                # 2. if no values, pick first sleep time
                i = np.argwhere(np.logical_and(df1["stage"] > 1, df1["start_time"].dt.hour > 21))
                if len(i):
                    bed_time = df1["start_time"].iloc[i.reshape(len(i),)[0]].time()
            time[d] = (up_time, bed_time)
        return time  

    def map_day(self, x):
        return 1 if x < 5 else 0

    def extract(self, df, df1):
        day_df = pd.DataFrame(columns = [x for x in df.columns \
                                     if x not in ["start_time", "end_time", "day"]])
        for attr in df.columns:
            if attr in ["day", "start_time", "end_time"]:
                continue
            day_df[attr] = df1[attr]["mean"] if attr not in ["distance", "count", "calorie", "total_calorie", "sleep"] else df1[attr]["mean"] * df1[attr]["count"]
        return day_df

    def combine_features(self, DF):
        df = self.process_sleep(DF)
        df = self.extract(DF, df)
        df["start_time"] = pd.to_datetime(df.index)
        df.index = range(len(df))
        time = self.compute_bed_time(DF)
        self.bed_time = time

        # weekday
        df["day_of_week"] = df["start_time"].dt.weekday
        df["weekday"] = df["day_of_week"].map(lambda x: self.map_day(x))
        df["weekend"] = df["weekday"].apply(lambda x: int(not x))
        
        # map date with corresponding wake/bed time
        df["day"] = df["start_time"].dt.date
        df["wake_time"] = df["day"].map(lambda x: time[x][0])
        df["bed_time"] = df["day"].map(lambda x: time[x][1])
        #df["duration"] = df["day"].map(lambda x: self.duration[x] if x in self.duration else 0)
        return df

    def day_df(self):
        return self.combine_features(self.df)
      
    def minute_df(self):
        return self.df

class prepare_model:
    def __init__(self, user_id, day_df):
        self.df = day_df
        self.id = user_id

    def read_bp(self, user_id):
        bp_pth = "BP/{0:03d}/{0:03d}.csv".format(user_id)
        bp = pd.read_csv(bp_pth)
        bp = bp.sort_values(by = "dateTimeLocal")
        bp["dateTimeLocal"] = pd.to_datetime(bp["dateTimeLocal"])
        bp = pd.DataFrame(bp, columns = ["dateTimeLocal", "diastolic", "systolic"])
        bp["day"] = bp.dateTimeLocal.dt.date
        b = {}
        b["diastolic"] = bp.groupby("day").describe()["diastolic"]
        b["systolic"] = bp.groupby("day").describe()["systolic"]
        bp =  b["diastolic"]
        bp["systolic"] = b["systolic"]["mean"]
        bp["start_time"] = b["diastolic"].index
        bp["diastolic"] = bp["mean"]
        bp = pd.DataFrame(bp, columns = ["start_time","diastolic", "systolic"])
        bp.index = range(len(bp))
        self.bp = bp
        return bp

    def merge_bp_df(self):
        bp = self.read_bp(self.id)
        bp["start_time"] = pd.to_datetime(bp["start_time"])
        self.merge = pd.merge(self.df, bp, how = "inner", on = "start_time")
        return self.merge

    def interpolate(self):
        self.t = time_shift()
        day_df = self.merge_bp_df()
        df = self.t.time_convertion(day_df, cols = ["wake_time", "bed_time", "measure_time"])
        df = df.drop(columns = ["heart_beat_count", "day"])
        df["sleep"] = df["sleep"].map(lambda x: x if x > 0 else self.t.compute_mean(df, "sleep"))
        #df["duration"] = df["duration"].map(lambda x: x if x > 0 else self.t.compute_mean(df, "duration"))
        
        idx = np.argwhere(df["diastolic"] == min(df["diastolic"]))
        df = df.drop(index = idx.reshape(len(idx),))
        return df

    def time_shift_data(self):
        df = self.interpolate()
        return self.t.shift(df)

    
class time_shift:

    def unix_time_millis(self, dt, st):
        dt_delta = timedelta(hours = dt.hour, minutes = dt.minute, seconds = dt.second)
        st_delta = timedelta(hours = st.hour, minutes = st.minute, seconds = st.second)
        return (dt_delta - st_delta).total_seconds() * 1000.0

    def compute_mean(self, df, feature):
        num = len(np.argwhere(df[feature] > 0))
        mean = np.mean(df[feature]) * df.shape[0] / num
        return mean

    def time_convertion(self, df, cols):
        st = datetime.utcfromtimestamp(0).time()
        for col in cols:
            tmp = df[col].map(lambda x: st if x == "Nan" else x)
            df[col] = tmp.map(lambda x: self.unix_time_millis(x, st)) 
            df[col] = df[col].map(lambda x: x if x > 0 else self.compute_mean(df, col))
        return df

    def shift(self, df):
        for co in df.columns:
            if co == "start_time":
                continue
            for i in range(1, 4):
                df[co + "_lag{}".format(i)] = df[co].shift(i)
        df.index = df["start_time"]
        df = df.drop(columns = ["start_time"])
        df.fillna(0, inplace = True)
        return df
