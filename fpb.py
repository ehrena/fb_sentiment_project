
#Do high-sentiment posts correlate to more likes?
#Day of Week

import sqlite3
import urllib.request, urllib.parse, urllib.error
import subprocess
import warnings
import requests
import json
import numpy as np
import datetime
import re
import pylab
from google.cloud import language
import facebook
import google.auth
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
import webbrowser
import matplotlib
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go
import fb_info
credentials, project = google.auth.default()
client = language.LanguageServiceClient(credentials = credentials)
#plotly_api_key = "iCXiURqN9lSc4tCqE3E2"
###########FACEBOOK##############
APP_ID     = '444901019190968'
APP_SECRET = '465b0244019fabad1becec4c13534e88'
baseurl = 'https://graph.facebook.com/me/posts'
myToken = fb_info.token
myUsername = 'iceberg630'
fullUrl = baseurl+'/'+myUsername
facebook_session = False
#################################
CACHE_FNAME = "final_project_cache.json" #Cache file for Facebook data
NLP_CACHE = "nlp_cache.json" #Cache file for Google NLP data
conn = sqlite3.connect("final.sqlite")
cur = conn.cursor()
##Caching patterns for both set up here##
try:
    cache_file = open(CACHE_FNAME,'r')
    cache_contents = cache_file.read()
    cache_file.close()
    CACHE_DICTION = json.loads(cache_contents)
except:
    CACHE_DICTION = {}

try:
    cache_file = open(NLP_CACHE,'r')
    cache_contents = cache_file.read()
    cache_file.close()
    NLP_CACHE_DICTION = json.loads(cache_contents)
except:
    NLP_CACHE_DICTION = {}



"""def makeFacebookRequest(baseURL, params = {}):
    global facebook_session
    if not facebook_session:
        authorization_base_url = 'https://www.facebook.com/dialog/oauth'
        token_url = 'https://graph.facebook.com/oauth/access_token'
        redirect_uri = 'https://www.programsinformationpeople.org/runestone/oauth'
        scope = ['user_posts','pages_messaging','user_managed_groups','user_likes']
        facebook = OAuth2Session(APP_ID, redirect_uri=redirect_uri, scope=scope)
        facebook_session = facebook_compliance_fix(facebook)
        authorization_url, state = facebook_session.authorization_url(authorization_base_url)
        print('Opening browser to {} for authorization'.format(authorization_url))
        webbrowser.open(authorization_url)
        redirect_response = input('Paste the full redirect URL here: ')
        facebook_session.fetch_token(token_url, client_secret=APP_SECRET, authorization_response=redirect_response.strip())
    return facebook_session.get(baseURL, params=params)
myRequest = makeFacebookRequest(baseurl)"""

#This is an OAuth configuration, but running it takes a while so I commented it out.
def lang_analysis(text):
    document = language.types.Document(
    content = text,
    type = 'PLAIN_TEXT')
    sentiment = client.analyze_sentiment(document = document)
    sentiment = sentiment.document_sentiment
    return sentiment.score, sentiment.magnitude

graph = facebook.GraphAPI(myToken)
user = 'me'
if user in CACHE_DICTION:
    pass
else:
    profile = graph.get_object(id= user, limit=100)
    posts = graph.get_connections(profile['id'], 'posts')
    myPosts = []
    i = 0
    while True:
        try:
            # Perform some action on each post in the collection we receive from Facebook.              
            [myPosts.append(post) for post in posts['data']]
            # Attempt to make a request to the next page of data, if it exists.
            posts = requests.get(posts['paging']['next']).json()
            i+=1
        except KeyError:
            # When there are no more pages (['paging']['next']), break from the loop and stop paginating
            break
    CACHE_DICTION[user] = myPosts
    try:
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
    except:
        print("This is not a valid search term. Please try again.")

sentDict = {}

