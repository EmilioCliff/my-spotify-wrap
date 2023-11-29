import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, request, url_for, session
import time
from flask_sqlalchemy import SQLAlchemy
import os

# Initializing flask app and SQLite db
app = Flask(__name__)
app.config['SESSION_COOKIE_NAME'] = os.environ.get('COOKIE')
app.secret_key = os.environ.get('SECRET_KEY')
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///spotify.db"
db.init_app(app)
TOKEN_INFO = 'my_token'


# Creating Table Schema
class Tracks(db.Model):
    track_id = db.Column(db.Integer, primary_key=True)
    track_name = db.Column(db.String(250), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    track_length = db.Column(db.Float, nullable=False)
    track_popularity = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    print(code)
    token_info = create_spotify_oauth().get_access_token(code)
    session['TOKEN_INFO'] = token_info
    print(token_info)
    return redirect(url_for('wrap', external=True, token=token_info['access_token']))


@app.route('/wrapped')
def wrap():
    try:
        token = request.args.get('token', None)
    except:
        print("User not logged in")
        return redirect('/')
    sp = spotipy.Spotify(auth=token)
    # print(sp.current_user_playing_track())
    # recently_played = sp.current_user_recently_played(limit=30)
    top_tracks = sp.current_user_top_tracks()['items']
    for track in top_tracks:
        artist_name = track['album']['artists'][0]['name']
        track_name = track['name']
        track_length = track['duration_ms']/60000
        track_popularity = track['popularity']
        new_track = Tracks(
            track_name=track_name,
            track_length=track_length,
            track_popularity=track_popularity,
            artist=artist_name
        )
        db.session.add(new_track)
        db.session.commit()
    return "Successful "


# Getting access_token and refreshing if expired
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return redirect(url_for('login', external=False))
    is_expired = token_info['expires_in'] - int(time.time()) < 60
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


# Getting the authorization URL
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.environ.get('CLIENT_ID'),
        client_secret=os.environ.get('CLIENT_SECRET'),
        scope="user-top-read user-read-recently-played user-read-currently-playing",
        redirect_uri=url_for('redirect_page', _external=True)
    )


if __name__ == "__main__":
    app.run(debug=True)
