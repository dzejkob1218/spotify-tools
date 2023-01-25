import os
import sys

# Workaround to import classes properly
test_path = os.path.dirname(os.path.abspath(__file__))
new_path = test_path.rsplit("/", 1)[0]
sys.path.insert(0, new_path)

import pytest
from dotenv import load_dotenv

from classes.spotify_session import SpotifySession


# TODO: Once getting a random playlist is a feature, use it to test any possible input

# Dictionaries of collection and track id's used for testing
PLAYLISTS = {
    "basic_test": "spotify:playlist:0qaWhFRLG86FcXqw47FDtQ",  # small, basic playlist, owned by me (dzejkob1218)
    "edge_test": "411NWDp9tPPcPgt5afBf5x",
    # long playlist, no set image, no description, includes podcasts (also by me)
    "empty_test": "3kPfB9mIkckYOPNxDgie2Q",  # empty playlist
    "running": "37i9dQZF1DWZUTt0fNaCPB",  # spotify's 'running to rock' playlist
}


class TestSpotifySession:
    @pytest.fixture
    def sp(self):
        load_dotenv()
        sp = SpotifySession("")
        yield sp
        sp.remove_cache()

    # Authorize connection once and keep alive for all tests in module
    # Note that to test authorized endpoints, a log in to a working spotify account is needed
    @pytest.fixture
    def sp_auth(self, sp, scope="module"):
        url = sp.auth_manager.get_authorize_url()
        print(f"Visit this url: {url}")
        code = input("Enter the code: ")
        sp.connect(code)
        return sp

    # def test_fetch_user_playlists(self, sp_auth):
    # def test_fetch_user(self, sp_auth):
    # def test_fetch_currently_playing(self, sp_auth):
    # def test_play(self, sp_auth):

    # def test_fetch_bulk_features(self, sp):
    # def test_fetch_playlist_tracks(self, sp):
    # def test_search(self, sp):

    def test_fetch_item(self, sp):
        playlist = sp.fetch_item(PLAYLISTS["basic_test"])
        assert playlist["tracks"]["total"] == 6
        assert playlist["name"] == "SpotifyBuddyTesting"
