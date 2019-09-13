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
import seaborn as sns
from new_data_merge import *


class visualize:
    def __init__(self, user_id):
        bp_pth = "users/{0:03d}/{0:03d}.csv".format(user_id)
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

    def merge_bp_sc(self, sc):
        sc = pd.DataFrame(sc, columns = ["start_time", "count"])
        sc["day"] = sc.start_time.dt.date
        step = sc.groupby("day").describe()
        step = step["count"]
        step["total_steps"] = step["count"] * step["mean"]
        step["start_time"] = step.index
        step.index = range(len(step))
        sc = pd.DataFrame(step, columns = ["start_time", "total_steps"])
        
        return pd.merge(self.bp, sc, how = "inner", on = "start_time")

    def plot_bp_sc(self, sc):
        df = self.merge_bp_sc(sc)

        fig, ax1 = plt.subplots(figsize = (15, 7))
        ax1.set_ylabel('Daily Steps', color = "darkgreen", fontsize = 16)
        ax1.set_title("Daily Steps vs Blood Pressure", fontsize = 16, weight = "bold")
        ax1.bar(range(len(df)), df["total_steps"], color = "cadetblue", label = "steps")
        ax1.legend(fontsize = 12, loc = 4)
        ax1.tick_params(axis='y', labelcolor = "darkgreen")
        ax1.set_ylim([0, 50000])
        ax2 = ax1.twinx() 
        ax2.plot(range(df.shape[0]), df["diastolic"], color = "orange", label = "diastolic")
        ax2.plot(range(df.shape[0]), df["systolic"], color = "indianred", label = "systolic")
        ax2.legend(fontsize = 12, loc = 2)
        ax2.set_ylabel('Blood Pressure', color = "red", fontsize = 16)
        ax2.tick_params(axis='y', labelcolor = "red")
        ax2.set_ylim([0, 150])
        ax1.set_xticks(range(0, df.shape[0] + 2, 2))
        ax1.set_xticklabels(df["start_time"].iloc[::2], rotation = 40, fontsize = 14)
        plt.tight_layout()
        plt.savefig("step_bp.png")
        plt.show()

    def plot_bp_duration(self, duration):
        df = self.merge_bp_slp(duration)
        df = df.sort_values(by = "duration")
        fig, ax1 = plt.subplots(figsize = (15, 7))
        ax1.set_ylabel('Daily Blood Pressure', color = "indianred", fontsize = 16)
        ax1.set_title("Daily Sleep Duration vs Blood Pressure", fontsize = 16, weight = "bold")
        ax1.bar(df["duration"], df["diastolic"], color = "steelblue", label = "sleep duration")
        ax1.legend(fontsize = 12, loc = 4)
        ax1.tick_params(axis='y', labelcolor = "steelblue")
        ax1.set_ylim([0, 1200])
        ax2 = ax1.twinx() 
        ax2.plot(range(df.shape[0]), df["diastolic"], color = "orange", label = "diastolic")
        ax2.plot(range(df.shape[0]), df["systolic"], color = "indianred", label = "systolic")
        ax2.legend(fontsize = 12, loc = 2)
        ax2.set_ylabel('Blood Pressure', color = "indianred", fontsize = 16)
        ax2.tick_params(axis='y', labelcolor = "indianred")
        ax2.set_ylim([0, 150])
        ax1.set_xticks(range(0, df.shape[0] + 2, 2))
        ax1.set_xticklabels(df["start_time"].iloc[::2], rotation = 40, fontsize = 14)
        plt.tight_layout()
        plt.savefig("slp_bp.png")
        plt.show()

    def merge_bp_slp(self, duration):
        slp_duration = pd.DataFrame(index = sorted(duration.keys()), columns = ["duration"])
        slp_duration["duration"] = slp_duration.index
        slp_duration["duration"] = slp_duration["duration"].apply(lambda x: duration[x])
        slp_duration["start_time"] = slp_duration.index
        slp_duration.index = range(len(slp_duration))
        slp_duration = pd.DataFrame(slp_duration, columns = ["start_time", "duration"])
        return pd.merge(slp_duration, self.bp, how = "inner", on = "start_time")

    def plot_duration_freq(self, duration):
        df = self.merge_bp_slp(duration)
        df = df.sort_values(by = "duration")
        df.index = range(len(df))
        plt.figure(figsize = (10,5))
        sns.distplot(df["duration"], color = 'darkblue',\
                     hist_kws={'alpha':.4, 'edgecolor':'black'}, kde_kws={'shade':True})
        plt.title("Sleep Duration Frequency Distribution", fontsize = 16, weight = "bold")
        plt.xticks(fontsize = 14)
        plt.xlabel("Sleep Duration", fontsize = 14, weight = "bold")
        plt.ylabel("Frequency", fontsize = 14)
        plt.tight_layout()
        plt.show()

    def classify_bp(self, df):
        d1 = pd.DataFrame(df, columns = ["duration", "diastolic"])
        d2 = pd.DataFrame(df, columns = ["duration", "systolic"])
        new_df = pd.concat([d1, d2])
        new_df.index = range(len(new_df))
        new_df["type"] = new_df["diastolic"].map(lambda x: "diastolic" if x > 0 else "systolic")
        idx = np.argwhere(new_df["systolic"] > 0)
        new_df["diastolic"][idx.reshape(len(idx), )] = new_df["systolic"][idx.reshape(len(idx), )]
        new_df = pd.DataFrame(new_df, columns = ["duration", "diastolic", "type"])
        new_df.columns = ["duration", "bp", "type"]
        return new_df

    def plot_duration_bp_reg(self, duration):
        df = self.classify_bp(self.merge_bp_slp(duration))
        plt.figure(figsize = (15, 7))
        sns.lmplot("duration", "bp", data = df, hue = "type", palette = {"diastolic": "indianred", "systolic": "#7777aa"})
        plt.title("Blood Pressure Tendency along with Sleep Duration", fontsize = 14, weight = "bold")
        plt.legend(fontsize = 12)
        plt.ylabel("Blood Pressure", fontsize = 14, weight = "bold")
        plt.xlabel("Sleep Duration", fontsize = 14, weight = "bold")
        plt.tight_layout()
        plt.show()


    def plot_bp_slp(self, duration):
        df = self.merge_bp_slp(duration)
        fig, ax1 = plt.subplots(figsize = (15, 7))
        ax1.set_ylabel('Daily Sleep Duration', color = "steelblue", fontsize = 16)
        ax1.set_title("Daily Sleep Duration vs Blood Pressure", fontsize = 16, weight = "bold")
        ax1.bar(range(len(df)), df["duration"], color = "steelblue", label = "sleep duration")
        ax1.legend(fontsize = 12, loc = 4)
        ax1.tick_params(axis='y', labelcolor = "steelblue")
        ax1.set_ylim([0, 1200])
        ax2 = ax1.twinx() 
        ax2.plot(range(df.shape[0]), df["diastolic"], color = "orange", label = "diastolic")
        ax2.plot(range(df.shape[0]), df["systolic"], color = "indianred", label = "systolic")
        ax2.legend(fontsize = 12, loc = 2)
        ax2.set_ylabel('Blood Pressure', color = "indianred", fontsize = 16)
        ax2.tick_params(axis='y', labelcolor = "indianred")
        ax2.set_ylim([0, 150])
        ax1.set_xticks(range(0, df.shape[0] + 2, 2))
        ax1.set_xticklabels(df["start_time"].iloc[::2], rotation = 40, fontsize = 14)
        plt.tight_layout()
        plt.savefig("slp_bp.png")
        plt.show()

    def merge_bp_hr(self, df):
        hrz = pd.DataFrame(df, columns = ["start_time", "heart_rate", "heart_rate_zone"])
        hrz = hrz.fillna(0)
        hrz["day"] = hrz.start_time.dt.date
        percent = self.hrz_percentile(hrz)
        self.percent = percent
        zone = pd.DataFrame(index = sorted(percent.keys()), columns = ["Nan", "50%", "60%", "70%", "80%", "90%", "100%"])
        for i in zone.index:
            for pct in percent[i]:
                if pct == "Nan":
                    zone["Nan"][i] = percent[i][pct]
                else:
                    zone[str(int(pct*100)) + "%"][i] = percent[i][pct]

        zone["start_time"] = zone.index
        zone.index = range(len(zone))
        return pd.merge(zone, self.bp, how = "inner", on = "start_time")

    def plot_bp_hr(self, df):
        df = self.merge_bp_hr(df)
        fig, ax1 = plt.subplots(figsize = (20, 10))
        ax1.set_ylabel('Daily Heart Rate Zone', color = "black", fontsize = 18)
        ax1.set_title("Daily Heart Rate Zone vs Blood Pressure", fontsize = 18, weight = "bold")
        barWidth = 0.8
        x = range(len(df))
        bottom1 = [i + j for i,j in zip(df["Nan"], df["50%"])]
        bottom2 = [i + j for i,j in zip(bottom1, df["60%"])]
        bottom3 = [i + j for i,j in zip(bottom2, df["70%"])]
        bottom4 = [i + j for i,j in zip(bottom3, df["80%"])]
        bottom5 = [i + j for i,j in zip(bottom4, df["90%"])]


        ax1.bar(x, df["Nan"], color = "yellow", edgecolor = "black", width=barWidth, label = "Nan")
        ax1.bar(x, df["50%"], bottom = df["Nan"], color = "#ff9999", edgecolor = "black", width=barWidth, label = "<= 50%")
        ax1.bar(x, df["60%"], bottom = bottom1, color='lightskyblue', edgecolor = "black", width=barWidth, label = "<= 60%")
        ax1.bar(x, df["70%"], bottom = bottom2, color='#7777aa', edgecolor = "black", width=barWidth, label = "<= 70%")
        ax1.bar(x, df["80%"], bottom = bottom3, color='palegreen', edgecolor= "black", width=barWidth, label = "<= 80%")
        ax1.bar(x, df["90%"], bottom = bottom4, color='violet', edgecolor= "black", width=barWidth, label = "<= 90%")
        ax1.bar(x, df["100%"], bottom = bottom5, color='orange', edgecolor= "black", width=barWidth, label = "<= 100%")
        ax1.legend(fontsize = 14, loc = 4)
        ax1.tick_params(axis='y', labelcolor = "black")
        ax1.set_ylim([0, 2.0])

        ax2 = ax1.twinx() 
        ax2.plot(x, df["diastolic"], color = "orange", label = "diastolic")
        ax2.plot(x, df["systolic"], color = "indianred", label = "systolic")
        ax2.legend(fontsize = 18, loc = 2)
        ax2.set_ylabel('Blood Pressure', color = "indianred", fontsize = 18)
        ax2.tick_params(axis='y', labelcolor = "indianred")
        ax2.set_ylim([0, 150])
        ax1.set_xticks(range(0, df.shape[0] + 2, 2))
        ax1.set_xticklabels(df["start_time"].iloc[::2], rotation = 40,fontsize = 14)

        plt.tight_layout()
        plt.savefig("hrz_bp.png")
        plt.show()

    def hrz_percentile(self, hrz):
        days = set(hrz["day"].unique())
        percent = {}
        for d in days:
            idx = np.argwhere(hrz["day"] == d)
            idx = idx.reshape(len(idx), )
            df = hrz.iloc[idx]
            idx0 = np.argwhere(df["heart_rate_zone"] <= 0.01)
            idx1 = np.argwhere(np.logical_and(df["heart_rate_zone"] <= 0.5, df["heart_rate_zone"] >0.01))
            idx2 = np.argwhere(np.logical_and(df["heart_rate_zone"] <= 0.6, df["heart_rate_zone"] >0.5))
            idx3 = np.argwhere(np.logical_and(df["heart_rate_zone"] <= 0.7, df["heart_rate_zone"] >0.6))
            idx4 = np.argwhere(np.logical_and(df["heart_rate_zone"] <= 0.8, df["heart_rate_zone"] >0.7))
            idx5 = np.argwhere(np.logical_and(df["heart_rate_zone"] <= 0.9, df["heart_rate_zone"] >0.8))
            idx6 = np.argwhere(np.logical_and(df["heart_rate_zone"] <= 1.0, df["heart_rate_zone"] >0.9))

            dic = {}
            dic["Nan"] = idx0.shape[0] / df.shape[0]
            dic[0.5] = idx1.shape[0] / df.shape[0]
            dic[0.6] = idx2.shape[0] / df.shape[0]
            dic[0.7] = idx3.shape[0] / df.shape[0]
            dic[0.8] = idx4.shape[0] / df.shape[0]
            dic[0.9] = idx5.shape[0] / df.shape[0]
            dic[1.0] = idx6.shape[0] / df.shape[0]
            percent[d] = dic
        return percent

    def process_hr(self, df):
        df = self.merge_bp_hr(df)
        data = df.drop(columns = ["diastolic", "systolic"])
        data = data.set_index("start_time")
        new = data.transpose()
        new.index = [x + " of max hr" for x in new.index]
        return new

    def plot_hr_bp_2(self, DF):
        new = self.process_hr(DF)
        sns.set(context = 'notebook', style = "white", palette = "Reds")
        ax1 = new.set_index(new.index).T.plot(kind = 'bar', stacked = True, \
                                             figsize = (20, 10), grid = False)
        ax1.tick_params(axis='y', labelcolor = "orange")
        ax1.legend(fontsize = 14, loc = 4)
        ax1.set_ylabel('Daily Heart Rate Zone', color = "orange", fontsize = 18, weight = "bold")
        ax1.set_title("Daily Heart Rate Zone vs Blood Pressure", fontsize = 18, weight = "bold")
        ax1.set_ylim([0, 2.0])
        ax1.set_xlabel("Heart Rate Zone", fontsize = 16, weight = "bold")
        ax1.set_xticks(range(0, len(new.columns) + 2, 2))
        ax1.set_xticklabels(new.columns[::2], fontsize = 14)
        ax1.set_yticks(np.arange(0, 1.25, 0.25))
        ax1.set_yticklabels(np.arange(0, 1.25, 0.25), fontsize = 14, weight = "bold")
        ax1.text(len(new.columns) - 8, 1.5, "Max Heart Rate = 220 - Age", fontsize  = 14, weight = "bold")

        ax2 = ax1.twinx() 
        ax2.tick_params(axis='y', labelcolor = "indianred")
        x = range(len(new.columns))
        df = self.merge_bp_hr(DF)
        ax2.plot(x, df["diastolic"], color = "orange", label = "diastolic")
        ax2.plot(x, df["systolic"], color = "indianred", label = "systolic")
        ax2.legend(fontsize = 18, loc = 1)
        ax2.set_ylabel('Blood Pressure', color = "indianred", fontsize = 18, weight = "bold")
        ax2.tick_params(axis='y', labelcolor = "indianred")
        ax2.set_ylim([0, 150])
        ax2.set_yticks(range(0, 150, 20))
        ax2.set_yticklabels(range(0, 150, 20), fontsize = 14, weight = "bold")

        plt.tight_layout()
        plt.show()

    def process_walk_distance(self, df):
        dist = df.groupby("day").describe()["distance"]
        dist1 = pd.DataFrame(dist, index = dist.index, columns = ["count", "mean"])
        dist1["total"] = dist1["count"] * dist1["mean"]
        dist1["day"] = dist1.index
        dist1.index = range(len(dist1))
        dist1 = dist1.drop(columns = ["count", "mean"])
        idx = np.argwhere(dist1["total"] < 1000)
        dist = dist1.drop(index = idx.reshape(len(idx), ))
        return dist

    def plot_bp_dist(self, dist):
        bp = self.bp
        dist.columns = ["total", "start_time"]
        df = pd.merge(bp, dist, how = "inner", on = "start_time")
        fig, ax1 = plt.subplots(figsize = (15, 7))
        ax1.set_ylabel('Daily Walk Distance', color = "darkslategray", fontsize = 16)
        ax1.set_title("Daily Walk Distance vs Blood Pressure", fontsize = 16, weight = "bold")
        ax1.bar(range(len(df)), df["total"], color = "lightslategray", label = "Total Daily Distance")
        ax1.legend(fontsize = 12, loc = 4)
        ax1.tick_params(axis='y', labelcolor = "darkslategray")
        ax1.set_ylim([0, 30000])
        ax2 = ax1.twinx() 
        ax2.plot(range(df.shape[0]), df["diastolic"], color = "orange", label = "diastolic")
        ax2.plot(range(df.shape[0]), df["systolic"], color = "indianred", label = "systolic")
        ax2.legend(fontsize = 12, loc = 2)
        ax2.set_ylabel('Blood Pressure', color = "red", fontsize = 16)
        ax2.tick_params(axis='y', labelcolor = "red")
        ax2.set_ylim([0, 150])
        ax1.set_xticks(range(0, df.shape[0] + 2, 2))
        ax1.set_xticklabels(df["start_time"].iloc[::2], rotation = 40, fontsize = 14)
        plt.tight_layout()
        plt.savefig("kmlVisual/dist_bp.png")
        plt.show()
        return df

    def plot_bp_dist_reg(self, df):
        dist = self.process_walk_distance(df)
        dist_bp = self.plot_bp_dist(dist)
        plt.figure(figsize = (7, 5))
        plt.title("Daily Walk Distance vs Blood Pressure", fontsize = 16, weight = "bold")
        sns.regplot("total", "systolic", dist_bp, color = "lightskyblue", label = "systolic")
        sns.regplot("total", "diastolic", dist_bp, color = "lightpink", label = "diastolic")
        plt.ylabel("Blood Pressure", fontsize = 14, weight = "bold")
        plt.xlabel("Walk Distance", fontsize = 14, weight = "bold")
        plt.legend(fontsize = 12)
        plt.tight_layout()
        plt.show()


    def sedentary_time(self, df):
        s_time = {}
        days = set(df.day.unique())
        for d in days:
            idx = np.argwhere(df["day"] == d)
            day = df.iloc[idx.reshape(len(idx), )]
            day.index = range(len(day))
            idx = np.argwhere(day["count"] > 0)
            walk = day.iloc[idx.reshape(len(idx), )]
            s_time[d] = 1 - len(walk.start_time.dt.hour.unique()) / len(day.start_time.dt.hour.unique())
        return s_time

    def plot_sed_bp(self, df):
        s_time = self.sedentary_time(df)
        bp = self.bp
        sed = pd.DataFrame(index = range(len(s_time)), columns = ["start_time", "sedentary_time"])
        sed["start_time"] = sorted(s_time.keys())
        sed["sedentary_time"] = sed["start_time"].apply(lambda x: s_time[x])
        df = pd.merge(bp, sed, how = "inner", on = "start_time")
        fig, ax1 = plt.subplots(figsize = (15, 7))
        ax1.set_ylabel('Daily Proportion of Sedentary Time', color = "darkslategray", fontsize = 16)
        ax1.set_title("Daily Proportion of Sedentary Time vs Blood Pressure", fontsize = 16, weight = "bold")
        ax1.bar(range(len(df)), df["sedentary_time"], color = "lightblue", label = "Total Daily Distance")
        ax1.legend(fontsize = 12, loc = 4)
        ax1.tick_params(axis='y', labelcolor = "darkslategray")
        ax1.set_yticks(np.arange(0, 1.2, 0.2))
        ax1.set_yticklabels(["{:.1f}% of day".format(x) for x in np.arange(0, 1.2, 0.2)], fontsize = 14)
        ax1.set_ylim([0, 1.5])
        ax2 = ax1.twinx() 
        ax2.plot(range(df.shape[0]), df["diastolic"], color = "orange", label = "diastolic")
        ax2.plot(range(df.shape[0]), df["systolic"], color = "indianred", label = "systolic")
        ax2.legend(fontsize = 12, loc = 2)
        ax2.set_ylabel('Blood Pressure', color = "red", fontsize = 16)
        ax2.tick_params(axis='y', labelcolor = "red")
        ax2.set_ylim([0, 150])
        ax1.set_xticks(range(0, df.shape[0] + 2, 2))
        ax1.set_xticklabels(df["start_time"].iloc[::2], rotation = 40, fontsize = 14)
        plt.tight_layout()
        plt.show()
        return df

    def plot_sed_bp_reg(self, df):
        sed_bp = self.plot_sed_bp(df)
        plt.figure(figsize = (7, 5))
        plt.title("Proportion of Sedentary Time vs Blood Pressure", fontsize = 16, weight = "bold")
        sns.regplot("sedentary_time", "systolic", sed_bp, color = "mediumturquoise", label = "systolic")
        sns.regplot("sedentary_time", "diastolic", sed_bp, color = "lightgreen", label = "diastolic")
        plt.ylabel("Blood Pressure", fontsize = 14, weight = "bold")
        plt.xlabel("Proportion of Sedentary Time", fontsize = 14, weight = "bold")
        plt.legend(fontsize = 12)
        plt.tight_layout()
        plt.show()

    def plot_stg_bp_reg(self, df):
        stg = pd.DataFrame(df, columns = ["start_time", "stage"])
        stg["start_time"] = stg["start_time"].dt.date
        stg["stage"] = stg["stage"].apply(lambda x: x if x > 1 else 1)
        stg_bp = pd.merge(stg, self.bp, how = "inner", on = "start_time")

        plt.figure(figsize = (7, 5))
        plt.title("Sleep Stage vs Blood Pressure", fontsize = 16, weight = "bold")
        sns.regplot("stage", "systolic", stg_bp, color = "deepskyblue", label = "systolic")
        sns.regplot("stage", "diastolic", stg_bp, color = "purple", label = "diastolic")
        plt.ylabel("Blood Pressure", fontsize = 14, weight = "bold")
        plt.xlabel("Sleep Stage", fontsize = 14, weight = "bold")
        plt.xticks(range(0, 5, 1), ["", "Awake", "Light Sleep", "Deep Sleep", "REM"], fontsize = 14)
        plt.xlim([0, 5])
        plt.legend(fontsize = 12)
        plt.tight_layout()
        plt.show()

