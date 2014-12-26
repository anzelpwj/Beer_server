#!/usr/bin/python
# -*- coding: utf-8 -*-

# Written in python 3

from beerroutines import *
# import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
import pandas as pd


# sns.set_palette(sns.color_palette("cubehelix", 8))

conn, cur = InitFromCSV(':memory:')

## Graphing methods
def Analytics(cur,Country_thresh, Corp_thresh):
    symbolarray = ['o', 's', '+', 'D', '*', '^']
    ratingsarray, countries, country_count = CountCountryRatings(cur,Country_thresh)
    ratingsarray_corp, corporations, corps_count = CountCorpRatings(cur,Corp_thresh)
    #
    # Plot Country
    plt.figure(figsize=(16, 8))
    plt.subplot(121)
    for ind in range(0,len(country_count)):
        plt.plot(range(0,11), ratingsarray[ind,:]/country_count[ind],'o-')
    #
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating', fontsize=18)
    plt.title('Country Ratings', fontsize=20)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(countries, loc=2, fontsize=16)
    plt.subplot(122)
    #
    # Plot Corporation
    for ind in range(0,len(corps_count)):
        plt.plot(range(0,11), ratingsarray_corp[ind,:]/corps_count[ind],'o-')

    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating', fontsize=18)
    plt.title('Corp ratings', fontsize=20)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(corporations, loc=2, fontsize=16)
    plt.show()
    return 1

def BasicHistogram(cur):
    """
    A routine just to check the overall spread of ratings
    """
    ratingsarray = BasicRatings(cur)
    numberOfReviews = np.sum(ratingsarray)
    plt.figure(figsize=(8, 8))
    plt.plot(range(0,11), ratingsarray/numberOfReviews, 'o-', 
             markersize=10)
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating', fontsize=18)
    plt.title('All Ratings', fontsize=20)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.show()

def CountryHistogram(cur, threshhold):
    symbolarray = ['o', 's', '+', 'D', '*', '^']
    ratingsarray, countries, country_count = CountCountryRatings(cur,threshhold)
    # Plotting everything in the same plot is super confusing, let's try doing
    # Multiple plots
    # num_subplots = np.ceil(len(country_count) / plotsplit)
    # if num_subplots > 9:
    #     print("Increase plotsplit")
    #     return 1
    plt.figure(figsize=(8, 8))
    for ind in range(len(country_count)):
        symbol = symbolarray[ind % len(symbolarray)]
        plt.plot(range(11), ratingsarray[ind,:]/country_count[ind],
                 symbol + '-', label=countries[ind], markersize=10)
    plt.legend(loc=2, fontsize=16)
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating', fontsize=18)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.title('Country Ratings', fontsize=20)
    plt.show()
    return 1

