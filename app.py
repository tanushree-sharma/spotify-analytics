
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
import plotly.express as px
import numpy as np
import pandas as pd
import psutil
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import binned_statistic


plt.switch_backend('Agg') #backend to a non-interactive to prevent crash

AUTHORIZATION_HEADER = ""
#  Client Keys
CLIENT_ID = "3decd3b13fee4dc3828c56b24136abcb"
CLIENT_SECRET = "5fe9f9cdb12f471d8a7e73cd58aea97f"


# Server-side Parameters
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": "http://127.0.0.1:5000/callback/q",
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


@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": "http://127.0.0.1:5000/callback/q",
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

    return render_template("home.html")

def get_data(track_ids):
    accousticness = []

    for track in track_ids:
        top_track_endpoint  = "https://api.spotify.com/v1/audio-features/{}".format(track)
        song_response = requests.get(top_track_endpoint, headers=AUTHORIZATION_HEADER)
        song_data = json.loads(song_response.text)
        song_accousticness = song_data['danceability']
        accousticness.append(song_accousticness)
    
    return accousticness



@app.route("/get_top_tracks", methods=['GET','POST'])
def get_top_tracks():
    num_tracks = request.form['num_songs']

    # Get profile data
    #user_profile_api_endpoint = "{}/me".format("https://api.spotify.com/v1")
    top_track_endpoint  = "https://api.spotify.com/v1/me/top/tracks?limit={}&time_range=short_term".format(num_tracks)
    profile_response = requests.get(top_track_endpoint, headers=AUTHORIZATION_HEADER)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    #playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    #playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    #playlist_data = json.loads(playlists_response.text)

    # Combine profile and playlist data to display
  
    tracks = []

    display_arr = [profile_data][0]['items']
    #display_arr = [profile_data][0]
    for each_track in display_arr:
        tracks.append([each_track][0]['id'])

    all_accousticness = get_data(tracks)

    bin_means = binned_statistic(all_accousticness, np.arange(50), statistic='count', bins=6, range=(0, 1))[0]

    means = (bin_means.astype(int)).tolist()


    return render_template("auth_return.html", values=json.dumps(means))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)

'''
    arr_t = np.array(all_accousticness).T

    sns.set()
    sns.distplot(arr_t, bins=20, hist=True, kde=False, axlabel='Accousticness')
    plt.savefig('./static/accoustic.png')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/callback")
def callback():
    print("2nd page")
    return("nothing")

'''