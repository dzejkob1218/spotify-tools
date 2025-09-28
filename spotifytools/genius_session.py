import spotifytools.spotify as spotify
import requests
from spotifytools.helpers import uniform_title
from fuzzywuzzy import fuzz
from lyricsgenius import Genius
import os


class GeniusSession:
    NO_LYRICS_PLACEHOLDER = 'No lyrics available.'

    def __init__(self):
        self.token = os.environ.get("GENIUS_TOKEN")
        self.connection = Genius(self.token)
        self.header = headers = {'Authorization': 'Bearer ' + self.token}

    def get_features(self, query):
        """
        Get genius features from a query preferably consisting of a title and artists.

        This function makes a direct call to the genius API without using lyricsgenius.

        """
        # TODO: Should this be replaced with lyricsgenius entirely?
        # TODO: Rip solutions from geniuslyrics
        url = 'https://genius.com/api/search'
        params = {'q': query}

        # Set the API headers with the access token

        # Make the API request
        response = requests.get(url, params=params, headers=self.header)

        # TODO: Check the hits instead of blindly going with the first one
        hits = response.json()['response']['hits']
        if hits:
            hit_id = hits[0]['result']['id']
            response = requests.get('https://api.genius.com/songs/' + str(hit_id), headers=self.header).json()

            data = response['response']['song']
            return spotify.GeniusFeatures(data)
        else:
            return None


    def get_lyrics(self, track):
        """Search genius.com for lyrics to a song
        Genius doesn't always return the right lyric as the first result, especially with less popular songs.
        Some songs on Spotify have multiple artists listed and it's not always the first one who is credited as
        the author on Genius.
        """

        name = uniform_title(track.name)

        # TODO: If performance is poor for songs with multiple artists, try searching for each one separately
        artists_string = ", ".join([artist.name for artist in track.artists])
        print(f"Searching for lyrics to {name} by {artists_string}")
        page = self.connection.search_song(name, track.artists[0].name)
        if not page:
            return self.NO_LYRICS_PLACEHOLDER

        # Check if any of the listed artists and the track title more or less match the result.
        artist_match = any(
            [
                (fuzz.ratio(page.artist.lower(), artist.lower()) > 70)
                for artist in [artist.name for artist in track.artists]
            ]
        )
        title_match = fuzz.partial_ratio(page.title.lower(), name.lower()) > 70

        if title_match and artist_match:
            return cleanup_lyrics(page.lyrics)
        else:
            return self.NO_LYRICS_PLACEHOLDER


def cleanup_lyrics(text):
    """Cleans up common errors in genius results"""

    # TODO: You might also like[Chorus], You might also like[Instrumental]  - spotted in the wild

    text = text.split("Lyrics", 1)[1]

    if text[-5:] == "Embed":
        text = text.split("Embed", 1)[0]

    # Remove random numbers from end of lyrics
    while text[-1].isnumeric():
        text = text[:-1]

    if text[-19:] == "You might also like":
        text = text.split("You might also like", 1)[0]

    return text
