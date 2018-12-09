#!/usr/bin/env python3
"""
Project myJobs by Zachary Gale
Analytics personalized.

myJobs, a simple and straightforward way to collect and determine trending jobs
no matter where you want to work.
"""
#built in libraries
import datetime as DT
import os
import platform  # detect o/s
import re
import subprocess  # open default program
import sys
import time
from pathlib import Path  # deals with paths between operating systems
from pathlib import PureWindowsPath

# 3rd party
import matplotlib.pyplot as plt  # plotting
import numpy as np  # NaN
import pandas as pd  # dataframes
import requests  # access URL
import seaborn as sns  # plotting
from bs4 import BeautifulSoup  # webscraping


def main():
    '''main function, provides user menu and settings to adjust for set searches
    '''

    # max results per city when scraping multiple locations
    maxCity_set = 150

    # Modify and use when gathering data from multiple areas
    citySet = [
        'Dallas', 'Arizona', 'Washington', 'Iowa', 'California', 'New+York'
    ]

    # set columns for dataframe
    columns = ['jobTitle', 'company', 'location', 'summary', 'salary', 'date']
    # create our dataframe
    df = pd.DataFrame(columns=columns)

    # ask if users wants to use set
    useSet = input("Use city set?(y,n): ")
    # get job search
    jobSearch = input("Job title/search term: ")
    jobSearch = jobSearch.replace(" ", "+")  # we need + in job search terms
    # check if cityset
    if useSet is 'y':
        scrapIndeed_set(df, citySet, maxCity_set, jobSearch)
    else:

        # ask for city name
        cityName = input(
            "Enter city, state, or zipcode to check for job postings: ")

        # ask max city results
        maxCity = input("Maximum results per city (multiples of 50): ")

        scrapIndeed(df, cityName, int(maxCity), jobSearch)

    # inform user when done
    print("Job done.\n")

    # ask to save data
    saveFile = input("Would you like to save the data to cvs?(y,n): ")
    if saveFile is 'y':
        filePath = getPath("Path to save file: ")
        fileName = input("File name: ")
        saveData(df, os.path.join(filePath, fileName))

        # ask if user wants to open
        openFile = input("Open saved data now?(y,n): ")

        newFile = os.path.join(filePath, fileName) + ".csv"
        # if yes open
        if openFile is 'y':  # check which os we are on
            if sys.platform.startswith('darwin'):  # mac
                subprocess.call(('open', newFile))
            elif os.name == 'nt':  # Windows
                os.startfile(newFile)
            elif os.name == 'posix':  # Linux,possibly mac.
                subprocess.call(('xdg-open', newFile))

    # create menu when done
    while True:
        print("1: Data summary" + "\n2. Job count by date" +
              "\n3. Job title by count" + "\n4. Time series plot" +
              "\n5. Top 10 jobs chart" + "\n0. Exit.")
        option = input("Option: ")

        if option is '1':
            dataSummary(df)  # basic summary
        elif option is '2':
            dataCount(df)  # job count
        elif option is '3':
            titleCount(df)  # quick title count
        elif option is '4':
            timeSeries(df)  # time series chart
        elif option is '5':
            titleChart(df)  # title chart
        elif option is '0':
            sys.exit(0)
        else:
            print("Invalid choice, try again.\n")


