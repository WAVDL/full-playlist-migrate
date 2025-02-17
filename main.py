
# Copyright (C) 2025 William Van Der Laar
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. 

"""
A simple script to copy a user's playlist from their Spotify account to their Tidal account.
"""

import spotipy
from spotipy.oauth2 import SpotifyPKCE
from pathlib import Path
import tidalapi

# I've only registered a spotify app in development, so the number of users are limited.
# If you run into issues authenticating with Spotify, consider registering your own App and replacing these values.
SPOTIFY_CLIENT_ID="89e61cd20e2048c2b449080829939f6e"
SPOTIFY_REDIRECT_URL = "https://wavdl.blog"

def get_playlist(sp, username, playlist_id):
    """Given a Spotify playlist Id, collects and returns all of the songs in the playlist."""
    songs = []
    read = 0
    page, total = 100, 100
    while read < total:
        results = sp.user_playlist_tracks(username, playlist_id, limit=page, offset=read)
        for idx, item in enumerate(results['items']):
            track = item['track']
            print(read+idx, track['artists'][0]['name'], " – ", track['name']) 
            songs.append(track)
        read += page
        total = results['total']
    return songs

def get_all_playlists(sp):
    """
    Gets all playlists of the current logged in user.
    Also prints their names with an index so the user may select one.
    """
    playlists = dict()
    read, page, total = 0, 50, 1
    while read < total:
        results = sp.current_user_playlists(limit=page, offset=read)
        for idx, item in enumerate(results['items']):
            print(f"{idx}) {item['name']}")
            playlists[idx] = item['uri']
        read += page
        total = results['total']
    return playlists


def spotify_auth():
    """Prompts the user to log in via PKCE (or uses cached token)."""
    print(f"Logging in to Spotify!")
    scope = "user-library-read playlist-read-private"
    auth_manager = SpotifyPKCE(
        scope=scope, 
        client_id=SPOTIFY_CLIENT_ID, 
        redirect_uri=SPOTIFY_REDIRECT_URL,
        open_browser=False,
    )

    sp = spotipy.Spotify(auth_manager=auth_manager)
    print(f"You're logged in to Spotify as {sp.current_user()['display_name']}")
    print(f"(To force a new login, delete the file at .cache)\n")
    return sp

def tidal_auth():
    """Prompts the user to log in (or uses cached session)."""
    print(f"Logging in to Tidal!")
    file_name = ".tidal_session"
    session = tidalapi.Session()
    session.login_session_file(Path(file_name))
    metadata = session.user.profile_metadata
    print(f"You're logged in to Tidal as {metadata['firstName']} {metadata['lastName']} | {metadata['email']}")
    print(f"(To force a new login, delete the file at {file_name})\n")
    return session

def tidal_get_tracks(td, songs):
    """Uses the ISRC values returned by Spotify to lookup and return corresponding Tidal tracks."""
    print(f"\nCollecting track list... \n")
    result = []
    skipped=0
    for song in songs:
        try:
            tracks = td.get_tracks_by_isrc(song['external_ids']['isrc'].upper())
        except:
            skipped+=1
            print(f"Tidal couldn't locate {song['artists'][0]['name']} – {song['name']}")
            continue
        result.append(tracks[0])
    if skipped:
        print(f"Unable to find {skipped} track(s)")
    return result


def tidal_create_playlist(td, tracks):
    """Given a list of Tidal tracks, creates a playlist in Tidal."""
    playlist_title = input("Enter Tidal playlist title (Default: full-playlist-migrate)") or 'full-playlist-migrate'
    description = "This playlist created using full-playlist-migrate. Service provided by https://wavdl.blog"
    playlist = td.user.create_playlist(playlist_title, description)
    media_ids = [t.id for t in tracks]
    added = 0
    page = 100
    while added < len(tracks):
        playlist.add(
                media_ids[added:], 
                #allow_duplicates=True, 
                limit= page)
        added += page



def main():
    print(f"\n Thanks for using full-playlist-migrator! I'll try to walk you through everything. \n")
    td = tidal_auth()
    sp = spotify_auth()
    
    # username = input(f"Enter spotify username (Default: {user['display_name']}):") or user['id']
    playlists = get_all_playlists(sp)
    playlist = input("\nEnter a number to select a playlist (Default: 0):") or 0
    playlist_id = playlists[int(playlist)]
    songs = get_playlist(sp, sp.current_user()['id'], playlist_id)
    tracks = tidal_get_tracks(td, songs)
    tidal_create_playlist(td, tracks)
    




if __name__ == "__main__":
    main()
