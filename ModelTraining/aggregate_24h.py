from new_data_merge import *

class aggregate_24df:
    def __init__(self, user_id, age):
        m = data_merge(user_id)
        self.df = m.final_merge_df(age)
        self.bp = self.read_bp(user_id)
        self.tmp = self.match_bp_time_and_hr(self.df, self.bp)

    def read_bp(self, user_id):
        bp_pth = "BP/{0:03d}/{0:03d}.csv".format(user_id)
        bp = pd.read_csv(bp_pth)
        bp = bp.sort_values(by = "dateTimeLocal")
        bp["dateTimeLocal"] = pd.to_datetime(bp["dateTimeLocal"])
        bp = pd.DataFrame(bp, columns = ["dateTimeLocal", "diastolic", "systolic"])
        return bp
    
    def match_bp_time_and_hr(self, df, bp):
        bp["start_time"] = bp["dateTimeLocal"].apply(lambda t: t - pd.Timedelta(t.second, unit = "s"))
        comb = pd.merge(bp, df, how = "inner", on = "start_time")
        tmp = pd.DataFrame(comb, columns = ["dateTimeLocal", "heart_rate"])
        tmp.columns = ["dateTimeLocal", "measure_heart_rate"]
        return tmp

    def get_past_24(self, df, bp):
        bp["dateTimeLocal"] = pd.to_datetime(bp.dateTimeLocal)
        past_24 = {}
        for time in set(bp.dateTimeLocal.unique()):
            past_24[time] = "Nan"
            start, end = pd.to_datetime(time), pd.to_datetime(time)
            start -= pd.Timedelta(start.second, unit = "s")
            end -= pd.Timedelta(end.second, unit = "s")
            start -= pd.Timedelta('1 days')
            end -= pd.Timedelta(1, unit = "m")
            try:
                s_idx = np.argwhere(df["start_time"] == start)
                e_idx = np.argwhere(df["start_time"] == end)
                s_idx = s_idx.reshape(len(s_idx), )[0]
                e_idx = e_idx.reshape(len(e_idx), )[0] 
                past_24[time] = [s_idx, e_idx]
            except:
                pass
        return past_24

    def extract(self, df, df1):
        day_df = pd.DataFrame(columns = [x for x in df.columns \
                                     if x not in ["start_time", "end_time", "day"]])
        for attr in df.columns:
            if attr in ["day", "start_time", "end_time"]:
                continue
            day_df[attr] = df1[attr]["mean"] if attr not in ["distance", "count", "calorie", "total_calorie", "sleep"] \
                                            else df1[attr]["mean"] * df1[attr]["count"]
        return day_df

    def aggregate_past_24(self, df, bp):
        past_24 = self.get_past_24(df, bp)
        aggregate = {}
        for time in set(bp.dateTimeLocal.unique()):
            if past_24[time] == "Nan":
                continue 
            s, e = past_24[time]
            time = pd.to_datetime(time)
            day_df = df[s:e+1]
            day_df["day"] = datetime(time.year, time.month, time.day)
            #print(day_df)
            up_time, bed_time = self.compute_sleep(day_df)
            duration = self.get_duration(day_df)
            t = day_df.groupby("day").describe()
            aggre = self.extract(df, t)
            aggre["wake_time"], aggre["bed_time"], aggre["sleep"] = up_time, bed_time, duration
            aggre.index = range(len(aggre))
            aggregate[time] = aggre
        return aggregate

    def get_duration(self, df):
        idx = np.argwhere(df["stage"] > 1)
        return len(idx)

    def get_bed_time(self, df1, time):
        bed_time = None
        i = np.argwhere(np.logical_and(df1["count"] > 1, df1["start_time"].dt.hour > time))
        if len(i):
            bed_time = df1["start_time"].iloc[i.reshape(len(i),)[-1]].time()
        else:
            # 2. if no values, pick first sleep time
            i = np.argwhere(np.logical_and(df1["stage"] > 1, df1["start_time"].dt.hour > time))
            if len(i):
                bed_time = df1["start_time"].iloc[i.reshape(len(i),)[0]].time()
        return bed_time

    def get_up_time(self, df1, time1, time2):
        up_time = None
        i = np.argwhere(np.logical_and(df1["count"] > 0, df1["start_time"].dt.hour > time1))
        if len(i):
            up_time = df1["start_time"].iloc[i.reshape(len(i),)[0]].time()
        else:
            # 2. if no values, pick last sleep time 
            i = np.argwhere(df1["stage"] > 1)
            df2 = df1.iloc[i.reshape(len(i),)]
            i = np.argwhere(np.logical_and(df2["start_time"].dt.hour < time2, df2["start_time"].dt.hour > time1))
            if len(i):
                up_time = df2["start_time"].iloc[i.reshape(len(i), )[-1]].time()
        return up_time

    def compute_sleep(self, df):
        last, nxt = sorted(df.start_time.dt.date.unique())
        i = np.argwhere(df["start_time"].dt.date == last)
        j = np.argwhere(df["start_time"].dt.date == nxt)
        df1 = df.iloc[i.reshape(len(i),)]    
        df2 = df.iloc[j.reshape(len(j),)]
        df1.index = range(len(df1))
        df2.index = range(len(df2))    
        
        # first day
        bt1 = self.get_bed_time(df1, 21)
        ut1 = self.get_up_time(df1, 6, 12)
        # second day
        bt2 = self.get_bed_time(df2, 21)
        ut2 = self.get_up_time(df2, 6, 12)
        
        bed_time = bt2 if bt2 else bt1 or "Nan"
        up_time = ut2 if ut2 else ut1 or "Nan"
        
        return up_time, bed_time


    def map_bp(self, df, bp):
        aggregate = self.aggregate_past_24(df, bp)
        new = pd.concat(aggregate)
        new.index = new.index.map(lambda x: x[0])
        new["dateTimeLocal"] = new.index
        new.index = range(len(new))
        new = pd.merge(new, bp, how = "inner", on = "dateTimeLocal")
        return pd.DataFrame(new, columns = ["dateTimeLocal", "diastolic", "systolic", "heart_rate","rest_heart_rate", \
                                        "heart_rate_zone", "min", "max","heart_beat_count", "count", "distance",\
                                        "speed", "calorie", "sleep", "wake_time","bed_time", "stage"])
    def map_day(self, x):
        return 1 if x < 5 else 0

    def combine_features(self):
        df, bp = self.df, self.bp
        new = self.map_bp(df, bp)
        new["day_of_week"] = new["dateTimeLocal"].dt.weekday
        new["weekday"] = new["day_of_week"].map(lambda x: self.map_day(x))
        new["weekend"] = new["weekday"].apply(lambda x: int(not x))
        final = pd.merge(new, self.tmp, how = "inner", on = "dateTimeLocal")
        final["measure_time"] = final["dateTimeLocal"].apply(lambda x: x.time())
        final = final.sort_values(by = "dateTimeLocal")
        final.index = range(len(final))
        return final