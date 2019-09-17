# Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation
[![Blood Pressure](https://img.shields.io/badge/Blood%20Pressure%20Data-Omron%20Wellness-orange)](https://www.omronwellness.com/Home/Landing)
[![Samsung Health](https://img.shields.io/badge/Health%20%26%20Fitness%20Data-Samsung%20Galaxy%20Watch-9cf)](https://www.samsung.com/au/support/mobile-devices/galaxy-watch-samsung-health/)
[![Project Status](https://img.shields.io/badge/Project%20Status-1st%20Stage-ff69b4)](https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation)



## Content Overview
* [Prerequisites](#Prerequisites)
* [Code Organization](#Code-Organization)
* [Dataset](#Dataset)
* [Data Visualization](#Data-Visualization)
* [Model Training](#Model-Training)

## Prerequisites
<pre>
1. numpy
2. pandas
3. matplotlib
4. requests
5. json
6. authlib
7. oauthlib
8. base64
9. csv
10. seaborn
11. sklearn 
12. pickle

</pre>

## Code Organization
<pre>
<b>DataRequestAndParsing: for requesting and parsing data </b><br>
  1. read_BP.ipynb: request and parse blood pressure data from Omron
  2. read_samsung_data.py: request and parse health and fitness data from Samsung
  3. new_data_merge.py: combine health and fitness features into one data frame
  
<b>DataUpdate: for regular data maintenance </b><br>
  1. refresh_omron_token.py: refresh tokens for accessing blood pressure data from Omron
  2. refresh_samsung_token.py: refresh tokens for accessing health and fitness data collected by Samsung Galaxy Watch
  3. update_info.py: create csv file with updated health and fitness data

<b>DataVisualization: for data visualization and exploration of correlation </b><br>
	1. visualize_merged_df.py: visualize different features and their underlying relationships
  2. visualize_merged_df.ipynb: for running the script with user index specified
  3. Results: folder of data visualizationr results
  
<b>ModelTraining: for training model to fit blood pressure, health and fitness data </b><br>
	1. aggregate_24h.py: aggregate data in past 24 hours based on the timestamp of each record of blood pressure measurement
  2. build_models.py: extract additional features, convert time form, interpolate data and prepare training model
  3. slp_duration.py: for processing sleep data and computing daily sleep duration
  4. slp_processing.py: for preprocessing sleep data
  
</pre>

## Dataset
- [Omron Blood Pressure Data](https://omronwellness.com/Home/Landing)<br>
  The mobile application <b>Omron Connects</b> helps to transfer the data from the BP monitors to the <b>Omron Cloud Service</b>. We could either download the data from <b>Omron Cloud Service</b> to our server or directly request the data from <b>Omron Connect</b> by OAuth authentication.
  - [diastolic](https://www.verywellhealth.com/systolic-and-diastolic-blood-pressure-1746075) 
  - [systolic](https://www.verywellhealth.com/systolic-and-diastolic-blood-pressure-1746075) 
- [Samsung Health Data](https://developer.samsung.com/health/partner-only/server/api/data-types)<br>
  For the access of data, the <b>Samsung Health</b> mobile application is connected to <b>Samsung Cloud Service</b>, from which we are able to download all related data
  - [calories](https://www.samsung.com/au/support/mobile-devices/galaxy-watch-samsung-health/)
  - [step count](https://developer.samsung.com/health/partner-only/server/api/data-types/step-count)
  - [floors](https://developer.samsung.com/health/partner-only/server/api/data-types/floors-climbed)
  - [exercise](https://developer.samsung.com/health/partner-only/server/api/data-types/exercise)
  - [sleep stage](https://developer.samsung.com/health/partner-only/server/api/data-types/sleep-stage)
  - [heart rate](https://developer.samsung.com/health/partner-only/server/api/data-types/heart-rate)
  - [step daily trend](https://developer.samsung.com/health/partner-only/server/api/data-types/daily-step-count-trend)
 
## Data Visualization
There are some examples demonstrated below.
- <b>Heart Rate Daily and Weekly Pattern</b> & <b>Heart Rate Stacked Plot vs Blood Pressure</b>
<p float="left">
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/heart_rate_weekly_pattern.png" width="400"/>
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/hr_stacked_plot2.png" width="400"/>
</p>


- <b>Daily Sleep Stage</b> & <b>Daily Sleep Duration vs Blood Pressure</b>
<p float="left">
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/daily_sleep_stage.png" width="350"/>
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/slp_bp.png" width="450"/>
</p>

- <b>Daily Step Count</b> & <b>Daily Step Count vs Blood Pressure</b>
<p float="left">
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/daily_step_count.png" width="350"/>
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/step_bp.png" width="450"/>
</p>

- <b> Exercise Event Visualization</b>

![Running](https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/running_trajectory.gif)
![Swimming](https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/swimming_trajectory.gif)

- <b>Daily Proporrion of Sedentary Time vs Blood Pressure</b>
<p float="left">
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/sedentary_bp.png" width="500"/>
  <img src="https://github.com/kwanmolee/Blood-Pressure-Prediction-and-Peronalized-Health-Behavior-Recommendation/blob/master/DataVisualization/Results/sedentary_bp_reg.png" width="300"/>
</p>

## Model Training
