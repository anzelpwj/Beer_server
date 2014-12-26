#!/usr/bin/python
# -*- coding: utf-8 -*-

# Written for python 3

import sqlite3 as lite
import sys
import csv
import numpy as np
import pandas as pd

from email.mime.text import MIMEText
from datetime import date
import smtplib

# Email info is a python file with the following
# SMTP_USERNAME = XXXXXX
# SMTP_PASSWORD = XXXXXX
# EMAIL_FROM = XXXXX
from email_info import *

class StdevFunc:
    """
    For use as an aggregate function in SQLite, in order to get standard
    deviations. But I generally don't use this. Code from StackOverflow,
    somewhere...
    """
    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 0

    def step(self, value):
        try:
            # automatically convert text to float, like the rest of SQLite
            val = float(value)
            # if fails, skips this iteration, which also ignores nulls
            tM = self.M
            self.k += 1
            self.M += ((val - tM) / self.k)
            self.S += ((val - tM) * (val - self.M))
        except:
            pass

    def finalize(self):
        if self.k <= 1: # avoid division by zero
            return 0
        else:
            return np.sqrt(self.S / (self.k-1))

def Quicktest():
    """
    Just to see if things are working properly
    """
    print("Staring into madness...")
    return 1

def RatingsArrayIntoStats(ratingsarray):
    """
    A lot of routines return a ratings array. This is a routine to get some
    descriptive stats on the ratings array. Call:
    r_averages, r_stdev, r_min, r_max = RatingsArrayIntoStats(ratingsarray)
    """
    m, n = ratingsarray.shape
    r_averages = np.zeros((m))
    r_stdev = np.zeros((m))
    r_min = np.zeros((m))
    r_max = np.zeros((m))
    #
    for r_ind in range(m):
        fill_count = 0
        array_count = sum(ratingsarray[r_ind,:])
        if array_count > 0:
            ratingsarr = np.zeros((array_count))
            for ind in range(11):
                num_at_rating = ratingsarray[r_ind, ind]
                ratingsarr[fill_count:(fill_count + num_at_rating)] = ind
                fill_count = fill_count + num_at_rating
            r_averages[r_ind] = np.mean(ratingsarr)
            r_stdev[r_ind] = np.std(ratingsarr)
            r_min[r_ind] = min(ratingsarr)
            r_max[r_ind] = max(ratingsarr)
        else:
            r_averages[r_ind] = 0
            r_stdev[r_ind] = 0
            r_min[r_ind] = 0
            r_max[r_ind] = 0
    return r_averages, r_stdev, r_min, r_max

## Advanced ratings
def CountCountryRatings(cur, numberthreshhold):
    """
    Counts how many are rated for each country from 0 to 10
    Numthreshhold restricts our count so that we only get data if we have
    a sufficient number of ratings from the country. Call:
    ratingsarray, countries, count = CountCountryRatings(cur, numthreshhold)
    """
    SQLstr_counting = \
    """SELECT Country, count(*) FROM
    beers, regions
    ON beers.Origin = regions.Region
    WHERE ifnull(beers.Rating,'') <> ''
    GROUP BY Country;
    """
    cur.execute(SQLstr_counting)
    SQLout = cur.fetchall()
    # print(SQLout)
    countries = []
    country_count = []
    for row in SQLout:
    	if row[1] >= numberthreshhold:
    		countries.append(str(row[0]))
    		country_count.append(row[1])
    numcount = len(country_count)
    #
    ratingsarray = np.zeros((numcount,11)) # Countries, ratings
    for ratingind in range(0,11):
        SQLstr_ratings = \
        """SELECT Country, count(Rating) FROM
        beers, regions
        ON beers.Origin = regions.Region
        WHERE beers.Rating = """ + str(ratingind) + """
        GROUP BY Country;
        """
        cur.execute(SQLstr_ratings)
        SQLout = cur.fetchall()
        #print(SQLout)
        #print(ratingind)
        for SQLrow in SQLout:
        	# For-loop kludge, a smarter person could vectorize this
            # print(str(SQLrow[0]), SQLrow[1])
            for Cind in range(0,numcount):
                if countries[Cind] == str(SQLrow[0]):
                    ratingsarray[Cind, ratingind] = SQLrow[1]
    # I want np arrays
    countries = np.array(countries)
    country_count = np.array(country_count)
    return ratingsarray, countries, country_count

