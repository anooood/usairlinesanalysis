from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import csv
import sys
import sqlite3
import requests
import regex as re
import glob
import scipy
from scipy import stats
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import statistics

def analysis(file1, file2, file3):

    #Ranking Airlines based on Ticket Price (Calculation of Z-Scores)

    file = open(file1)

    Airline_Price_List = []
    for line in file:
        dictt = {}
        airline = re.findall(r'(\w+\s?\w+):',line)
        price = re.findall(r'\s\$(\d+)',line)
        index = 0
        while index < len(airline):
            dictt[airline[index]] = price[index]
            index += 1
        if len(airline) != 0:
            Airline_Price_List.append(dictt)

    Airline_Price_List_Ordered = []

    for dictt in Airline_Price_List:
        ordered_list = []
        for k, v in dictt.items():
            ordered_list.append((int(v), k))
            ordered_list = sorted(ordered_list)
        Airline_Price_List_Ordered.append(ordered_list)

    for List in Airline_Price_List_Ordered:
        prices = []
        for Tuple in List:
            prices.append(Tuple[0])

    Airline_ZScores = []
    for List in Airline_Price_List_Ordered:
        prices = []
        z_scores = []
        for Tuple in List:
            prices.append(Tuple[0])
        mean = sum(prices)/len(prices)
        stdev = statistics.stdev(prices)
        for Tuple in List:
            if stdev != 0:
                z_score = float(Tuple[0]-mean)/float(stdev)
            else:
                z_score = 0
            z_scores.append(z_score)
        Airline_ZScores.append(z_scores)

    Airline_dict = {}

    for List in Airline_Price_List_Ordered:
        index1 = Airline_Price_List_Ordered.index(List)
        for Tuple in List:
            index2 = List.index(Tuple)
            if Tuple[1] in Airline_dict:
                Airline_dict[Tuple[1]].append(Airline_ZScores[index1][index2])
                continue
            Airline_dict[Tuple[1]] = list()
            Airline_dict[Tuple[1]].append(Airline_ZScores[index1][index2])

    Avg_zscore_ranked = []
    for k, v in Airline_dict.items():
        avg_zscore = sum(v)/len(v)
        Avg_zscore_ranked.append((k,avg_zscore))
        Avg_zscore_ranked = sorted(Avg_zscore_ranked, key = lambda x: x[1])

    df = pd.DataFrame(Avg_zscore_ranked,columns=["Airline","Price Z-Score (Avg)"])
    df.insert(0,'Rank',[1,2,3,4,5,6,7,8],True)
    df = df.set_index("Airline")

    #Obtaining Airline Statistics (Cancellations, Delay, Accidents)

    connection = sqlite3.connect(file2)
    cur = connection.cursor()

    cur.execute('SELECT DISTINCT Airline_Name FROM Flight_Data')
    airlines_db = cur.fetchall()
    Airline_Stats = []

    for airline in airlines_db:
        total_flights = 0
        cancelled = 0
        delayed = []

        for row in cur.execute("SELECT * FROM Flight_Data where Airline_Name=?",(airline[0],)):
            total_flights += 1
            if row[4] == 'cancelled':
                cancelled += 1
            if row[5] != 'NULL':
                delayed.append(row[5])
                
        avg_delay = sum(delayed)/len(delayed)
        prop_cancelled = (cancelled/total_flights)*100

        Airline_Stats.append((airline[0], total_flights, cancelled, prop_cancelled, avg_delay))

    file = open(file1)

    airlines_list = []
    for line in file:
        airlines = re.findall('(\w+\s?\w+):',line)
        for airline in airlines:
            if airline not in airlines_list:
                airlines_list.append(airline)

    New_Airline_Stats = []

    for airline in airlines_list:
        for airline_db in Airline_Stats:
            if re.findall('\w+',airline)[0] == re.findall('\w+',airline_db[0])[0]:
                New_Airline_Stats.append((airline,airline_db[1],airline_db[2],airline_db[3],airline_db[4]))
                continue

    cur.execute('SELECT DISTINCT Airline_Name FROM Flight_Data')
    airlines_db = cur.fetchall()

    df2 = pd.DataFrame(New_Airline_Stats,columns=["Airline","Total Flights","Cancelled Flights","Cancellation Ratio (%)","Average Delay (mins)"])
    df2 = df2.set_index('Airline')
    df2.index = df2.index.str.strip()
    df2 = df2.reindex(list(df.index.values))

    key = '85f523-f4a659'
    url = 'https://aviation-edge.com/v2/public/airlineDatabase?key=' + key + '&codeIso2Country=US'
    response = requests.get(url).json()

    Airline_data = []

    for airline in airlines_db:
        airline_name = airline[0]
        for dictt in response:
            if dictt['nameAirline'] == airline_name:
                Airline_data.append((dictt['nameAirline'],dictt['founding']))
                
    connection = sqlite3.connect(file3)
    cur = connection.cursor()

    cur.execute('''UPDATE Airplane_Crashes SET Operator = ? WHERE Operator is "United Air Lines"''', ('United Airlines',))
    connection.commit()

    Accidents = []

    for airline in Airline_data:
        cur.execute("SELECT * FROM Airplane_Crashes WHERE Operator=?",(airline[0],))
        Accidents.append((airline[0],airline[1],len(cur.fetchall())))

    connection.close()

    df3 = pd.DataFrame(Accidents,columns=["Airline","Year Founded","Number of Accidents"])
    df3 = df3.replace(['Delta Air Lines','Spirit'],['Delta','Spirit Airlines'])
    df3 = df3.set_index('Airline')
    df3.index = df3.index.str.strip()
    df3 = df3.reindex(list(df.index.values))

    #Combining Datasets into One

    df_final = pd.concat([df, df2, df3], axis=1)
    df_final = df_final.drop(columns='Year Founded')
    print("Combined Dataset: \n\n", df_final, "\n")

    #Calculating Correlations (Pearson's r Coefficients)

    x1 = df_final['Rank']
    y1 = df_final['Cancellation Ratio (%)']
    x2 = df_final.index
    corr1 = scipy.stats.pearsonr(x1,y1)[0]
    p_val1 = scipy.stats.pearsonr(x1,y1)[1]
    print('Analysis 1: Airline Price Ranking vs Cancellation Rate [%]:\n','Pearson\'s r Coefficient: ', corr1, '\n P-Value: ', p_val1)
    print(' Scatter plot results are shown in: Figure 1')
    print(' Bar chart results are shown in: Figure 2')

    x3 = df_final['Rank']
    y3 = df_final['Average Delay (mins)']
    corr2 = scipy.stats.pearsonr(x3,y3)[0]
    p_val2 = scipy.stats.pearsonr(x3,y3)[1]
    print('\nAnalysis 2: Airline Price Ranking vs Average Departure Delay [mins]:\n','Pearson\'s r Coefficient: ', corr2, '\n P-Value: ', p_val2)
    print(' Scatter plot results are shown in: Figure 3') 

    x4 = df_final['Rank']
    y4 = df_final['Number of Accidents']
    corr3 = scipy.stats.pearsonr(x4,y4)[0]
    p_val3 = scipy.stats.pearsonr(x4,y4)[1]
    print('\nAnalysis 3: Airline Price Ranking vs Aircraft Accidents [count]:\n','Pearson\'s r Coefficient: ', corr3, '\n P-Value: ', p_val3)
    print(' Scatter plot results are shown in: Figure 4\n')
    
    slope, intercept, r, p, stderr = scipy.stats.linregress(x1,y1)
    line = f'Regression line: y={intercept:.2f}+{slope:.2f}x, r={r:.2f}'
    fig, ax = plt.subplots(num=1)
    ax.plot(x1, y1, linewidth=0, marker='o',label='Data points', color='royalblue')
    ax.plot(x1, intercept + slope * x1, label=f'Regression Line, r={r:.2f}', color='red')
    ax.set_xlabel('Airline Price Rank',labelpad=15, fontsize=12)
    ax.set_ylabel('Percentage of Cancelled Flights [%]',labelpad=15, fontsize=12)
    ax.set_title('Cancellations vs Airline Price Rank')
    ax.legend(facecolor='white',fontsize=12)
    plt.gcf().set_size_inches(7, 5)
    plt.yticks(np.arange(0,13,1.0), fontsize=12)
    plt.xticks(fontsize=12)
    plt.show()

    fig, ax = plt.subplots(num=2)
    ax.bar(x2,y1,color='lightseagreen')
    ax.set_xlabel('US Airline',labelpad=15, fontsize=12)
    ax.set_ylabel('Percentage of Cancelled Flights [%]',labelpad=15, fontsize=12)
    ax.set_title('Percentage of Flights Cancelled for US Airlines (as per Dataset)')
    ax.set_axisbelow(True)
    ax.yaxis.grid(color='gray', linestyle='solid')
    plt.gcf().set_size_inches(13, 5)
    plt.yticks(np.arange(0,13,1.0), fontsize=12)
    plt.show()
      
    slope, intercept, r, p, stderr = scipy.stats.linregress(x3,y3)
    line = f'Regression line: y={intercept:.2f}+{slope:.2f}x, r={r:.2f}'
    fig, ax = plt.subplots(num=3)
    ax.plot(x3, y3, linewidth=0, marker='o', label='Data points', color='forestgreen')
    ax.plot(x3, intercept + slope * x3, label=f'Regression Line, r={r:.2f}',color='red')
    ax.set_xlabel('Airline Price Rank',labelpad=15, fontsize=12)
    ax.set_ylabel('Average Departure Delay [mins]',labelpad=15, fontsize=12)
    ax.set_title('Departure Delay vs Airline Price Rank')
    ax.legend(facecolor='white', fontsize=12)
    plt.gcf().set_size_inches(7, 5)
    plt.yticks(np.arange(0,45,5), fontsize=12)
    plt.xticks(fontsize=12)
    plt.show()

    slope, intercept, r, p, stderr = scipy.stats.linregress(x4,y4)
    line = f'Regression line: y={intercept:.2f}+{slope:.2f}x, r={r:.2f}'
    fig, ax = plt.subplots(num=4)
    ax.plot(x4, y4, linewidth=0, marker='o', label='Data points', color='darkviolet')
    ax.plot(x4, intercept + slope * x4, label=f'Regression Line, r={r:.2f}', color='red')
    ax.set_xlabel('Airline Price Rank',labelpad=15, fontsize=12)
    ax.set_ylabel('Number of Aircraft Accidents',labelpad=15, fontsize=12)
    ax.set_title('Aircraft Accidents vs Airline Price Rank')
    ax.legend(facecolor='white', fontsize=12)
    plt.gcf().set_size_inches(7, 5)
    plt.yticks(np.arange(0,60,10), fontsize=12)
    plt.xticks(fontsize=12)
    plt.show()   

