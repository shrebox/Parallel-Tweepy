import configparser
import tweepy
import os
import json
from task_manager import TaskManager
import datetime
import pickle
import itertools

def get_twohop_followers(user_ids, task_manager, apis):
    """
    Fetches the two-hop follower network of the given users.
    Two-hop follower network referes to the entire network of the
    followers of a user as well as the followers of those followers.
    """
    task_manager.get_followers(user_ids)
    task_manager.run_tasks(apis)

    all_followers = set()
    for followers_file in os.listdir(task_manager.follower_folder_path):
        if '.json' not in followers_file:
            continue
        all_followers.update(
            task_manager.get_all_followers(followers_file[:-5]))

    task_manager.get_followers(user_ids)
    task_manager.run_tasks(apis)


def get_authors(tweet_objects):
    """
    Takes in the list of tweet_objects and returns the list of authors
    of the tweets.
    """
    user_ids = []
    for tweet in tweet_objects:
        user_ids.append(tweet['user']['id_str'])
    return user_ids


def process_users(user_ids, user_ignore_list, task_manager, apis):
    """
    Processes the list of users and fetches the following data related
    to them:
        - Followers and followees of the users
        - Timelines of the users
    """

    # This can be used to fetch the two-hop follower network of a user
    # get_twohop_followers(user_ids, task_manager, apis)

    filtered_user_ids = [user_id for user_id in user_ids
                         if user_id not in user_ignore_list]

    # task_manager.get_followers(filtered_user_ids)
    # task_manager.run_tasks(apis)

    # task_manager.get_followees(filtered_user_ids)
    # task_manager.run_tasks(apis)

    task_manager.get_timelines(filtered_user_ids)
    task_manager.run_tasks(apis)

def user_relations(user_ids, user_ignore_list, task_manager, apis):
    """
    Processes the list of users (retweeters) and fetches the following data related
    to them:
        - Timelines of the users (retweeters)
    """

    # This can be used to fetch the two-hop follower network of a user
    # get_twohop_followers(user_ids, task_manager, apis)

    # filtered_user_ids = [user_id for user_id in user_ids
    #                      if user_id not in user_ignore_list]
    fuid = user_ids
    task_manager.get_user_relation(fuid)
    task_manager.run_tasks(apis)

def retweeter_timeline(user_ids, user_ignore_list, task_manager, apis,source_id):
    """
    Processes the list of users (retweeters) and fetches the following data related
    to them:
        - Timelines of the users (retweeters)
    """

    # This can be used to fetch the two-hop follower network of a user
    # get_twohop_followers(user_ids, task_manager, apis)

    # filtered_user_ids = [user_id for user_id in user_ids
    #                      if user_id not in user_ignore_list]
    fuid = user_ids
    task_manager.get_rt_timelines(fuid,source_id)
    task_manager.run_tasks(apis)

def process_tweets(tweet_ids, user_ignore_list, task_manager, apis):
    """
    Processes the list of tweets and fetches the following data related
    to them:
        - Tweet objects
        - Last 100 (max) retweets
        - Followers and followees of the authors of the tweets
        - Timelines of the authors of the tweets
    """
    task_manager.get_tweet_details(tweet_ids)
    task_manager.run_tasks(apis)

    tweet_objects = []
    tweet_details = []
    for tweet_details_file in os.listdir(
            task_manager.tweet_details_folder_path):
        if '.json' not in tweet_details_file:
            continue
        with open(task_manager.tweet_details_folder_path +
                  tweet_details_file) as f:
            obj = json.load(f)
            tweet_objects.append(obj)
            tweet_details.append((tweet_details_file[:-5],
                                 obj['user']['id_str']))

    filtered_user_ids = []
    filtered_tweet_ids = []

    for tweet_id, user_id in tweet_details:
        if user_id not in user_ignore_list:
            filtered_user_ids.append(user_id)
            filtered_tweet_ids.append(tweet_id)

    task_manager.get_retweets(filtered_tweet_ids)
    task_manager.run_tasks(apis)

    process_users(filtered_user_ids, user_ignore_list, task_manager, apis)
    task_manager.run_tasks(apis)

    # iterate through the collected retweets and get the retweeters id

    rt_objects = []
    rt_source_ids = []
    for rt_details_file in os.listdir(task_manager.retweets_folder_path):
        if '.json' not in rt_details_file:
            continue
        with open(task_manager.retweets_folder_path + rt_details_file) as f:
            obj = json.load(f)
            rt_objects.append(obj)
            rt_source_ids.append(rt_details_file[:-5])
            # rt_details.append((rt_details_file[:-5],
            #                      obj['user']['id_str']))
    # run the retweeter_timeline() on the collected retweeter ids

    for rt_loop in range(len(rt_objects)):
        abc = rt_objects[rt_loop]
        rt_id_temp_list = []
        for ij in range(len(abc)):
            temp_obj = abc[ij]
            temp_obj = json.loads(temp_obj)
            rt_id_temp_list.append(temp_obj['user']['id'])
        retweeter_timeline(rt_id_temp_list,user_ignore_list, task_manager, apis,rt_source_ids[rt_loop])

