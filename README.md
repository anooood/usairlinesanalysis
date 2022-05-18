# Analysis of US Airlines

# INTRODUCTION:
---------------

In this project, I am interested in studying the relationship between cost of flight tickets and airline performance. Are US flights operated by cheap airlines more likely to have their flights delayed or cancelled? and are they more likely to be involved in accidents?

To answer the above questions, I am using datasets from three different sources as follows:

1) Scraping Flights Tickets Information from “Kayak” Website (Link: https://www.kayak.com/flights)

2) Flight Delay API from "Aviation Edge" – Current & Historical Cancellations and Delays (Link: https://aviation-edge.com/flight-delay-api/) 

3) Airplane Crash Data Since 1908 (CSV dataset from "Kaggle") (Link: https://www.kaggle.com/datasets/cgurkan/airplane-crash-data-since-1908)
   Although this dataset is a ready-made CSV dataset, I have stored it in a SQL database for this project (original CSV file "airplane_crashes.csv" can be found in the main folder).  

In Homework 4, three static datasets were created, one in the CSV format "flight_tickets.csv" and the other two are in the SQL database format "flight_data.db" and "airplane_crashes.db". 

For Homework 5, the analysis is performed on the combined dataset, it is recommended to run the analysis in the "Static" mode.

# REQUIREMENTS:
---------------

The following Python modules are required to be installed in order to run the code: selenium, webdriver-manager, beautifulsoup4, regex, pandas, pysqlite3, requests, glob2, lxml, scipy, statistics, matplotlib, and numpy.

To install the above packages run the following command in terminal: pip install -r requirements.txt

'requirements.txt' file has a list of all the necessary packages required to run this code


# HOW TO RUN CODE:
------------------

The code "scraper_analysis.py" can be run in the following two modes (it's recommended to run in "Static" mode):

1) Static Mode (Command line to run: python scraper_analysis.py --static)

This mode first outputs all the static datasets that were created after scraping the three data sources. There are a total of three static datasets located in the path "static_datasets/". For the first dataset, the output of scarping is a CSV file "flight_tickets.csv", which is fully printed in this mode as a Dataframe. For the second dataset, the output is a SQL database file "flight_data.db", which is printed partially as a Dataframe along with its dimensions. The output of the third dataset is also a SQL database file "airplane_crashes.db", printed partially as a Dataframe along with its dimensions.

After printing the static datasets, the "static" mode calls another function called "analysis", which takes in the three static datasets in order to perform the analyses. Z-score calculations are first performed to find out airline price rankings (as detailed in the write-up "Project Description.pdf"). Then, the combined dataset is printed, which integrates all the required data from the three different sources together. Finally, the analysis is performed on the combined dataset. Three correlational analyses were performed, the results of each analysis is printed in terminal, which consists of: Pearson's r Coefficient, P-Value, and at least one Figure. For the Figures, the current window displayed must first be closed in order to see the next Figure.


2) Default Mode (Command line to run: python scraper_analysis.py)

This mode scrapes all the required data from the three sources (the whole process takes around 15 minutes). For the the first dataset (web scraping), the output is a CSV file "flight_tickets_new.csv" containing a table of flight ticket prices offered by different US airlines for 15 flight routes that are defined as input in the script. The routes are assumed to be one-way and non-stop, with a departure date on June 1st, 2022. For the second dataset (API), the output is a SQL database "flight_data_new.db" containing a table of historical flight schedules for all airlines that exist in the CSV file from dataset 1. The historical schedule is taken from 4 different weeks in 2021, as described in the write-up. As for the third dataset (CSV dataset), the code converts the original CSV file into a SQL database table "airplane_crashes_new.db" containing records of previous aircraft accidents from 1908 to 2019. All outputs are printed as Dataframes along with their dimensions.

After printing the newly scraped datasets, the "default" mode calls the function "analysis", which takes in the three datasets created in order to perform the analyses. Z-score calculations are first performed to find out airline price rankings (as detailed in the write-up "Project Description.pdf"). Then, the combined dataset is printed, which integrates all the required data from the three different sources together. Finally, the analysis is performed on the combined dataset. Three correlational analyses were performed, the results of each analysis is printed in terminal, which consists of: Pearson's r Coefficient, P-Value, and at least one Figure. For the Figures, the current window displayed must first be closed in order to see the next Figure.

# EXTENSIBILITY AND MAINTAINABILITY:
------------------------------------

The code can be further extended or generalized in several ways. For example, in scraping the “Kayak” website, additional flight routes can be added to further confirm the trend of which airlines typically offer cheaper tickets and which ones are more expensive. As for using the API from "Aviation Edge", the code currently scrapes flight schedules for specific airports at specific periods in time. This can be further extended by modifying the code to get data from additional airports or dates in order to grow the database. 

As for maintainability, since I was given a free developer API key by the "Aviation Edge" sales team, the API call limit is 30,000 calls, which is more than sufficient for the purposes of this project. However, due to high airport traffic in some busy airports, I can only extract historical flight schedules for up to 1 week in some cases. Additionally, in scraping the "Kayak" website, one should keep in mind that the prices of flight tickets are always changing and are never fixed. Thus, the flight fares in the static dataset "flight_tickets.csv" are most likely to be outdated. 


