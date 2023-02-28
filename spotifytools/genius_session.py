from helpers import uniform_title
from fuzzywuzzy import fuzz
from lyricsgenius import Genius
import os

class GeniusSession:
    def __init__(self):
        self.connection = Genius(os.environ.get("GENIUS_SECRET"))

    def get_lyrics(self, track):
        """Search genius.com for lyrics to a song
        Genius doesn't always return the right lyric as the first result, especially with less popular songs.
        Some songs on Spotify have multiple artists listed and it's not always the first one who is credited as
        the author on Genius.
        """

        name = uniform_title(track.name)

        # TODO: If performance is poor for songs with multiple artists, try searching for each one separately
        artists = track.artists.split(", ")
        print(f"Searching for lyrics to {name} by {artists}")
        page = self.connection.search_song(name, artists[0])
        if not page:
            return "No lyrics available."

        # Check if any of the listed artists and the track title more or less match the result.
        artist_match = any(
            [
                (fuzz.ratio(page.artist.lower(), artist.lower()) > 70)
                for artist in artists
            ]
        )
        title_match = fuzz.partial_ratio(page.title.lower(), name.lower()) > 70

        if title_match and artist_match:
            return cleanup_lyrics(page.lyrics)
        else:
            return "No lyrics available."


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