def CountCorpRatings(cur, numberthreshhold):
    """
    Counts how many are rated for each corporation from 0 to 10
    Numthreshhold restricts our count so that we only get data if we have
    a sufficient number of ratings from each corp. Final element of array
    is independent/craft breweries, which is an ongoing process of
    classification. Call:
    ratingsarray, corps, count = CountCorpRatings(cur, numthreshhold)
    """
    SQLstr_counting = \
    """SELECT Corporation, count(*) FROM
    beers, brands
    ON beers.Brewery = brands.Brewery
    WHERE ifnull(beers.Rating,'') <> ''
    GROUP BY Corporation;
    """
    SQLstr_count_indeps = \
    """SELECT count(*) FROM beers
    WHERE Brewery IN
    (SELECT Brewery FROM beers EXCEPT SELECT Brewery FROM brands);
    """
    cur.execute(SQLstr_counting)
    SQLout = cur.fetchall()
    # print(SQLout)
    corporations= []
    corporation_count = []
    for row in SQLout:
    	if row[1] >= numberthreshhold:
    		corporations.append(str(row[0]))
    		corporation_count.append(row[1])
    cur.execute(SQLstr_count_indeps)
    corporations.append('Craft/Independent')
    indepnum = cur.fetchall()
    corporation_count.append(indepnum[0][0])
    numcount = len(corporation_count)
    #
    ratingsarray = np.zeros((numcount,11), dtype=float) # Corps, ratings
    for ratingind in range(0,11):
        SQLstr_ratings = \
        """SELECT Corporation, count(Rating) FROM
        beers, brands
        ON beers.Brewery = brands.Brewery
        WHERE beers.Rating = """ + str(ratingind) + """
        GROUP BY Corporation;
        """
        cur.execute(SQLstr_ratings)
        SQLout = cur.fetchall()
        #print(SQLout)
        #print(ratingind)
        for SQLrow in SQLout:
        	# For-loop kludge, a smarter person could vectorize this
            # print(str(SQLrow[0]), SQLrow[1])
            for Cind in range(0,numcount-1):
                if corporations[Cind] == str(SQLrow[0]):
                    ratingsarray[Cind, ratingind] = SQLrow[1]
    for ratingind in range(0,11): # Now we get the indeps
        SQLstr_ratings_indep = \
        """SELECT count(Rating) FROM beers
        WHERE Brewery IN
        (SELECT Brewery FROM Beers EXCEPT SELECT Brewery FROM Brands)
        AND Rating = """ + str(ratingind) + ';'
        #print(SQLstr_ratings_indep)
        cur.execute(SQLstr_ratings_indep)
        ratingvalueindep = cur.fetchall()
        #print(ratingvalueindep[0][0])
        ratingsarray[numcount-1, ratingind] = ratingvalueindep[0][0]
    # I want np arrays
    corporations = np.array(corporations)
    corporation_count = np.array(corporation_count)
    return ratingsarray, corporations, corporation_count