def create_api_objects():
    """
    Creates the api objects from the config file.
    """
    settings_file = "apikeys/apikeys.txt"
    # Read config settings
    config = configparser.ConfigParser()
    config.readfp(open(settings_file))

    # Create API objects for each of the API keys
    # 1-based indexing of config file
    start_idx = 1
    end_idx = 21
    num_api_keys = end_idx - start_idx + 1

    apis = []

    print("Creating api objects for {} API keys".format(num_api_keys))
    for api_idx in range(start_idx, end_idx + 1):
        consumer_key = config.get('API Keys ' + str(api_idx), 'API_KEY')
        consumer_secret = config.get('API Keys ' + str(api_idx), 'API_SECRET')
        access_token_key = config.get('API Keys ' + str(api_idx),
                                      'ACCESS_TOKEN')
        access_token_secret = config.get('API Keys ' + str(api_idx),
                                         'ACCESS_TOKEN_SECRET')

        # Connect to Twitter API
        try:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token_key, access_token_secret)
            api = tweepy.API(auth, wait_on_rate_limit=True)
        except Exception as e:
            print("Error while creating API object: " + str(e))
            continue
        else:
            apis.append(api)

    return apis


def run(user_ids, tweet_ids, curr_datetime, root_dir):
    """
    This run method assumes that data is periodically collected from Twitter
    and stored in folders ordered by timestamp of data collection.

    The task_manager scans the previously stored data, and saves the delta.
        - In the case of followers/followees, it stores the list of followers
          added/subtracted at each run.
        - In the case of timelines, it stores the new tweets by a user after
          the last fetched tweet from a user's timeline.

    Parameters:
        - user_ids (Twitter username/user_id): The list of users for which
          data needs to be collected.
        - tweet_ids: The list of tweets for which data needs to be collected.
        - curr_datetime (str): The current timestamp used to create the
          corresponding directory to store the Twitter data.
        - root_dir (str): The root directory path where all the timestamp
          folders are created.
    """
    print(" --- Collecting twitter data for {} tweets and {} users ---"
          .format(len(tweet_ids), len(user_ids)))

    apis = create_api_objects()

    base_folder_path = root_dir + '/'

    # Load list of users to ignore
    user_ignore_list = set()
    if os.path.exists(base_folder_path + 'user_ignore_list.txt'):
        with open(base_folder_path + 'user_ignore_list.txt') as f:
            for line in f:
                user_ignore_list.add(line.strip())

    twitter_folder_path = base_folder_path + curr_datetime + '/' + 'twitter/'

    if not os.path.exists(twitter_folder_path):
        os.makedirs(twitter_folder_path)

    task_manager = TaskManager(base_folder_path, twitter_folder_path)

    # process_tweets(tweet_ids, user_ignore_list, task_manager, apis)
    # process_users(user_ids, user_ignore_list, task_manager, apis)
    user_relations(user_ids,user_ignore_list,task_manager,apis)

    
if __name__ == "__main__":
    user_ids = []
    tweet_ids = []
    with open('test_comb.pkl','rb') as f:
        user_ids = pickle.load(f)
    # tweet_ids = ['1119577715466698753','1119977050750816256','1097433920453304321','1106523214946013184','1119977624816762880']
    # tweet_ids = ['1114691992292818944','1114997048326139906']
    # tweet_ids = ['1113703461701529601','1113268849271615488','1112588682626621445','1110734214880743424','1109678412526833664','1106523214946013184','1113446173199740928','1113423495604637697','1113352595618164741','1113284661940297728','1113196660644032512','1112451172525174784','1112226861675745281','1112148220119965696','1110306368282652672','1110190033737302018','1093210488652136453','1108021590489354240','1107910672401076224','1100745666135900160','1106273084523327488']
    curr_datetime = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    run(user_ids, tweet_ids, str(curr_datetime), './')
