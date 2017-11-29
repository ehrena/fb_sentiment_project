import sqlite3
import requests
import json
import re
from google.cloud import language
import facebook
import google.auth
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
import webbrowser
import matplotlib
import matplotlib.pyplot as plt
credentials, project = google.auth.default()
client = language.LanguageServiceClient(credentials = credentials)

###########FACEBOOK##############
APP_ID     = '444901019190968'
APP_SECRET = '465b0244019fabad1becec4c13534e88'
baseurl = 'https://graph.facebook.com/me/posts'
myToken = 'EAACEdEose0cBAOJID5ULZBGThTGN8EcZCs9RPbDiNZBSyOoGupBreceKcNq6qx8IhKUpIdPG4LVJ5onivjvZBZAD9MbGot43lYXDWsIAO4s5O1FEkItt4TfuYD2k4pBcQvAZCsZC3DQfMpIeagCGQ5qKZCMmaNZChHOco0VOeWJ4j3LW0CKjN17WfxnMNPjFGj2kZD'
myUsername = 'iceberg630'
fullUrl = baseurl+'/'+myUsername
facebook_session = False
#################################
CACHE_FNAME = "final_project_cache.json" #Cache file for Facebook data
NLP_CACHE = "nlp_cache.json" #Cache file for Google NLP data

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

def makeFacebookRequest(baseURL, params = {}):
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
myRequest = makeFacebookRequest(baseurl)

def fbRequest(access_token, user):
    if user in CACHE_DICTION:
        return CACHE_DICTION[user]
    else:
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object(id= user, fields=['id', 'created time', 'message'], limit=100)
        posts = graph.get_connections(profile['id'], 'posts')
        myPosts = []
        i = 0
        while True and i<1000:
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
            return CACHE_DICTION[user]
        except:
            print("This is not a valid search term. Please try again.")
            return None
        return myPosts

posts = fbRequest(myToken, 'me')
print(len(posts))

def lang_analysis(text):
    document = language.types.Document(
    content = text,
    type = 'PLAIN_TEXT')
    sentiment = client.analyze_sentiment(document = document)
    sentiment = sentiment.document_sentiment
    return sentiment.score, sentiment.magnitude

sentDict = {}
conn = sqlite3.connect("final.sqlite")
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS Posts')
cur.execute('''
CREATE TABLE Posts (id INTEGER, message TEXT, created_time TIMESTAMP, sentiment_score DECIMAL, magnitude DECIMAL)''')
#print(facebook_posts)
for post in posts[:500]: 
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
dates = [row[0] for row in cur.execute("SELECT created_time FROM Posts ORDER BY created_time")] #gets all the timestamps from the Posts table
sentiments = [row[0] for row in cur.execute("SELECT sentiment_score FROM Posts ORDER BY created_time")] #gets all the sentiments from the Posts table
magnitudes = [row[0] for row in cur.execute("SELECT magnitude FROM Posts ORDER BY created_time")] #gets all the magnitudes from the Posts table
#matplotlib.pyplot.plot_date(dates, sentiments)
#plt.show()

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