def scrapIndeed(df, cityName, maxCity, jobSearch):#TODO-> separate functions
    '''scrapIndeed takes user input and searches indeed for jobs

    Arguments:
        df dataframe -- dataframe where all scraped data is stored
        cityName string -- name of city to search in
        maxCity string -- maximum number of search results scraped
        jobSearch string -- term to query
'''
    citySet = [cityName]  # temp fix
    for city in citySet:
        for pCount in range(0, maxCity, 50):
            page = requests.get(  # page to search starting at 0, incrementing by 50 which is 1
                'https://www.indeed.com/jobs?q=' + \
                jobSearch + '&l=' + str(city)
                + '&radius=50&limit=50&fromage=30&start=' + str(pCount))

            time.sleep(1)  # 1 second between page grabs
            soup = BeautifulSoup(page.text,
                                 'lxml')  # lxml -> speed set no encoding
            for div in soup.find_all(name='div', attrs={'class': 'row'}):
                # row num for index of job
                num = (len(df) + 1)
                # Empty list to hold the data for each job posted
                jobPost = []

                # grab job title
                for a in div.find_all(
                        name='a', attrs={'data-tn-element': 'jobTitle'}):
                    jobPost.append(a['title'])

                # grab company name
                company = div.find_all(name='span', attrs={'class': 'company'})
                if len(company) > 0:
                    for b in company:
                        jobPost.append(b.text.strip())
                else:
                    sec_try = div.find_all(
                        name='span', attrs={'class': 'result-link-source'})
                    for span in sec_try:
                        jobPost.append(span.text.strip())

                # grab location name
                location = []
                # locations have issues and show up in both span/div location/vjs-loc
                # try multiple areas
                # TODO-> optimizations
                try:
                    c = div.findAll(name='span', attrs={'class': 'location'})
                    for span in c:  # search span -> location
                        location.append(span.text.strip())

                except:
                    c = div.findAll(name='span', attrs={'class': 'vjs-loc'})
                    for span in c:  # search span -> vjs-loc
                        location.append(span.text.strip())

                try:
                    c = div.findAll(name='div', attrs={'class': 'location'})
                    for span in c:  # search div -> location
                        location.append(span.text.strip())

                except:
                    c = div.findAll(name='div', attrs={'class': 'vjs-loc'})
                    for span in c:  # search div -> vjs-loc
                        location.append(span.text.strip())

                if len(location) >= 1:  # only append first location
                    jobPost.append(location[0])
                else:  # N/A if none found
                    jobPost.append("N/A")

                # Get summary information
                # \w for chars/nums + for multiple and space in our group ()
                d = div.find(name='span', attrs={'class': 'summary'})
                summaryText = "".join(re.findall(r"(\w+ )", d.text.strip()))
                jobPost.append(summaryText)

                # grabbing salary
                salaries = div.findAll(name='span', attrs={'class': 'sjcl'})
                salary = None
                # \d{2,3},\d{1,3} grab digits such as 100,000 or 50,000
                for pay in salaries:
                    salary = re.findall(r"\d{2,3},\d{1,3}", pay.text.strip())
                if not salary:
                    jobPost.append('N/A')
                elif len(salary) > 1:  # force string for now
                    payRange = str(salary[0]) + "-" + str(salary[1])
                    jobPost.append(payRange)
                else:
                    jobPost.append(str(salary))

                # date
                postDate = div.find(name='span', attrs={'class': 'date'})

                try:
                    checkDate = "".join(postDate.text.strip())

                    if "hour" in checkDate:  # if an hour ago set today
                        newDate = DT.date.today()
                    elif "hours" in checkDate:  # if hours ago set today
                        newDate = DT.date.today()
                    else:  # subtrack days from today and set date
                        newDate = "".join(re.findall(r"(\d+)", checkDate))
                        newDate = DT.date.today() - DT.timedelta(
                            days=int(newDate))
                except:
                    newDate = np.nan

                jobPost.append(newDate)

                # appending list of job post info to dataframe at index num
                df.loc[
                    num] = jobPost  # loc allows access to rows/columns by labels