def StyleRatings(cur, AleLagerCider, stylethresh):
    """
    Counts how many are rated for each style from 0 to 10
    stylethresh restricts our count so that we only get data if we have
    a sufficient number of ratings from each style. AleLagerCider can be
    a string of 'Ale', 'Lager', or 'Cider' to distinguish, otheriwise
    combines all three types. Call:
    ratingsarray, BeerStyles, BeerStyle_count = 
        StyleRatings(cur, AleLagerCider, stylethresh)
    """
    SQLstrAle = \
    """SELECT beers.Type, count(Rating)
    FROM beers JOIN taxonomy
    ON beers.Type=taxonomy.Type
    WHERE ifnull(beers.Rating,'') <> ''
    AND taxonomy.AleOrLager = 'Ale'
    GROUP BY beers.Type
    ORDER BY avg(Rating) DESC;
    """
    SQLstrLager = \
    """SELECT beers.Type, count(Rating)
    FROM beers JOIN taxonomy
    ON beers.Type=taxonomy.Type
    WHERE ifnull(beers.Rating,'') <> ''
    AND taxonomy.AleOrLager = 'Lager'
    GROUP BY beers.Type
    ORDER BY avg(Rating) DESC;
    """
    SQLstrCider =\
    """SELECT beers.Type, count(Rating)
    FROM beers JOIN taxonomy
    ON beers.Type=taxonomy.Type
    WHERE ifnull(beers.Rating,'') <> ''
    AND taxonomy.AleOrLager = 'Cider'
    GROUP BY beers.Type
    ORDER BY avg(Rating) DESC;
    """
    SQLstrAll =\
    """SELECT beers.Type, count(Rating)
    FROM beers JOIN taxonomy
    ON beers.Type=taxonomy.Type
    WHERE ifnull(beers.Rating,'') <> ''
    AND taxonomy.AleOrLager = 'Cider'
    GROUP BY beers.Type
    ORDER BY avg(Rating) DESC;
    """
    if AleLagerCider == 'Ale':
        cur.execute(SQLstrAle)
    elif AleLagerCider == 'Lager':
        cur.execute(SQLstrLager)
    elif AleLagerCider == 'Cider':
        cur.execute(SQLstrCider)
    else:
        cur.execute(SQLstrAll)
    SQLout = cur.fetchall()
    BeerStyl = []
    BeerStylCount = []
    for row in SQLout:
        if row[1] >= stylethresh:
            BeerStyl.append(str(row[0]))
            BeerStylCount.append(row[1])
    numcount = len(BeerStyl)
    ratingsarray = np.zeros((numcount,11)) # Countries, ratings
    for ratingind in range(0,11):
        SQLstr_ratings = \
        """SELECT beers.Type, count(Rating) FROM
        beers JOIN taxonomy
        ON beers.Type=taxonomy.Type
        WHERE beers.Rating = """ + str(ratingind) + """
        GROUP BY beers.Type;
        """
        cur.execute(SQLstr_ratings)
        SQLout = cur.fetchall()
        #print(SQLout)
        #print(ratingind)
        for SQLrow in SQLout:
            # Beyond this lies drunken madness, third pints, kebabs,
            # and destruction 
            for Cind in range(numcount):
                if BeerStyl[Cind] == str(SQLrow[0]):
                    ratingsarray[Cind, ratingind] = SQLrow[1]
        # I want np arrays
    BeerStyles = np.array(BeerStyl)
    BeerStyle_count = np.array(BeerStylCount)
    return ratingsarray, BeerStyles, BeerStyle_count

def AleLagerCiderRatings(cur):
    """
    Returns a ratings array for the three types for histogramming, etc.
    Call:
    ratingsarray, AleLagerCider = 
        AleLagerCiderRatings(cur)
    """
    AleLagerCiderTemp = np.array(["'Ale'", "'Lager'", "'Cider'"])
    AleLagerCider = np.array(["Ale", "Lager", "Cider"])
    ratingsarray = np.zeros((3,11))
    for ALCind in range(3):
        for ratingind in range(0,11):
            SQLstr = """SELECT count(*) FROM
            beers JOIN taxonomy
            ON beers.Type=taxonomy.Type
            WHERE taxonomy.AleOrLager = """ + AleLagerCiderTemp[ALCind] + """
            AND ifnull(beers.Rating,'') <> ''
            AND beers.Rating = """ + str(ratingind) + ';'
            cur.execute(SQLstr)
            Temprating = cur.fetchall()
            ratingsarray[ALCind, ratingind] = Temprating[0][0]
    ALCsum = np.sum(ratingsarray, axis=1)
    return ratingsarray, AleLagerCider, ALCsum

## Basic stats
def BasicRatings(cur):
    """
    Returns a ratings array for all beers, in order to check for normal-shape
    """
    ratingsarray = np.zeros((11))
    for ratingind in range(0,11):
        SQLstr = """SELECT count(*) FROM beers
        WHERE ifnull(beers.Rating,'') <> ''
        AND beers.Rating = """ + str(ratingind) + ';'
        cur.execute(SQLstr)
        Temprating = cur.fetchall()
        ratingsarray[ratingind] = Temprating[0][0]
    return ratingsarray

def CountriesRepresented(cur):
    """
    Lists the countries that I've tried beers from. Does not process strings
    yet. Call:
    SQLoutput = CountriesRepresented(cur)
    """
    SQLstr = \
    """SELECT DISTINCT regions.Country FROM
    beers JOIN regions
    ON beers.Origin=regions.Region
    WHERE ifnull(beers.Rating,'') <> '';
    """
    cur.execute(SQLstr)
    return cur.fetchall()

