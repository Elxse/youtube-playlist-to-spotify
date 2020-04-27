#!usr/bin/env python3

# playlist.py -- Create or update a spotify playlist from any youtube folder

# usage: python playlist.py arg[1] arg[2] arg[3] 
# where 
#   arg[1] -- the name of the spotify playlist you want to create/update
#   arg[2] -- the name of the youtube playlist to fetch the songs from
#   arg[3] -- "create" or "update"
# attention: case sensitive and no space


import json
import requests
import os
import sys 

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

from secrets import spotify_token, spotify_user_id
from parse_text import mainText

class Playlist:
    def __init__(self, spotify_playlist_name, youtube_playlist_name, spotify_playlist_description="music discoveries from youtube"):
        self.request_header_fields = {
            "Authorization": "Bearer {}".format(spotify_token),    
            "Content-Type": "application/json" 
        }

        self.spotify_user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.spotify_playlist_name = spotify_playlist_name
        self.spotify_playlist_id = ""
        self.spotify_playlist_description = spotify_playlist_description

        self.youtube_client = self.getYoutubeClient()
        self.youtube_playlist_name = youtube_playlist_name
        self.youtube_playlist_id = self.getYoutubePlaylistID()

        self.songs_info = self.getYoutubeVideos()
        self.songs_uris = self.getAllUris()    
    

    ########################
    # ------ YOUTUBE ------
    ########################
    def getYoutubeClient(self):
        """Log into YouTube."""

        # Copied from Youtube Data API
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube Data API
        youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

        return youtube_client

    def getYoutubePlaylistID(self):
        """Get videos from any YouTube folder."""

        request = self.youtube_client.playlists().list(
            part="snippet,contentDetails",
            maxResults=25,
            mine=True
        )
        response = request.execute()

        playlist_id = -1
        for playlist in response["items"]:
            if(playlist["snippet"]["title"] == self.youtube_playlist_name):
                playlist_id = playlist["id"]
                self.n_songs = playlist["contentDetails"]["itemCount"]
                break

        if playlist_id == -1:
            raise ValueError("could not find the youtube playlist named {}".format(self.youtube_playlist_name))

        return playlist_id

    def getYoutubeVideos(self):
        """Fetches a playlist of videos from a youtube playlist and creates a dictionary of important song information."""

        request = self.youtube_client.playlistItems().list(
            part="snippet",
            playlistId=self.youtube_playlist_id,
            maxResults=25
        )
        response = request.execute()
        
        songs_info = {}
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["snippet"]["resourceId"]["videoId"])

            # Use youtube_dl to collect the song name and artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = mainText(video["track"])
            artist = mainText(video["artist"])

            # Save all important information
            if song_name is not None and artist is not None:
                spotify_uri = self.getSpotifyUri(song_name, artist) # add the uri, easy to get song to put into playlist
                if(spotify_uri != 0):
                    songs_info[video_title] = {
                        "youtube_url": youtube_url,
                        "song_name": song_name,
                        "artist": artist,
                        "spotify_uri": spotify_uri
                    }
        return songs_info
    
    #######################
    # ------ TRACKS ------
    #######################
    def getSpotifyUri(self, song_name, artist):
        # Query parameters
            # q : query keywords
            # type : item types to search across
            # limit : maximum number of results to return
            # offset : the index of the first result to return
        query = "https://api.spotify.com/v1/search?q=track:{0}+artist:{1}&type=track&limit=20&offset=0".format(song_name, artist)

        # Response
        response = requests.get(
            query,
            headers=self.request_header_fields
        )
        response.raise_for_status()

        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # Only return the uri of the first song
        uri = 0
        if(len(songs) != 0):
            uri = songs[0]["uri"]
        return uri

    def getAllUris(self):
        uris = [info["spotify_uri"] for _, info in self.songs_info.items()]
        return uris

    ################################
    # ------ CREATE PLAYLIST ------
    ################################
    def createPlaylist(self):
        """Create a new playlist and return its spotify id."""

        # Request path (user's spotify UID)
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.spotify_user_id)

        # Convert Python to JSON (object to send to the server, we can also use the arg "json")
        request_body = json.dumps({
            "name": self.spotify_playlist_name,
            "description": self.spotify_playlist_description,
            "public": True
        })

        # Response 
        response = requests.post(
            query,
            data=request_body,                                  
            headers=self.request_header_fields
        )
        response.raise_for_status()

        # Convert the JSON response into a python dictionnary 
        response_json = response.json()
        return response_json["id"]

    def addTracks(self):
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(self.spotify_playlist_id)

        # Request body with the list of all songs uri
        request_body = json.dumps(self.songs_uris)

        response = requests.post(
            query,
            data=request_body,
            headers=self.request_header_fields
        )
        response.raise_for_status()

    def create(self):
        """Create a new playlist and add songs from the youtube playlist."""

        self.spotify_playlist_id = self.createPlaylist()
        self.addTracks()
        print("Creation done!")

    ################################
    # ------ UPDATE PLAYLIST ------
    ################################
    def getSpotifyPlaylistId(self):
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.spotify_user_id)

        response = requests.get(
            query,
            headers=self.request_header_fields
        )
        response.raise_for_status()

        response_json = response.json()
        playlist_id = -1
        for playlist in response_json["items"]:
            if(playlist["name"] == self.spotify_playlist_name):
                playlist_id = playlist["id"]
                break

        if playlist_id == -1:
            raise ValueError("could not find the spotify playlist named {}".format(self.spotify_playlist_name))

        return playlist_id

    def replaceTracks(self):
        query = "https://api.spotify.com/v1/playlists/{0}/tracks?uris={1}".format(self.spotify_playlist_id, ",".join(self.songs_uris))
        response = requests.put(
            query,
            headers=self.request_header_fields
        )
        response.raise_for_status()

    def update(self):
        """Updates spotify playlist with songs from the youtube playlist."""

        self.spotify_playlist_id = self.getSpotifyPlaylistId()
        self.replaceTracks()
        print("Update done!")

if __name__ == '__main__':
    
    assert len(sys.argv) == 4, "Expected three arguments: spotify_playlist_name, youtube_playlist_name, action between create and update"

    spotify_playlist_name, youtube_playlist_name, action = sys.argv[1:]
    assert action == "create" or action == "update", "action takes its value in ('create', 'update')"

    playlist = Playlist(spotify_playlist_name, youtube_playlist_name)

    
    if action == "create":
        print("would you like to add a description for the new playlist? [y/n]")
        ans = input()
        assert ans == "y" or ans == "n", "enter 'y' or 'n'"
        if(ans == "y"):
            print("your description: ", end="")
            playlist.spotify_playlist_description = input()
        playlist.create()
    else:
        playlist.update()
    