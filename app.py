
import os
from flask import Flask, render_template, redirect, g, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import os
import sys
import json
import requests
from urllib.parse import quote
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import binned_statistic


AUTHORIZATION_HEADER = ""
#  Client Keys
CLIENT_ID = "3decd3b13fee4dc3828c56b24136abcb"
CLIENT_SECRET = "5fe9f9cdb12f471d8a7e73cd58aea97f"


# Server-side Parameters
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

REDIRECT_URI = "https://sp-analytics-testing.herokuapp.com/callback/q"
#REDIRECT_URI = "http://127.0.0.1:5000/callback/q"


auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": "playlist-modify-private user-top-read",
    "client_id": CLIENT_ID
}

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login")
def auth():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format("https://accounts.spotify.com/authorize", url_args)
    return redirect(auth_url)

def get_top_tracks(time_range):

    top_track_endpoint  = "https://api.spotify.com/v1/me/top/tracks?limit=50&time_range={}".format(time_range)
    profile_response = requests.get(top_track_endpoint, headers=AUTHORIZATION_HEADER)
    profile_data = json.loads(profile_response.text)
  
    tracks = []

    display_arr = [profile_data][0]['items']
    for each_track in display_arr:
        tracks.append([each_track][0]['id'])

    return tracks #return the id of the top 50 tracks

def get_feature_data(track_ids):
    accousticness = []
    danceability = []
    energy = []
    tempo = []
    valence = []


    try: 
        for track in track_ids:
            feat_endpoint  = "https://api.spotify.com/v1/audio-features/{}".format(track)
            song_response = requests.get(feat_endpoint, headers=AUTHORIZATION_HEADER)
            song_data = json.loads(song_response.text)
            song_ac = song_data['acousticness']
            accousticness.append(song_ac)
            song_da= song_data['danceability']
            danceability.append(song_da)
            song_en = song_data['energy']
            energy.append(song_en)
            song_te = song_data['tempo']
            tempo.append(song_te)
            song_va = song_data['valence']
            valence.append(song_va)
        
    except:
        print("Error occured with getting song data")

    # bin data to create hisogram
    ac_bins = binned_statistic(accousticness, np.arange(50), statistic='count', bins=6, range=(0, 1))[0]
    da_bins = binned_statistic(danceability, np.arange(50), statistic='count', bins=6, range=(0, 1))[0]
    en_bins = binned_statistic(energy, np.arange(50), statistic='count', bins=6, range=(0, 1))[0]
    te_bins = binned_statistic(tempo, np.arange(50), statistic='count', bins=6, range=(50, 200))[0] #tempo ranges from 50-200BPM
    va_bins = binned_statistic(valence, np.arange(50), statistic='count', bins=6, range=(0, 1))[0]

    return ((ac_bins.astype(int)).tolist(), (da_bins.astype(int)).tolist(), (en_bins.astype(int)).tolist(), (te_bins.astype(int)).tolist(), (va_bins.astype(int)).tolist())


@app.route("/callback/q", methods=['GET','POST']) 
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post("https://accounts.spotify.com/api/token", data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    global AUTHORIZATION_HEADER    # Needed to modify global copy of globvar
    AUTHORIZATION_HEADER  = {"Authorization": "Bearer {}".format(access_token)}

    #ids of top 50 tracks
    short_top = get_top_tracks("short_term") 
    med_top = get_top_tracks("medium_term")
    long_top = get_top_tracks("long_term")

    short_ac, short_da, short_en, short_te, short_va= get_feature_data(short_top)
    med_ac, med_da, med_en, med_te, med_va= get_feature_data(med_top)
    long_ac, long_da, long_en, long_te, long_va= get_feature_data(long_top)

    return render_template("auth_return.html", short_ac=json.dumps(short_ac), med_ac=json.dumps(med_ac), long_ac=json.dumps(long_ac),
                           short_da=json.dumps(short_da), med_da=json.dumps(med_da), long_da=json.dumps(long_da),
                           short_en=json.dumps(short_en), med_en=json.dumps(med_en), long_en=json.dumps(long_en),
                           short_te=json.dumps(short_te), med_te=json.dumps(med_te), long_te=json.dumps(long_te),
                           short_va=json.dumps(short_va), med_va=json.dumps(med_va), long_va=json.dumps(long_va))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)