import tweepy as tw  # https://docs.tweepy.org/en/stable/

# for now just a script to remove from followers and followings who is not mutual

def main():
    consumer_key = ''
    consumer_secret = ''
    acess_token = ''
    acess_token_secret = ''

    auth = tw.OAuthHandler(consumer_key, consumer_secret).set_acess_token(acess_token, acess_token_secret)
    api = tw.API(auth)

    follower_list = api.get_follower_ids(user_id='')
    following_list = api.get_friends_ids(user_id='')

    for user in follower_list:
        if user not in following_list:
            api.create_block(user_id=user)
            api.destroy_block(user_id=user)

    for user in following_list:
        if user not in follower_list:
            api.destroy_friendship(user_id=user)

if __name__ == "__main__":
    main()