Beer_server
===========

This is my own attempt to make a personal beer database program. These are designed to work with Python3

Missing from the repository are the actual beer reviews (for my own commentary purposes) and the email_info.py file (because it has my personal e-mail info). But to make your own version, email info is a python file with

SMTP_USERNAME = "XXX"
SMTP_PASSWORD = "YYY"
EMAIL_FROM = "ZZZ"

Meanwhile, Beers.csv is a csv file (with semi-colon seperators) adhering to the following schema
  RatingID INTEGER PRIMARY KEY, -- Just an incrementing number
  BeerName TEXT NOT NULL,
  Brewery TEXT NOT NULL,
  Type TEXT, -- Referenced with Beer_taxonomy.csv
  Origin TEXT, -- Referenced with Regions.csv
  ABV REAL, -- In percentage
  HowIDrank TEXT, -- Things like "bottle at desk"
  TempIDrank TEXT,
  Taste TEXT,
  Aftertaste TEXT,
  MouthFeel TEXT, -- I use position in mouth
  Rating INTEGER, -- In range 0 to 10
  Notes TEXT, -- Haven't really done much with this yet
  KeepReport INTEGER DEFAULT 1, -- Haven't done anything with this yet
  CheckManually INTEGER DEFAULT 0, -- Haven't done anything with this yet, but soon
  WhyCheckManually TEXT, -- See above
  Date TEXT

Todo:
- I've completely ignored any sort of error handling, so that somebody else can start to use this.
- A lot of systems don't do well if you have zero entries (say you've archived a lot of beer info but haven't added any ratings yet).
- I'd like to add some analytics for:
  - A 5-day running mean of my ratings (to see if my reviews have drifted over time)
  - Classifying the companies as Multinational (e.g. AB/InBev) or National (e.g. Boston Beer Co).
    - I'm still trying to figure this classification out myself.
  - Start running some analytics for how well I rate beers that I drink out of a can versus a bottle.
     - And when I get a lot of data there, I might even be able to start adjusting results.
- More intelligent use of CheckManually
- Dynamic updating
- Actually work with databases instead of just loading from csv to memory
- Learn a lot more about the "national"-level companies.
