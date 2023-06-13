#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import datetime
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pandas as pd
from time import sleep
import warnings

# Defaults
i_plot = True
i_sort = "cit/year"  # Way to be sorted. can be 'cit/year'
i_n_results = 250  # Results to fetch
i_s_year = 2003  # Starting year of results
i_e_year = datetime.datetime.now().year  # Ending year of results
MAX_CSV_FNAME = 255

# Don't touch
# i_csv_path = './' + "CSVs/"
i_csv_path = "CSVs/"
i_keyword_list = list()
for file in os.listdir('keywords/'):
    if file.endswith(".txt"):
        with open('keywords/'+str(file), 'rt') as kw_file:
            kw_s = kw_file.readlines()
            for i in range(len(kw_s)):
                if kw_s[i].endswith('\n'):
                    kw_s[i] = kw_s[i][0:-1]
            kw_b = ' '.join(kw_s)
            i_keyword_list.append(kw_b)


# Web_session
GSCHOLAR_URL = 'https://scholar.google.com/scholar?start={}&q={}&hl=en&as_sdt=0,5'
YEAR_RANGE = ''
STARTYEAR_URL = '&as_ylo={}'
ENDYEAR_URL = '&as_yhi={}'
ROBOT_KW = ['unusual traffic from your computer network', 'not a robot']


for i_keyword in i_keyword_list:
    def get_command_line_args(kw, cpath, plotting, sorting, articles, syear, eyear):
        keyword = kw
        csvpath = cpath
        sortby = sorting
        plot_results = plotting
        nresults = articles
        save_csv = True
        start_year = syear
        end_year = eyear
        debug = False
        return keyword, nresults, save_csv, csvpath, sortby, plot_results, start_year, end_year, debug


    def get_citations(content):
        out = 0
        for char in range(0,len(content)):
            if content[char:char+9] == 'Cited by ':
                init = char+9
                for end in range(init+1,init+6):
                    if content[end] == '<':
                        break
                out = content[init:end]
        return int(out)


    def get_year(content):
        for char in range(0,len(content)):
            if content[char] == '-':
                out = content[char-5:char-1]
        if not out.isdigit():
            out = 0
        return int(out)


    def setup_driver():
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import StaleElementReferenceException
        except Exception as e:
            print(e)
            print("Please install Selenium and chrome webdriver for manual checking of captcha")

        print('Loading...')
        chrome_options = Options()
        chrome_options.add_argument("disable-infobars")
        driver = webdriver.Chrome(chrome_options=chrome_options)
        return driver


    def get_author(content):
        for char in range(0, len(content)):
            if content[char] == '-':
                out = content[2:char-1]
                break
        return out


    def get_element(driver, xpath, attempts=5, _count=0):
        """Safe get_element method with multiple attempts"""
        try:
            element = driver.find_element_by_xpath(xpath)
            return element
        except Exception as e:
            if _count<attempts:
                sleep(1)
                get_element(driver, xpath, attempts=attempts, _count=_count+1)
            else:
                print("Element not found")


    def get_content_with_selenium(url):
        if 'driver' not in globals():
            global driver
            driver = setup_driver()
        driver.get(url)

        # Get element from page
        el = get_element(driver, "/html/body")
        c = el.get_attribute('innerHTML')

        if any(kw in el.text for kw in ROBOT_KW):
            input("Solve captcha manually and press enter here to continue...")
            el = get_element(driver, "/html/body")
            c = el.get_attribute('innerHTML')
        return c.encode('utf-8')


