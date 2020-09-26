import requests
import random


bearer_token = 'AAAAAAAAAAAAAAAAAAAAAJwtIAEAAAAARWv%2FIfswc6tKCJJVyd6xUN078ew%3DIPAveOB4aMJ3q40C2OKV3E3E3P2bctKlunuOO1hWYbZ0eYrvoj'
headers = {'Authorization': 'Bearer %s' % bearer_token}


def filter_media(tweets): #Keep all the tweets that do not contain media
    return [tweet for tweet in tweets if not ('media' in tweet['entities'] and tweet['entities']['media'])]


def filter_urls(tweets): #Keep all the tweets that do not contain urls
    return [tweet for tweet in tweets if not ('urls' in tweet['entities'] and tweet['entities']['urls'])]


def filter_tags(tweets): #Keep all the tweets that do not contain user_mentions
    return [tweet for tweet in tweets if not ('user_mentions' in tweet['entities'] and tweet['entities']['user_mentions'])]


# api only allows a response of max 200 tweets, but it's usually far less after filtering retweets, replies, and tags
def get_tweet_batch(screen_name, max_amount=200, before_id=None, filtered=True):
    before_parameter = '&max_id=%d'%before_id if before_id else '' #keep track of the newest tweets id so we can get old tweets after the inital 200
    filters_parameter = '&include_rts=false&exclude_replies=true' if filtered else '' #no retweets and replies
    response = requests.get("https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=%s&count=%d%s%s" % (screen_name, max_amount, filters_parameter, before_parameter), headers=headers)
    tweets = response.json()
    if not tweets:
        if filtered:
            unfiltered_tweets = get_tweet_batch(screen_name, max_amount, before_id, False)
            last_id = unfiltered_tweets[1]
        else:
            return None, None
    else:
        last_id = tweets[-1]['id']-1
    if filtered: #normal case that filters and loads the tweets for the game and keeps track of the last tweets id that way we cna  show new tweets
        tweets = filter_tags(tweets)
        tweets = filter_urls(tweets)
        tweets = filter_media(tweets)
    return tweets, last_id


# can only look as far back as 3200 tweets ago, including retweets, replies, tags, and media, so only a few hundred on average can be scraped per account
def get_exactly_n_tweets(screen_name, exact_amount, before_id=None):
    tweets = []
    while len(tweets) < exact_amount: #loop until we get 3200 tweets or until we stop getting tweets
        next_batch, before_id = get_tweet_batch(screen_name, 200, before_id)
        if not next_batch:
            return tweets
        tweets += next_batch
    return tweets[:exact_amount]


def pick_users(): # the interface that lets you choose how you want to play the game
    users = {1: 'elonmusk', 2: 'kanyewest'}
    print('Do you want to play with elonmusk and kanyewest or custom twitter handles?')
    answer = input('1) Default\n2) Custom\nYour choice (1 or 2): ').strip()
    while answer not in ['1','2']:
        print('\nERROR: Your answer must be either "1", "2", or "3" without the quotes')
        answer = input('1) Default\n2) Custom\nYour choice (1 or 2): ').strip()
    if answer == '2':
        for num in range(1,3):
            users[num] = input('Twitter handle number %d: ' % num).strip()
    return users


def get_user_tweets(users): #get the actual text from each tweet to store them
    print('Loading...')
    user_to_tweets = {}
    for user in users.values():
        tweets = get_exactly_n_tweets(user, 3200)
        user_to_tweets[user] = [tweet['text'] for tweet in tweets]
    return user_to_tweets


def gen_game_screen(right, wrong, tweet, users):
    return """
Right answers: %d\tWrong answers: %d

Mystery tweet:
    %s

Who wrote it?
1) %s
2) %s
3) [QUIT]

Your answer (1, 2, or 3): """ % (right, wrong, tweet, users[1], users[2])


def gen_end_screen(right, wrong):
    return """
Good game! Here are your results:

Right answers: %d
Wrong answers: %d
Percent correct: %.1f%%
""" % (right, wrong, right/(right+wrong)*100)


if __name__ == '__main__':
    print('Welcome to the hit gameshow, Kanye Musk!')

    users = pick_users()
    user_to_tweets = get_user_tweets(users)

    right = 0
    wrong = 0
    while True:
        print('\n\n\n\n\n')

        user = random.choice(list(user_to_tweets.keys()))
        if not user_to_tweets[user]:        #edge case if you run out of tweets then the game is over and print your results
            print("Wow, you've gone through all of %s's recent tweets. I guess this means game over." % user)
            break
        tweet_ind = random.randint(0, len(user_to_tweets[user])-1)      #choose a random number
        tweet = user_to_tweets[user][tweet_ind]     #find the tweet associated with that number to display
        del user_to_tweets[user][tweet_ind]     #then deleting that tweet completely

        game_screen = gen_game_screen(right, wrong, tweet, users)

        answer = input(game_screen).strip()
        while answer not in ['1','2','3']:
            print('\nERROR: Your answer must be either "1", "2", or "3" without the quotes')
            answer = input(game_screen).strip()
        answer = int(answer)

        if answer == 3:
            break
        correct = users[answer] == user
        if correct:
            right += 1
        else:
            wrong += 1
        print('You are %s!' % ('CORRECT' if correct else 'WRONG'))
        input('Press enter to see the next tweet...')

    end_screen = gen_end_screen(right, wrong)
    print(end_screen)