cur.execute('DROP TABLE IF EXISTS Posts')
cur.execute('''
CREATE TABLE Posts (id INTEGER, message TEXT, created_time TIMESTAMP, sentiment_score DECIMAL, magnitude DECIMAL)''')
for post in CACHE_DICTION[user][:500]: #500 posts is close to the max that the lang_analysis function can handle at once, even once the Google NLP data is
    if "message" in post:
        if post["message"] in NLP_CACHE_DICTION:
            analysis = NLP_CACHE_DICTION[post["message"]]
            tup = (post["id"], post["message"], post["created_time"], analysis[0], analysis[1])
            cur.execute("INSERT INTO Posts (id, message, created_time, sentiment_score, magnitude) VALUES (?, ?, ?, ?, ?)", tup)
            sentDict[(post["id"], post["message"], post["created_time"])] = analysis
        else:
            analysis = lang_analysis(post["message"])
            tup = (post["id"], post["message"], post["created_time"], analysis[0], analysis[1])
            cur.execute("INSERT INTO Posts (id, message, created_time, sentiment_score, magnitude) VALUES (?, ?, ?, ?, ?)", tup)
            sentDict[(post["id"], post["message"], post["created_time"])] = analysis
            NLP_CACHE_DICTION[post["message"]] = analysis
            try:
                dumped_json_cache = json.dumps(NLP_CACHE_DICTION)
                fw = open(NLP_CACHE,"w")
                fw.write(dumped_json_cache)
                fw.close()
            except:
                print("This is not a valid search term. Please try again.")

#print((sentDict))
"""post_ids = cur.execute("SELECT id FROM Posts")
post_id_list = []
for row in post_ids:
    post_id_list.append(row[0])
post_id_list = post_id_list[:50]
posts_from_id = graph.get_objects(ids = post_id_list, fields = 'message, place, created_time, likes')"""


    

#print(posts_from_id)


dates = []
for row in cur.execute("SELECT created_time FROM Posts ORDER BY created_time"):
    f = '%Y-%m-%dT%H:%M:%S+0000'
    ts = row[0]
    dates.append(datetime.datetime.strptime(ts, f))
#print(dates)
sentiments = [row[0] for row in cur.execute("SELECT sentiment_score FROM Posts ORDER BY created_time")] #gets all the sentiments from the Posts table
magnitudes = [row[0] for row in cur.execute("SELECT magnitude FROM Posts ORDER BY created_time")] #gets all the magnitudes from the Posts table
#plt.plot(dates, sentiments)
#plt.show()
month_dict = {}
for i in range(1, 13):
    for row in cur.execute("SELECT * FROM Posts ORDER BY created_time"):
        if re.match("^[0-9]{4}-[0]?" + str(i) + "-[0-9]{2}.*", row[2]) and i not in month_dict:
            month_dict[i] = [row[3]]
        elif re.match("^[0-9]{4}-[0]?" + str(i) + "-[0-9]{2}.*", row[2]) and i in month_dict:
            month_dict[i].append(row[3])
        else:
            pass
#print(month_dict)
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
month_sentiments = {}
for i in range(1, 13):
    month_sentiments[months[i-1]] = sum(month_dict[i])/len(month_dict[i])
#print(month_sentiments)
myKeys = month_sentiments.keys()
myValues = month_sentiments.values()
month_bar = [go.Bar(
                    x = list(myKeys) ,
                    y = list(myValues)
            )]
layout = go.Layout(
    title="Andrew's average sentiment on Facebook by month (since 2014)",
)
data = month_bar
fig = go.Figure(data = data, layout = layout)
py.iplot(fig, filename='basic-bar')


conn.commit()
conn.close()

#print(get_tweets())
"""pattern = [(r'[a-zA-Z]*')]
tweets = get_tweets()
tokenized_tweets = []
for tweet in tweets:
	tokenized_tweets.append(nltk.word_tokenize(tweet))
#x = pos_tag_sents(tokenized_tweets)
#print(x
for tweet in tokenized_tweets:
	for token in tweet:
		print(token)"""
		#if re.match(token, pattern):
			#print(token)
#myTweets = nltk.pos_tag(tokenized_tweets)
#print(myTweets)


"""adjDict = {}
for tweet in myTweets:
	for tup in tweet:
		if tup[1] == "JJ" and tup[0] not in adjDict:
			adjDict[tup[0]] = 1
		elif tup[1] == "JJ" and tup[0] in adjDict:
			adjDict[tup[0]] += 1
		else:
			continue
for item in adjDict.copy().keys():
	if "@" in item or "#" in item:
		del adjDict[item]

print(sorted(adjDict.items(), key = lambda x: x[1], reverse = True))"""