# name = __main__
    keyword, number_of_results, save_database, path, sortby_column, plot_results, start_year, end_year, debug =\
        get_command_line_args(kw=i_keyword, cpath=i_csv_path, plotting=i_plot, sorting=i_sort,
                              articles=i_n_results, syear=i_s_year, eyear=i_e_year)

    # Create main URL
    if start_year:
        GSCHOLAR_MAIN_URL = GSCHOLAR_URL + STARTYEAR_URL.format(start_year)
    else:
        GSCHOLAR_MAIN_URL = GSCHOLAR_URL

    if end_year != datetime.datetime.now().year:
        GSCHOLAR_MAIN_URL = GSCHOLAR_MAIN_URL + ENDYEAR_URL.format(end_year)

    if debug:
        GSCHOLAR_MAIN_URL = 'https://web.archive.org/web/20210314203256/'+GSCHOLAR_URL

    # Start new session
    session = requests.Session()
    # headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    # Variables
    links = []
    title = []
    citations = []
    year = []
    author = []
    venue = []
    publisher = []
    rank = [0]

    # Get content from number_of_results URLs
    for n in range(0, number_of_results, 10):
        # if start_year is None:
        url = GSCHOLAR_MAIN_URL.format(str(n), keyword.replace(' ','+'))
        if debug:
            print("Opening URL:", url)
        # else:
        #    url=GSCHOLAR_URL_YEAR.format(str(n), keyword.replace(' ','+'), start_year=start_year, end_year=end_year)

        print("Loading next {} results".format(n+10))
        page = session.get(url)  # , headers=headers)
        c = page.content
        if any(kw in c.decode('ISO-8859-1') for kw in ROBOT_KW):
            print("Robot checking detected, handling with selenium (if installed)")
            try:
                c = get_content_with_selenium(url)
            except Exception as e:
                print("No success. The following error was raised:")
                print(e)

        # Create parser
        soup = BeautifulSoup(c, 'html.parser', from_encoding='utf-8')

        # Get stuff
        mydivs = soup.findAll("div",{"class": "gs_or" })

        for div in mydivs:
            try:
                links.append(div.find('h3').find('a').get('href'))
            except: # catch *all* exceptions
                links.append('Look manually at: '+url)

            try:
                title.append(div.find('h3').find('a').text)
            except:
                title.append('Could not catch title')

            try:
                citations.append(get_citations(str(div.format_string)))
            except:
                warnings.warn("Number of citations not found for {}. Appending 0".format(title[-1]))
                citations.append(0)

            try:
                year.append(get_year(div.find('div', {'class': 'gs_a'}).text))
            except:
                warnings.warn("Year not found for {}, appending 0".format(title[-1]))
                year.append(0)

            try:
                author.append(get_author(div.find('div', {'class': 'gs_a'}).text))
            except:
                author.append("Author not found")

            try:
                publisher.append(div.find('div', {'class': 'gs_a'}).text.split("-")[-1])
            except:
                publisher.append("Publisher not found")

            try:
                venue.append(" ".join(div.find('div', {'class': 'gs_a'}).text.split("-")[-2].split(",")[:-1]))
            except:
                venue.append("Venue not fount")

            rank.append(rank[-1]+1)

        # Delay
        sleep(0.5)

    # Create a dataset and sort by the number of citations
    data = pd.DataFrame(list(zip(author, title, citations, year, publisher, venue, links)), index=rank[1:],
                        columns=['Author', 'Title', 'Citations', 'Year', 'Publisher', 'Venue', 'Source'])
    data.index.name = 'Rank'

    # Add columns with number of citations per year
    data['cit/year'] = data['Citations']/(end_year + 1 - data['Year'])
    data['cit/year'] = data['cit/year'].round(0).astype(int)

    # Sort by the selected columns, if exists
    try:
        data_ranked = data.sort_values(by=sortby_column, ascending=False)
    except Exception as e:
        print('Column name to be sorted not found. Sorting by the number of citations...')
        data_ranked = data.sort_values(by='Citations', ascending=False)
        print(e)

    # Plot by citation number
    rank = data_ranked.index.values.tolist()
    citations = data_ranked["Citations"].values.tolist()
    if plot_results:
        plt.plot(rank[0:3],citations[0:3],'*', c='r')
        plt.plot(rank[3:],citations[3:],'*', c='b')
        plt.ylabel('Number of Citations')
        plt.xlabel('Rank of the keyword on Google Scholar')
        plt.title('Keyword: '+keyword)
        plt.show()

    # Save results
    if save_database:
        fpath_csv = os.path.join(path, keyword.replace(' ', '_')+'.csv')
        fpath_csv = fpath_csv[:MAX_CSV_FNAME]
        data_ranked.to_csv(fpath_csv, encoding='utf-8')

#%%
for i_keyword in i_keyword_list:
    i_keyword = i_keyword.replace(' ', '_')
    csv_file = i_csv_path+i_keyword+".csv"
    df = pd.read_csv(csv_file)
    print('for keyword = '+i_keyword)
    print(df.iloc[[0, 1, 2], [7]])
    print('\n')
    print('\n')
