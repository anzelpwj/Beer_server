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
    plt.xlabel('Rating value', fontsize=18)
    plt.title('Country Ratings', fontsize=20)
    plt.legend(countries, loc=2, fontsize=16)
    plt.subplot(122)
    #
    # Plot Corporation
    for ind in range(0,len(corps_count)):
        plt.plot(range(0,11), ratingsarray_corp[ind,:]/corps_count[ind],'o-')

    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating value', fontsize=18)
    plt.title('Corp ratings', fontsize=20)
    plt.legend(corporations, loc=2, fontsize=16)
    plt.show()
    return 1

def CountryHistogram(cur, threshhold):
    ratingsarray, countries, country_count = CountCountryRatings(cur,threshhold)
    #
    for ind in range(0,len(country_count)):
        plt.plot(range(0,11), ratingsarray[ind,:]/country_count[ind],'o-')
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating value', fontsize=18)
    plt.title('Country Ratings', fontsize=20)
    plt.legend(countries, loc=2, fontsize=16)
    plt.show()
    return 1

def CorpHistogram(cur, threshhold):
    ratingsarray_corp, corporations, corps_count = CountCorpRatings(cur,threshhold)
    #
    for ind in range(0,len(corps_count)):
        plt.plot(range(0,11), ratingsarray_corp[ind,:]/corps_count[ind],'o-')
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating value', fontsize=18)
    plt.title('Corp Ratings', fontsize=20)
    plt.legend(corporations, loc=2, fontsize=16)
    plt.show()
    return 1

def ALCHistogram(cur):
    ratingsarray, AleLagerCider, ALC_sum = AleLagerCiderRatings(cur)
    for ind in range(0,len(ALC_sum)):
        if ALC_sum[ind] > 0:
            plt.plot(range(0,11), ratingsarray[ind,:]/ALC_sum[ind],'o-')
        else:
            plt.plot(range(0,11), np.zeros(11), 'o-')
    plt.ylabel('Normalized quantity', fontsize=18)
    plt.xlabel('Rating value', fontsize=18)
    plt.title('Ale/Lager/Cider Ratings', fontsize=20)
    plt.legend(AleLagerCider, loc=2, fontsize=16)
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
    style_averages = np.zeros((n))
    style_std = np.zeros((n))
    style_min = np.zeros((n))
    style_max = np.zeros((n))
    for style_ind in range(n):
        # Make the temp list of ratings
        fill_count = 0
        ratingsarr = np.zeros((BeerStyle_count[style_ind]))
        for ind in range(11):
            num_at_rating = ratingsarray[style_ind, ind]
            ratingsarr[fill_count:(fill_count + num_at_rating)] = ind
            fill_count = fill_count + num_at_rating
        style_averages[style_ind] = np.mean(ratingsarr)
        style_std[style_ind] = np.std(ratingsarr)
        style_min[style_ind] = min(ratingsarr)
        style_max[style_ind] = max(ratingsarr)
    y_pos = 1.5*np.arange(len(BeerStyles))
    plt.barh(y_pos, style_averages, xerr=style_std,align='center',alpha=0.4)
    plt.yticks(y_pos,BeerStyles, fontsize=16)
    plt.xlabel('Rating', fontsize=18)
    plt.title('Beer Style Ratings', fontsize=20)
    plt.show()
    # Make dataframe
    ratarr = np.vstack((style_averages, style_std, BeerStyle_count, 
                        style_min, style_max))
    beerstyle_df = pd.DataFrame(data=ratarr.T, index=BeerStyles,
                            columns=['Mean', 'StDev', 'Count', 'Min', 'Max'])
    # print(beerstyle_df.to_string(float_format='{:,.2f}'.format))
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
    print(ALC_df)
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
    # country_df[1] = country_df[1].map('${:,.2f}'.format)
    # print(country_df.to_string(float_format='{:,.2f}'.format))
    return country_df

def IsCraftBetter(cur, Corp_thresh):
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
                    columns=['Mean', 'StDev', 'Count', 'Two sided p_val'])
    # print(corp_df.to_string(float_format='{:,.4f}'.format))
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
    IsCraftBetter(cur, thresh) for corp stats
    BeersList(cur) for a dataframe on all the beers I've had
    EmailBeersList(cur, emailaddr) to email beerslist
    AleOrLager(cur) for a quick Ale/Lager consideration
    MissingBeerTaxonomy(cur) to make sure I have all the styles accounted for
    MissingBeerRegions(cur) to make sure I have all regions accounted for
    """
    print(helpstr)
    return 0

EmailBeersList(cur, 'anzelpwj@gmail.com')
# HelpMe()
# ALCHistogram(cur)
# print(CountryStats(cur, 5))
# http://www.nature.com/news/scientific-method-statistical-errors-1.14700
# Sometimes p-stats are disappointing