def scrapIndeed_set(df, citySet, maxCity_set, jobSearch):
    '''scrapIndeed takes user input and searches indeed for jobs

Arguments:
    df dataframe -- dataframe where all scraped data is stored
    citySet string -- name of cities to search in
    maxCity_set string -- maximum number of search results scraped
    jobSearch string -- term to query
'''
    for city in citySet:
        for pCount in range(0, maxCity_set, 50):
            page = requests.get(  # page to search starting at 0, incrementing by 50 which is 1
                'https://www.indeed.com/jobs?q=' + \
                jobSearch + '&l=' + str(city)
                + '&radius=50&limit=50&fromage=30&start=' + str(pCount))
            time.sleep(1)  # 1 second between page grabs
            soup = BeautifulSoup(page.text,
                                 'lxml')  # lxml -> speed set no encoding
            for div in soup.find_all(name='div', attrs={'class': 'row'}):
                # row num for index of job
                num = (len(df) + 1)
                # Empty list to hold the data for each job posted
                jobPost = []

                # grab job title
                for a in div.find_all(
                        name='a', attrs={'data-tn-element': 'jobTitle'}):
                    jobPost.append(a['title'])

                # grab company name
                company = div.find_all(name='span', attrs={'class': 'company'})
                if len(company) > 0:
                    for b in company:
                        jobPost.append(b.text.strip())
                else:
                    sec_try = div.find_all(
                        name='span', attrs={'class': 'result-link-source'})
                    for span in sec_try:
                        jobPost.append(span.text.strip())

                # grab location name
                location = []
                # locations have issues and show up in both span/div location/vjs-loc
                # try multiple areas
                # TODO-> optimizations
                try:
                    c = div.findAll(name='span', attrs={'class': 'location'})
                    for span in c:  # search span -> location
                        location.append(span.text.strip())

                except:
                    c = div.findAll(name='span', attrs={'class': 'vjs-loc'})
                    for span in c:  # search span -> vjs-loc
                        location.append(span.text.strip())

                try:
                    c = div.findAll(name='div', attrs={'class': 'location'})
                    for span in c:  # search div -> location
                        location.append(span.text.strip())

                except:
                    c = div.findAll(name='div', attrs={'class': 'vjs-loc'})
                    for span in c:  # search div -> vjs-loc
                        location.append(span.text.strip())

                if len(location) >= 1:  # only append first location
                    jobPost.append(location[0])
                else:  # N/A if none found
                    jobPost.append("N/A")

                # Get summary information
                # \w for chars/nums + for multiple and space in our group ()
                d = div.find(name='span', attrs={'class': 'summary'})
                summaryText = "".join(re.findall(r"(\w+ )", d.text.strip()))
                jobPost.append(summaryText)

                # grabbing salary
                salaries = div.findAll(name='span', attrs={'class': 'sjcl'})
                salary = None
                # \d{2,3},\d{1,3} grab digits such as 100,000 or 50,000
                for pay in salaries:
                    salary = re.findall(r"\d{2,3},\d{1,3}", pay.text.strip())
                if not salary:
                    jobPost.append('N/A')
                elif len(salary) > 1:  # force string for now
                    payRange = str(salary[0]) + "-" + str(salary[1])
                    jobPost.append(payRange)
                else:
                    jobPost.append(str(salary))

                # date
                postDate = div.find(name='span', attrs={'class': 'date'})

                try:
                    checkDate = "".join(postDate.text.strip())

                    if "hour" in checkDate:  # if an hour ago set today
                        newDate = DT.date.today()
                    elif "hours" in checkDate:  # if hours ago set today
                        newDate = DT.date.today()
                    else:  # subtrack days from today and set date
                        newDate = "".join(re.findall(r"(\d+)", checkDate))
                        newDate = DT.date.today() - DT.timedelta(
                            days=int(newDate))
                except:
                    newDate = np.nan

                jobPost.append(newDate)

                # appending list of job post info to dataframe at index num
                df.loc[
                    num] = jobPost  # loc allows access to rows/columns by labels


def saveData(df, file):
    # save df to cvs, no safety checks this version
    df.to_csv(file + '.csv', encoding='utf-8')


# verify provided path or get path from user
def getPath(text, path=None):
    # if userFile defaults to None ask for file name
    if not path:
        path = input(text)

    while True:  # check path
        path = Path(path)  # set path to work for current os
        if str(path) == ".":  # current directory
            return os.getcwd()
        elif os.path.exists(path):  # return a valid path
            return path
        else:
            print("You entered: ", path, " which does not seem to exist")
            path = input("enter new path or 0 to exit: ")

            if path == "0":
                sys.exit(0)


def dataSummary(df):
    # print basic summary
    print(df.describe())


def dataCount(df):
    # print by date/count
    print(df.groupby('date').count())


def titleCount(df):
    # print by jobtitle/count
    print(pd.value_counts(df['jobTitle'].values, sort=True))


def timeSeries(df):
    # line/ts chart
    df['date'].value_counts()[0:].plot(
        grid=True, rot=90, title="Jobs posted over time")
    plt.xlabel("Date")
    plt.ylabel("Jobs posted")
    plt.tight_layout()
    plt.show()  # show time series plot
    plt.clf()  # clear and close plot
    plt.close()


def titleChart(df):
    # bar graph using seaborn
    sns.set()  # prep sb
    catPlot = sns.countplot(  # setup our catagorical plot
        x="jobTitle",
        hue="jobTitle",
        hue_order=pd.value_counts(df['jobTitle']).iloc[:10].index,
        data=df,
        order=pd.value_counts(df['jobTitle']).iloc[:10].index).plot()

    # set x/y labels and remove xticks and adjust legend
    plt.ylabel("Jobs posted")
    plt.xlabel("Job title")
    noTicks = []
    plt.xticks(noTicks)
    plt.legend(title="Job title", ncol=2, loc='upper right')
    plt.show()  # show barchart
    plt.clf()  # clear and close plot
    plt.close()


# call main at the end
if __name__ == '__main__':
    main()