def BestBeers(cur, RatingThresh):
    """
    Lists which beers are rated >= RatingThresh. Doesn't process strings yet.
    Call:
    SQLoutput = BestBeers(cur, RatingThresh)
    """
    SQLstr = \
    """SELECT BeerName AS Beer, Brewery FROM beers
    WHERE Rating >= " + str(RatingThresh) + "
    ORDER BY Rating DESC;"""
    cur.execute(SQLstr)
    return cur.fetchall()

def BestFromCountry(cur, num_get, Country):
    """
    Gives the top num_get beers from a country
    UNTESTED
    """
    assert num_get >= 1
    SQLstr = 'SELECT TOP ' + str(round(num_get)) + """ PERCENT BeerName, Brewery, Rating FROM
    beers JOIN regions
    ON beers.Origin=regions.Region
    WHERE ifnull(beers.Rating,'') <> ''
    AND Country = '""" + Country + """'
    ORDER BY Rating DESC;"""
    cur.execute(SQLstr)
    values = cur.fetchall()
    Beers = np.zeros(num_get)
    Breweries = np.zeros(num_get)
    Ratings = np.zeros(num_get)
    for ind in range(num_get):
        print(ind)
        # FIX THIS
        Beers[ind] = values[ind][0]
        Breweries[ind] = values[ind][1]
        Ratings[ind] = values[ind][2]
    return Beers, Breweries, Ratings

def AleOrLager(cur):
    """
    A quick routine to see whether I like Ale or Lager better. Should be
    replaced by AleLagerCiderRatings
    """
    SQLstrAle = """SELECT avg(beers.Rating) FROM
    beers JOIN taxonomy
    ON beers.Type=taxonomy.Type
    WHERE taxonomy.AleOrLager = 'Ale'
    AND ifnull(beers.Rating,'') <> '';"""
    SQLstrLager = """SELECT avg(beers.Rating) FROM
    beers JOIN taxonomy
    ON beers.Type=taxonomy.Type
    WHERE taxonomy.AleOrLager = 'Lager'
    AND ifnull(beers.Rating,'') <> '';"""
    cur.execute(SQLstrAle)
    Ale_rating = cur.fetchall()
    #SQLite is returning tuples, so I use X, = ... to untuple the single tuple.
    Ale_rating, = Ale_rating[0]
    cur.execute(SQLstrLager)
    Lager_rating = cur.fetchall()
    Lager_rating, = Lager_rating[0]
    print("Ale rating: {0:.2f}".format(Ale_rating))
    print("Lager rating: {0:.2f}".format(Lager_rating))
    if Ale_rating > Lager_rating:
        print("Ale wins")
        return Ale_rating, Lager_rating
    elif Ale_rating < Lager_rating:
        print("Lager wins")
        return Ale_rating, Lager_rating
    else:	
        print("The two are equal")
        return Ale_rating, Lager_rating

def BeersList(cur):
    """
    Lists the beers we already have
    """
    SQLstr = \
    """SELECT BeerName, Brewery, Country
    FROM beers JOIN regions
    ON beers.Origin=regions.Region
    ORDER BY Country, Brewery;"""
    cur.execute(SQLstr)
    beerlist = cur.fetchall()
    beerarr = []
    breweryarr = []
    originarr = []
    for linebeer in beerlist:
        beer, brewery, origin = linebeer
        beerarr.append(beer)
        breweryarr.append(brewery)
        originarr.append(origin)
    beerarr = np.array(beerarr)
    breweryarr = np.array(breweryarr)
    originarr = np.array(originarr)
    interarr = np.vstack((beerarr, breweryarr, originarr))
    beer_df = pd.DataFrame(data=interarr.T, columns=['Beer', 'Brewery', 'Origin'])
    return beer_df

## Check that things run properly
def MissingBeerTaxonomy(cur):
    # Looks for any beer styles missing in the taxonomy
    SQLstr = \
    """SELECT Type FROM beers
    EXCEPT SELECT Type FROM taxonomy;"""
    cur.execute(SQLstr)
    output = cur.fetchall()
    return output

def MissingBeerRegions(cur):
    """
    Looks for any countries missing from the region list
    """
    SQLstr = \
    """SELECT Origin FROM beers
    EXCEPT SELECT Region FROM regions;"""
    cur.execute(SQLstr)
    output = cur.fetchall()
    return output

