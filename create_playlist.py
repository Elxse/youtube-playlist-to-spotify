#!usr/bin/env python3

# Create spotify playlist from my "Music" youtube folder

import json
import requests
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

from secrets import spotify_token, spotify_user_id

class PlayList:
    def __init__(self, playlist_name):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.getYoutubeClient()
        self.youtube_playlist_name = playlist_name
        self.youtube_playlist_id = self.getYoutubePlaylistID()
        self.n_songs = 0
        self.all_song_info = {}

    def getYoutubeClient(self):
        """Log into YouTube."""

        # Copied from Youtube Data API
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_id.json"

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

        for playlist in response["items"]:
            if(playlist["snippet"]["title"] == self.youtube_playlist_name):
                playlist_id = playlist["id"]
                self.n_songs = playlist["contentDetails"]["itemCount"]
                break

        return playlist_id

    def getYoutubeVideos(self):
        """Fetches a playlist of videos from a youtube playlist and creates a dictionary of important song information."""

        request = self.youtube_client.playlistItems().list(
            part="snippet",
            playlistId=self.youtube_playlist_id,
            maxResults=25
        )
        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["snippet"]["resourceId"]["videoId"])

            # Use youtube_dl to collect the song name and artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            # Save all important information
            if song_name is not None and artist is not None:
                spotify_uri = self.getSpotifyUri(song_name, artist) # add the uri, easy to get song to put into playlist
                if(spotify_uri != 0):
                    self.all_song_info[video_title] = {
                        "youtube_url": youtube_url,
                        "song_name": song_name,
                        "artist": artist,
                        "spotify_uri": spotify_uri
                    }
        
    def createPlaylist(self):
        """Create a new playlist.

            Returns:
                str -- the spotify ID of the playlist
        """

        # Request path (user's spotify UID)
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)

        # Header fiels
        header_fields = {
            "Authorization": "Bearer {}".format(self.spotify_token),    # info about the client requesting the resource (required by spotify)
            "Content-Type": "application/json"                       # info about the body of the resource (required by spotify)
        }

        # Convert Python to JSON (object to send to the server, we can also use the arg "json")
        request_body = json.dumps({
            "name": "yt discoveries",
            "description": "music discoveries in youtube",
            "public": True
        })

        # Response 
        response = requests.post(
            query,
            data=request_body,                                  
            headers=header_fields
        )

        # Convert the JSON response into a python dictionnary 
        response_json = response.json()

        # Playlist id
        return response_json["id"]

    def getSpotifyUri(self, song_name, artist):

        # Header field
        header_fields = {
            "Authorization": "Bearer {}".format(self.spotify_token),    
            "Content-Type": "application/json" 
        }

        # Query parameters
            # q : query keywords
            # type : item types to search across
            # limit : maximum number of results to return
            # offset : the index of the first result to return
        query = "https://api.spotify.com/v1/search?q=track:{0}+artist:{1}&type=track&limit=20&offset=0".format(song_name, artist)

        # Response
        response = requests.get(
            query,
            headers=header_fields
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # Only return the uri of the first song
        uri = 0
        if(len(songs) != 0):
            uri = songs[0]["uri"]
        return uri

    def addTrackToPlaylist(self):
        # Populate our songs dictionary
        self.getYoutubeVideos()

        # Collect all uri
        uris = []
        for _, info in self.all_song_info.items():
            uris.append(info["spotify_uri"])

        # Create a new playlist
        playlist_id = self.createPlaylist()

        # Query path
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        # Header fields
        header_fields = {
            "Authorization": "Bearer {}".format(self.spotify_token),
            "Content-Type": "application/json"
        }

        # Request body with the list of all songs uri
        request_body = json.dumps(uris)

        response = requests.post(
            query,
            data=request_body,
            headers=header_fields
        )
        
        response_json = response.json()
        return response_json

if __name__ == '__main__':
    cp = PlayList("Music")
    cp.addTrackToPlaylist()