import re
import tweepy
from tweepy import OAuthHandler
from textblob import TextBlob
import pandas as pd
import yaml


class TwitterClient(object):
    def __init__(self):
        credentials_data = self.process_yaml()
        consumer_key = credentials_data["search_tweets_api"]["consumer_key"]
        consumer_secret = credentials_data["search_tweets_api"]["consumer_secret"]
        access_token = credentials_data["search_tweets_api"]["access_token"]
        access_token_secret = credentials_data["search_tweets_api"]["access_token_secret"]

        # attempt authentication
        try:
            # create OAuthHandler object
            self.auth = OAuthHandler(consumer_key, consumer_secret)
            # set access token and secret
            self.auth.set_access_token(access_token, access_token_secret)
            # create tweepy API object to fetch tweets
            self.api = tweepy.API(self.auth)
        except:
            print("Error: Authentication Failed")

    @staticmethod
    def process_yaml():
        with open("config.yaml") as file:
            return yaml.safe_load(file)

    def clean_tweet(self, tweet):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        '''
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def get_tweet_sentiment(self, tweet):
        '''
        Utility function to classify sentiment of passed tweet
        using textblob's sentiment method
        '''
        # create TextBlob object of passed tweet text
        analysis = TextBlob(self.clean_tweet(tweet))
        # set sentiment
        if analysis.sentiment.polarity > 0:
            return 'positive', analysis.sentiment.polarity
        elif analysis.sentiment.polarity == 0:
            return 'neutral', analysis.sentiment.polarity
        else:
            return 'negative', analysis.sentiment.polarity

    def get_tweets(self, query, count=10):
        '''
        Main function to fetch tweets and parse them.
        '''
        # empty list to store parsed tweets
        tweets = []

        try:
            # call twitter api to fetch tweets
            fetched_tweets = self.api.search(q=query, count=count)
            all_tweets = []
            # parsing tweets one by one
            for tweet in fetched_tweets:
                # empty dictionary to store required params of a tweet
                parsed_tweet = {}

                # saving text of tweet
                parsed_tweet['text'] = tweet.text
                # saving sentiment of tweet
                sentiment, score = self.get_tweet_sentiment(tweet.text)
                parsed_tweet['sentiment'] = sentiment
                parsed_tweet['score'] = score
                all_tweets.append(tweet.text)
                # appending parsed tweet to tweets list
                if tweet.retweet_count > 0:
                    # if tweet has retweets, ensure that it is appended only once
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
                else:
                    tweets.append(parsed_tweet)

            # return parsed tweets
            return tweets, ";".join(all_tweets)

        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))


def count_scores(q):
    api = TwitterClient()
    tweets, all_tweets = api.get_tweets(query=q, count=200)
    mentions = len(tweets)
    print("Number of mentions: {}".format(mentions))

    if mentions > 0:
        ptweets = [tweet for tweet in tweets if tweet['sentiment'] == 'positive']
        ntweets = [tweet for tweet in tweets if tweet['sentiment'] == 'negative']
        positive = round(100 * len(ptweets) / len(tweets), 2)
        negative = round(100 * len(ntweets) / len(tweets), 2)
        neutral = round(100 * (len(tweets) - (len(ntweets) + len(ptweets))) / len(tweets), 2)
        scores = [tweet['score'] for tweet in tweets]
        avg_score = sum(scores) / len(tweets)
    else:
        positive, negative, neutral, avg_score = 0,0,0,0

    return mentions, positive, negative, neutral, avg_score, all_tweets


if __name__ == "__main__":
    data = pd.read_excel(r"C:\Users\maxim\OneDrive\Desktop\folder\diplom\data\parsing\final_companies.xlsx")
    companies = list(data['Company'])
    mentions, positive, negative, neutral, avg_score, tweets = [], [], [], [], [], []

    for company in companies:
        v1, v2, v3, v4, v5, v6 = count_scores(company)
        print(v1, v2, v3, v4, v5, v6)
        mentions.append(v1)
        positive.append(v2)
        negative.append(v3)
        neutral.append(v4)
        avg_score.append(v5)
        tweets.append(v6)

    data['Mentions'] = mentions
    data['Positiveness'] = positive
    data['Negativeness'] = negative
    data['Neutralness'] = neutral
    data['Average positiveness'] = avg_score
    data['Tweets'] = tweets

    data.to_excel(r"C:\Users\maxim\OneDrive\Desktop\folder\diplom\data\parsing\final_companies_with_text.xlsx")