def default_function():
    # Print datasets 1, 2, 3, and combined
    # Call analysis function, passing files as arguments
    # no return

    #Dataset 1: Scraping "Kayak" Website (Extra flight routes)

    Routes = (('JFK','LAX'),('LGA','ORD'),('ATL','MCO'),('ATL','FLL'),('DEN','PHX'),('LAX','SFO'),('LAS','LAX'),('LGA','MIA'),('JFK','MIA'),('HNL','LAX')
            ,('DEN','LAS'),('HNL','SFO'),('EWR','MCO'),('ATL','LGA'),('DEN','LAX'))

    Airline_Price_List = []

    chrome_options = webdriver.ChromeOptions()
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument('headless')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    s = Service(ChromeDriverManager(log_level=0).install())
    driver = webdriver.Chrome(service=s,options=chrome_options)
    driver.implicitly_wait(20)

    for route in Routes:

        origin = route[0]
        destination = route[1]
        startdate = "2022-06-01"

        url = "https://www.kayak.com/flights/" + origin + "-" + destination + "/" + startdate + "?sort=price_a&fs=stops=0"        
        driver.get(url)
        time.sleep(30) 

        soup=BeautifulSoup(driver.page_source, 'lxml')

        airlines = soup.find_all('div', attrs={'class': 'bottom', 'dir':'ltr'})

        while airlines is None:
            airlines = soup.find_all('div', attrs={'class': 'bottom', 'dir':'ltr'})

        airline = []

        for div in airlines:
            airline.append(div.getText().strip())

        regex = re.compile("Common-Booking-MultiBookProvider Theme-featured-large .*?")
        price_results = soup.find_all('div', attrs={'class': regex})

        price_list = []

        for result in price_results:
            price = result.getText().split('\n')[4].strip().replace('$','')
            price_list.append(price)

        flight_dict = dict()

        index = 0

        while index < len(price_list):
            if price_list[index].isnumeric():
                if airline[index] in flight_dict:
                    if int(price_list[index]) > flight_dict[airline[index]]:
                        index += 1
                        continue
                if airline[index] == 'Greyhound' or airline[index] == 'Amtrak':
                    index += 1
                    continue
                flight_dict[airline[index]] = int(price_list[index])
            index += 1

        Airline_Price_List.append(flight_dict)

    driver.close() 
    csv_columns = ["Route","Price 1","Price 2","Price 3","Price 4","Price 5","Price 6","Price 7","Price 8","Price 9"]

    with open('flight_prices_new.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(csv_columns)
        index = 0
        for dictt in Airline_Price_List:
            prices = []
            for k, v in dictt.items():
                prices.append(k + ": $" + str(v))
            route = Routes[index][0] + " to " + Routes[index][1]
            prices.insert(0, route)
            writer.writerow(prices)
            index += 1

    #Dataset 2: Scraping API Data (Extra flight dates)

    key = '85f523-f4a659'

    url1 = 'https://aviation-edge.com/v2/public/airlineDatabase?key=' + key + '&codeIso2Country=US'
    response1 = requests.get(url1).json()

    file = open('flight_prices_new.csv')
    airlines_list = []

    for line in file:
        airlines = re.findall('(\w+\s?\w+):',line)
        for airline in airlines:
            if airline not in airlines_list:
                airlines_list.append(airline)

    Airline_data = []

    for dictt in response1:
        for Airline in airlines_list:
            if dictt['nameAirline'].lower() == Airline.lower():
                Airline_data.append((dictt['nameAirline'],dictt['codeIataAirline'],dictt['codeHub']))
                airlines_list.remove(Airline)
            elif dictt['nameAirline'].lower() == (Airline+" "+"Airlines").lower() or dictt['nameAirline'].lower() == (Airline+" "+"Air lines").lower():
                Airline_data.append((dictt['nameAirline'],dictt['codeIataAirline'],dictt['codeHub']))
                airlines_list.remove(Airline)
            elif (dictt['nameAirline']+" "+"Airlines").lower() == Airline.lower():
                Airline_data.append((dictt['nameAirline'],dictt['codeIataAirline'],dictt['codeHub']))
                airlines_list.remove(Airline)

    connection = sqlite3.connect('flight_data_new.db')

    cur = connection.cursor()

    cur.execute("DROP table IF EXISTS Flight_Data")
    cur.execute('''CREATE TABLE IF NOT EXISTS Flight_Data (Flight_Number_IATA text, Flight_Date text, Airline_Name text, Departure_Airport text, Flight_Status text, Delay_mins int)''')

    for Airline in Airline_data:
        index = 0
        flight_dates = [('2021-07-01','2021-07-07'),('2021-08-01','2021-08-07'),('2021-11-21','2021-11-27'),('2021-12-21','2021-12-27')]
        while index < len(flight_dates):
            date_from = flight_dates[index][0]
            date_to = flight_dates[index][1]
            if Airline[0] == 'Spirit':
                airport_hub = 'FLL'
                url = 'http://aviation-edge.com/v2/public/flightsHistory?key=' + key + '&code=' + airport_hub + '&type=departure&date_from=' + date_from + '&date_to=' + date_to + '&airline_iata=' + Airline[1].lower()
            else:
                url = 'http://aviation-edge.com/v2/public/flightsHistory?key=' + key + '&code=' + Airline[2] + '&type=departure&date_from=' + date_from + '&date_to=' + date_to + '&airline_iata=' + Airline[1].lower()
            response = requests.get(url).json()
            try:
                response[0]
                for flight in response:
                    flight_date = flight['departure']['scheduledTime'][:10]
                    flight_number = flight['flight']['iataNumber']
                    departure_airport = flight['departure']['iataCode'].upper()
                    flight_status = flight['status']
                    try:
                        delay = flight['departure']['delay']
                    except:
                        delay = 'NULL'
                    insert_records = "INSERT INTO Flight_Data (Flight_Number_IATA, Flight_Date, Airline_Name, Departure_Airport, Flight_Status, Delay_mins) VALUES(?, ?, ?, ?, ?, ?)"
                    cur.executemany(insert_records, [(flight_number, flight_date, Airline[0], departure_airport, flight_status, delay)])
            except:
                try:
                    url = 'http://aviation-edge.com/v2/public/flightsHistory?key=' + key + '&code=' + Airline[2] + '&type=departure&date_from=' + date_from + '&date_to=' + date_to
                    response = requests.get(url).json()
                    new_response = []
                    for dictt in response:
                        if dictt['airline']['iataCode'] == Airline[1].lower():
                            new_response.append(dictt)
                except:
                    new_date_to = date_to[:-2]
                    day = int(date_to[-2:]) - 1
                    while True:
                        new_date_to = date_to[:-2]
                        if day >= 10:
                            new_date_to = new_date_to + str(day)
                        else:
                            new_date_to = new_date_to + "0" + str(day)
                        try:
                            url = 'http://aviation-edge.com/v2/public/flightsHistory?key=' + key + '&code=' + Airline[2] + '&type=departure&date_from=' + date_from + '&date_to=' + new_date_to
                            response = requests.get(url).json()  
                            new_response = []
                            for dictt in response:
                                if dictt['airline']['iataCode'] == Airline[1].lower():
                                    new_response.append(dictt)
                            break
                        except:
                            day = day - 1
                for flight in new_response:
                    flight_date = flight['departure']['scheduledTime'][:10]
                    flight_number = flight['flight']['iataNumber']
                    departure_airport = flight['departure']['iataCode'].upper()
                    flight_status = flight['status']
                    try:
                        delay = flight['departure']['delay']
                    except:
                        delay = 'NULL'
                    insert_records = "INSERT INTO Flight_Data (Flight_Number_IATA, Flight_Date, Airline_Name, Departure_Airport, Flight_Status, Delay_mins) VALUES(?, ?, ?, ?, ?, ?)"
                    cur.executemany(insert_records, [(flight_number, flight_date, Airline[0], departure_airport, flight_status, delay)])
            index += 1
        
    connection.commit()
    connection.close()

    #Dataset 3: Converting "Airplane Crash Data" CSV file to SQL

    connection = sqlite3.connect('airplane_crashes_new.db')
        
    cur = connection.cursor()

    cur.execute("DROP table IF EXISTS Airplane_Crashes")
    cur.execute('''CREATE TABLE IF NOT EXISTS Airplane_Crashes (Date date, Time time, Location text, Operator text, Flight_Number text, Route text, AC_Type text, Registration text, cn_In text, Aboard int, Aboard_Passengers int, Aboard_Crew int, Fatalities int, Fatalities_Passangers int, Fatalities_Crew int, Ground int, Summary text)''')

    file = open('airplane_crashes.csv')

    contents = csv.reader(file)

    insert_records = "INSERT INTO Airplane_Crashes (Date, Time, Location, Operator, Flight_Number, Route, AC_Type, Registration, cn_In, Aboard, Aboard_Passengers, Aboard_Crew, Fatalities, Fatalities_Passangers, Fatalities_Crew, Ground, Summary) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

    cur.executemany(insert_records, contents)
    sql_delete_query = """DELETE from Airplane_Crashes where Date = 'Date'"""
    cur.execute(sql_delete_query)
    connection.commit()
    connection.close()
    
    file1 = 'flight_prices_new.csv'
    file2 = 'flight_data_new.db'
    file3 = 'airplane_crashes_new.db'

    # Opening and Printing Datasets as DataFrames

    df_web = pd.read_csv(file1)
    df_web = df_web.dropna(axis=1,how='all')
    dimensions_web = df_web.shape

    connection = sqlite3.connect(file2)
    df_api = pd.read_sql_query("SELECT * from Flight_Data", connection)
    dimensions_api = df_api.shape
    pd.options.display.show_dimensions = False
    connection.close()

    connection = sqlite3.connect(file3)
    df_db = pd.read_sql_query("SELECT * from Airplane_Crashes", connection)
    dimensions_db = df_db.shape
    pd.options.display.show_dimensions = False
    connection.close()  

    print("\nPrinting Datasets Scraped:\n")
    print("Dataset 1: Scraping 'Kayak' Website for Flight Tickets\n\n", df_web, "\n\nDataset 1 dimensions: ", dimensions_web[0], "rows, ", dimensions_web[1], "columns", "\n\nDataset 2: Scraping 'Aviation Edge' API for Historical Flight Schedules\n\n", df_api, "\n\nDataset 2 dimensions: ", dimensions_api[0], "rows, ", dimensions_api[1], "columns", "\n\nDataset 3: Scraping 'Airplane Crashes' Database\n\n", df_db, "\n\nDataset 3 dimensions: ", dimensions_db[0], "rows, ", dimensions_db[1], "columns\n")

    analysis(file1,file2,file3)

def static_function():

    path_to_static_data = 'static_datasets/'
    file1 = path_to_static_data+'flight_prices.csv'
    file2 = path_to_static_data+'flight_schedules.db'
    file3 = path_to_static_data+'airplane_crashes.db'

    # Opening and Printing Datasets as DataFrames

    df_web = pd.read_csv(file1)
    df_web = df_web.dropna(axis=1,how='all')
    dimensions_web = df_web.shape

    connection = sqlite3.connect(file2)
    df_api = pd.read_sql_query("SELECT * from Flight_Data", connection)
    dimensions_api = df_api.shape
    pd.options.display.show_dimensions = False
    connection.close()

    connection = sqlite3.connect(file3)
    df_db = pd.read_sql_query("SELECT * from Airplane_Crashes", connection)
    dimensions_db = df_db.shape
    pd.options.display.show_dimensions = False
    connection.close()  

    print("\nPrinting Datasets Scraped:\n")
    print("Dataset 1: Scraping 'Kayak' Website for Flight Tickets\n\n", df_web, "\n\nDataset 1 dimensions: ", dimensions_web[0], "rows, ", dimensions_web[1], "columns", "\n\nDataset 2: Scraping 'Aviation Edge' API for Historical Flight Schedules\n\n", df_api, "\n\nDataset 2 dimensions: ", dimensions_api[0], "rows, ", dimensions_api[1], "columns", "\n\nDataset 3: Scraping 'Airplane Crashes' Database\n\n", df_db, "\n\nDataset 3 dimensions: ", dimensions_db[0], "rows, ", dimensions_db[1], "columns\n")

    analysis(file1,file2,file3)

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print("\nEntering Default Mode:")
        default_function()

    elif sys.argv[1] == '--static':
        print("\nEntering Static Mode:")
        static_function()