## Export data
def EmailBeersList(cur, addresstosend):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    # execfile('email_info.txt')
    # emailfile = open('email_info.txt', 'r')
    # for line in emailfile:
    #     exec(line, global=True)
    # emailfile.close()
    #
    EMAIL_TO = addresstosend
    EMAIL_SUBJECT = "Beer list"
    #
    DATE_FORMAT = "%d/%m/%Y"
    EMAIL_SPACE = ", "
    #
    Beerdf = BeersList(cur)
    DATA = Beerdf.to_string(justify='right')
    def send_email():
        msg = MIMEText(DATA)
        msg['Subject'] = EMAIL_SUBJECT + " %s" % (date.today().strftime(DATE_FORMAT))
        msg['To'] = EMAIL_TO 
        # EMAIL_SPACE.join(EMAIL_TO) # the join tends to send to a, n, z, ...
        msg['From'] = EMAIL_FROM
        mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        mail.starttls()
        mail.login(SMTP_USERNAME, SMTP_PASSWORD)
        mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        mail.quit()
    send_email()
    
    return 1

## Routines to handle DB
def InitFromCSV(filename):
    """
    Initializes everything from CSVs. Set filename to be ':memory:' if you
    just want to run everything in memory
    conn, cur = InitFromCSV(filename)
    """
    beertablestart = '''CREATE TABLE beers
    (
        RatingID INTEGER PRIMARY KEY,
        BeerName TEXT NOT NULL,
        Brewery TEXT NOT NULL,
        Type TEXT,
        Origin TEXT,
        ABV REAL,
        HowIDrank TEXT,
        TempIDrank TEXT,
        Taste TEXT,
        Aftertaste TEXT,
        MouthFeel TEXT,
        Rating INTEGER,
        Notes TEXT,
        KeepReport INTEGER DEFAULT 1,
        CheckManually INTEGER DEFAULT 0,
        WhyCheckManually TEXT,
        Date TEXT
    );
    '''
    
    regiontablestart = '''CREATE TABLE regions
    (
        Region TEXT NOT NULL,
        Country TEXT NOT NULL,
        Continent TEXT NOT NULL
    );
    '''
    
    taxonomytablestart = '''CREATE TABLE taxonomy
    (
        Type TEXT NOT NULL,
        BeerClass TEXT,
        AleOrLager TEXT
    );
    '''

    brandstablestart = '''CREATE TABLE brands
    (
        BrandID INTEGER PRIMARY KEY,
        Brewery TEXT,
        Corporation TEXT
    );
    '''
    beer_csv = csv.reader(open('Beers.csv'), delimiter=';', quotechar='"')
    regions_csv = csv.reader(open('Regions.csv'), delimiter=';', quotechar='"')
    taxonomy_csv = csv.reader(open('Beer_taxonomy.csv'), delimiter=';', quotechar='"')
    brand_csv = csv.reader(open('Brands.csv'), delimiter=';', quotechar='"')
    	
    conn = lite.connect(filename)
    
    with conn:
        
        cur = conn.cursor()
        conn.create_aggregate("stdev", 1, StdevFunc)
        cur.execute(beertablestart)
        cur.execute(regiontablestart)
        cur.execute(taxonomytablestart)
        cur.execute(brandstablestart)
        next(beer_csv) # This skips past the header info
        next(regions_csv)
        next(taxonomy_csv)
        next(brand_csv)
    
    with conn: # Strangely, I have to split up the with because dumb
        cur.executemany('INSERT INTO beers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', beer_csv)
        cur.executemany('INSERT INTO regions VALUES (?, ?, ?)', regions_csv)
        cur.executemany('INSERT INTO taxonomy VALUES (?, ?, ?)', taxonomy_csv)
        for row in brand_csv:
            cur.execute('INSERT INTO brands (Brewery, Corporation) VALUES (?, ?)', (row[1], row[2]))
    return conn, cur

def ExportCSV(cur):
    print("Here I will put the files into a CSV")
    return 1

def LoadDB(filename):
    """
    Loads from a premade database file
    conn, cur = LoadDB(filename)
    """
    if filename == ':memory':
        print("This routine is designed for premade files")
        print("Setting filename to default Beers.db")
        filename = 'Beers.db'
    conn = lite.connect(filename)
    cur = conn.cursor()
    conn.create_aggregate("stdev", 1, StdevFunc)
    print("I still need to have some routines to check that the database is properly set up")
    return conn, cur

# def ExportDB(cur,conn,filename):
# 	data = '\n'.join(con.iterdump())
# 	f = open(filename,'w')
# 	with f
# 		f.write(data)
# 	print("Still working on this one")
# 	return 1