def CorpHistogram(cur, threshhold):
    symbolarray = ['o', 's', '+', 'D', '*', '^']
    ratingsarray_corp, corporations, corps_count = CountCorpRatings(cur,threshhold)
    plt.figure(figsize=(8, 8))
    for ind in range(0,len(corps_count)):
        symbol = symbolarray[ind % len(symbolarray)]
        plt.plot(range(0,11), ratingsarray_corp[ind,:]/corps_count[ind],
            symbol + '-', label=corporations[ind], markersize=10)
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating', fontsize=18)
    plt.title('Corp Ratings', fontsize=20)
    plt.legend(loc=2, fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.show()
    return 1

def ALCHistogram(cur):
    symbolarray = ['o', 's', '+', 'D', '*']
    ratingsarray, AleLagerCider, ALC_sum = AleLagerCiderRatings(cur)
    plt.figure(figsize=(8, 8))
    for ind in range(0,len(ALC_sum)):
        if ALC_sum[ind] > 0:
            plt.plot(range(0,11), ratingsarray[ind,:]/ALC_sum[ind],
                symbolarray[ind] + '-', markersize=10)
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating', fontsize=18)
    plt.title('Ale vs. Lager Ratings', fontsize=20)
    plt.legend(AleLagerCider, loc=2, fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.show()
    return 1

# This is a bit of a hybrid method, perhaps I should seperate the two
def StyleBar(cur, styleval, stylethresh):
    ratingsarray, BeerStyles, BeerStyle_count = \
    StyleRatings(cur, styleval, stylethresh)
    # print(BeerStyles)
    # print(BeerStyle_count)
    # print(ratingsarray)
    n = len(BeerStyles)
    if n < 2:
        print("Too few things are rated, decrease stylethresh")
        return 1
    style_averages, style_std, style_min, style_max = \
    RatingsArrayIntoStats(ratingsarray)
    y_pos = 1.5*np.arange(len(BeerStyles))
    plt.figure(figsize=(18, 8))
    plt.barh(y_pos, style_averages, xerr=style_std, align='center',alpha=0.4)
    plt.yticks(y_pos,BeerStyles, fontsize=16)
    plt.xticks(fontsize=16)
    plt.xlabel('Rating', fontsize=18)
    plt.title(styleval + ' Style Ratings', fontsize=20)
    plt.show()
    # Make dataframe
    ratarr = np.vstack((style_averages, style_std, BeerStyle_count, 
                        style_min, style_max))
    beerstyle_df = pd.DataFrame(data=ratarr.T, index=BeerStyles,
                            columns=['Mean', 'StDev', 'Count', 'Min', 'Max'])
    beerstyle_df['StDev'] = beerstyle_df['StDev'].map('{:,.2f}'.format)
    beerstyle_df['Mean'] = beerstyle_df['Mean'].map('{:,.2f}'.format)
    return beerstyle_df

## Stats methods
def ALCstats(cur):
    """
    Gets Ale, Lager, and Cider stats and runs a t-test to find which
    I like better
    """
    ratingsarray, AleLagerCider, ALC_sum = AleLagerCiderRatings(cur)
    ALC_averages, ALC_std, ALC_min, ALC_max = \
    RatingsArrayIntoStats(ratingsarray)
    ALCarr = np.vstack((ALC_averages, ALC_std, ALC_sum))
    ALC_df = pd.DataFrame(data=ALCarr.T, index=AleLagerCider,
                          columns=['Mean', 'StDev', 'Count'])
    # Now, to T-test ales versus lagers
    fill_count = 0
    Ale_ratings = np.zeros((ALC_sum[0]))
    for ind in range(11):
        num_at_rating = ratingsarray[0, ind]
        Ale_ratings[fill_count:(fill_count + num_at_rating)] = ind
        fill_count = fill_count + num_at_rating
    fill_count = 0
    Lager_ratings = np.zeros((ALC_sum[1]))
    for ind in range(11):
        num_at_rating = ratingsarray[1, ind]
        Lager_ratings[fill_count:(fill_count + num_at_rating)] = ind
        fill_count = fill_count + num_at_rating
    t, prob = stats.ttest_ind(Ale_ratings,Lager_ratings, equal_var=False)
    ALC_df['Mean'] = ALC_df['Mean'].map('{:,.2f}'.format)
    ALC_df['StDev'] = ALC_df['StDev'].map('{:,.2f}'.format)
    # print(ALC_df)
    print('Two-sided p-value Ale vs Lager: {:.3e}'.format(prob))
    return ALC_df

def CountryStats(cur, Country_thresh):
    # Gives mean and std for various countries
    ratingsarray, countries, country_count = CountCountryRatings(cur, Country_thresh)
    # Unravel the ratings arrays into arrays of ratings
    n = len(countries)
    if n < 2:
        print("Too few things are rated, decrease Country_thresh")
        return 1
    country_averages, country_std, country_min, country_max = \
    RatingsArrayIntoStats(ratingsarray)
    # avg_sort_indicies = np.argsort(country_averages)
    # print(avg_sort_indicies)
    cntarr = np.vstack((country_averages, country_std, country_count))
    country_df = pd.DataFrame(data=cntarr.T, index=countries, 
                              columns=['Mean', 'StDev', 'Count'])
    country_df = country_df.sort_index(by='Mean', ascending=False)
    country_df['StDev'] = country_df['StDev'].map('{:,.2f}'.format)
    country_df['Mean'] = country_df['Mean'].map('{:,.2f}'.format)
    return country_df

def CorpStats(cur, Corp_thresh):
    # Runs two-sample t-tests on the corp results to tell if craft-brewing
    # is statistically better
    ratingsarray, corporations, corp_count = CountCorpRatings(cur,Corp_thresh)
    # Unravel the ratings arrays into arrays of ratings
    n = len(corporations)
    if len(corporations) < 2:
        print("Too few things are rated, decrease Corp_thresh")
        return 1
    corp_average, corp_std, corp_min, corp_max = \
    RatingsArrayIntoStats(ratingsarray)    
    # The last array is craft beers
    craft_ratings = np.zeros((corp_count[-1]))
    fill_count = 0
    for ind in range(0,11):
        num_at_rating = ratingsarray[n-1,ind]
        craft_ratings[fill_count:(fill_count + num_at_rating)] = ind
        fill_count = fill_count + num_at_rating
    #
    # Now to do t-tests
    p_arr = np.zeros((n))
    for corp_index in range(n-1):
        corp_ratings = np.zeros((corp_count[corp_index]))
        fill_count = 0
        for ind in range(0,11):
            num_at_rating = ratingsarray[corp_index,ind]
            corp_ratings[fill_count:(fill_count + num_at_rating)] = ind
            fill_count = fill_count + num_at_rating
        #
        t, prob = stats.ttest_ind(craft_ratings,corp_ratings, equal_var=False)
        p_arr[corp_index] = prob
    corparr = np.vstack((corp_average, corp_std, corp_count, p_arr))
    corp_df = pd.DataFrame(data=corparr.T, index=corporations, 
                    columns=['Mean', 'StDev', 'Count', 'Two-sided p'])
    corp_df['StDev'] = corp_df['StDev'].map('{:,.2f}'.format)
    corp_df['Mean'] = corp_df['Mean'].map('{:,.2f}'.format)
    corp_df['Two-sided p'] = corp_df['Two-sided p'].map('{:,.4f}'.format)
    return corp_df

def HelpMe():
    """
    Lists the routines I've got going on
    """
    helpstr = \
    """
    Analytics(cur, country_thresh, corp_thresh) for two histograms
    CountryHistogram(cur, thresh) for country histograms
    CorpHistogram(cur, thresh) for corp histogram
    StyleBar(cur, AleLagerCider, thresh) bar graph on ALC styles and stats
    CountryStats(cur, thresh) for country stats
    CorpStats(cur, thresh) for corp stats
    ALCstats(cur) to compare Ale, Lager, and Cider
    ALCHistogram(cur) to histogram ALC ratings
    BeersList(cur) for a dataframe on all the beers I've had
    EmailBeersList(cur, emailaddr) to email beerslist
    AleOrLager(cur) for a quick Ale/Lager consideration
    MissingBeerTaxonomy(cur) to make sure I have all the styles accounted for
    MissingBeerRegions(cur) to make sure I have all regions accounted for
    """
    print(helpstr)
    return 0

# CorpHistogram(cur, 5)
# StyleBar(cur, 'Lager', 2)
# ALCstats(cur)
# EmailBeersList(cur, 'anzelpwj@gmail.com')
# HelpMe()
# CountryHistogram(cur, 5)
# print(CountryStats(cur, 5))
# 
# Sometimes p-stats are disappointing
