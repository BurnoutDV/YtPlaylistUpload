import json, logging
from datetime import datetime, timedelta

from TwitchHandler import TwitchHandler

config_file_path = "yt-data.json"
scope = "channel_editor collections_edit"
#scope = "channel:manage:videos user:read:email collections_edit channel_editor user_read"

logging.basicConfig(filename='test_sync.log', format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO)

"""
This is definitely the opposite of orderly but it serves its purpose, as i need channel_editor for the old
v5 API for my purpose this is what is hardcoded here. But it might change. In my case all the juicy secret
API keys are written as a flat dictionary in a json file, but this should work even if you choose to be a 
bit more careful with your client secret
"""

if __name__ == "__main__":
    try:
        with open(config_file_path, "r") as config_file:
            my_dict = json.load(config_file)
    except Exception as e:
        print(f"Didn't worked out: {e}")

    # checks if token has enough time left
    if 'TWITCH_TOKENSCOPE' in my_dict and my_dict['TWITCH_TOKENSCOPE'] == scope:
        if 'TWITCH_TOKEN_LIFETIME' in my_dict:
            # ? there might be an argument being made that i should check if that string is an ISO one
            token_time = datetime.fromisoformat(my_dict['TWITCH_TOKEN_LIFETIME'])
            future_now = datetime.now() + timedelta(days=7)
            if token_time > future_now:
                print("Token renewal aborted, there are more than 7 days left")
                exit(0)

    twitch = TwitchHandler(my_dict['TWITCH_CLIENT_ID'], my_dict['TWITCH_TOKEN'])
    if 'TWITCH_CLIENT_SECRET' in my_dict:
        twitch.secret = my_dict['TWITCH_CLIENT_SECRET']
    else:
        print("Enter Client Secret: ", end="")
        twitch.secret = input()

    print("Loaded API Handler, commencing")
    try:
        token, life = twitch.obtain_server_token(scope)
        my_dict['TWITCH_TOKEN_LIFETIME'] = life.isoformat()
        my_dict['TWITCH_TOKEN'] = token
        my_dict['TWITCH_TOKENSCOPE'] = scope
        with open(config_file_path, "w") as target_file:
            json.dump(my_dict, target_file, indent=4)

    except Exception as e:
        print(f"Something went wrong: [{type(e).__name__}]{e}")
