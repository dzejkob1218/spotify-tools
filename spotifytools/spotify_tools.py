from lyricsgenius import Genius

import helpers
import webbrowser
from dotenv import load_dotenv
from typing import Dict, List

import spotifytools.filters.audio.language
import spotifytools.spotify as spotify
from spotifytools.spotify_session import SpotifySession
from spotifytools.genius_session import GeniusSession
from spotifytools.filters.audio.language import LanguageFilter
# The authorization scope for Spotify API needed to run this app
SCOPE = "user-top-read user-read-currently-playing user-modify-playback-state playlist-read-private playlist-read-collaborative playlist-modify-private"

load_dotenv()
sp = SpotifySession()
genius_session = GeniusSession()
sp.authorize()

# TODO: Best way to avoid passing the session to every constructor

def navigate_playback():
    # TODO: This could be turned into a utility shorthand
    currently_playing = sp.fetch_currently_playing()
    navigate(currently_playing)


def print_current_user():
    # TODO: Could also use shorthand to do this
    navigate(sp.fetch_user())

def navigate_home_menu():
    print(f"{'_' * 25}")
    if sp.authorized:
        user = sp.fetch_user()
        print(f"Logged in as {user.name}")
        currently_playing = sp.fetch_currently_playing()

        if currently_playing:
            print(
                f"Currently playing: {currently_playing.name} by {[a.name for a in currently_playing.artists]}"
            )
        lists = {"collections": collections}
        take_input(loaded_lists=lists)
    else:
        print("Not logged in")

def navigate_list(items: List, start=0, number=None):
    """Prints all entries in a list with options for navigating"""
    # TODO: Some nice way to print all children with an option to limit number could be integrated into Colllection
    total = len(items)
    end = total if not number or start + number > total else start + number
    for i in range(start, end):
        item = items[i]
        name_in_quotes = '"' + item.attributes["name"] + '":'
        # Note this starts indexing from 1 intentionally
        print(
            f"{str(i + 1) + ':':5}", end=""
        )  # TODO: Replace the 5-space gap here with the smallest uniform gap possible
        print(f"{name_in_quotes}")


def print_details():
    # TODO: A nice way to present details could also be preserved and integrated
    details = {**item.attributes, **item.get_features()}

    #if isinstance(item, spotify.Track):
        #confidence_scores = item.get_confidence_scores()
        #details.update({'lyrics': bool(item.lyrics), 'language': item.language})
    for i in details:
        value = details[i]
        if isinstance(value, float):
                value = round(value, 2)
        print(f"{i} {'.' * (25 - len(i))} {value}", end='')
        #if isinstance(item, spotify.Track) and i in confidence_scores:
        #    print(f" ({round(confidence_scores[i],2)}) ", end='')
        print()


def show_lyrics():
    # TODO: Lyrics also need some print alternative to spitting out the raw string
    lyrics = item.get_lyrics()
    print("\n" + lyrics)
    return
    if language := item.get_language():
        print(language)
        print(helpers.language_name(language[0].lang))
        input()
    navigate(navigation_stack.pop())


def open_image():
    # TODO: This could use a method
    item = navigation_stack[-1]
    webbrowser.open(item.album.images[-1], new=2)
    print("Opening cover image in browser...")
    navigate(navigation_stack.pop(), silent=True)


def load_object():
    """Force the object to download all available data about itself and its children."""
    item: spotify.Object = navigation_stack[-1]
    item.load()
    print("Loading object data...")
    navigate(navigation_stack.pop(), silent=True)

# TODO: Tracks can be manually added or removed to and from a collection to make it unrepresentative of actual state
# TODO: There should be:
# TODO:  - A way to flag that a collection is modified (custom)
# TODO:  - A method to compare it against the real spotify object
# TODO:  - A method to push the changes back up to Spotify
# TODO:  - Ideally, a resource representing Spotify data should be immutable, and modifying it should return a copy
# TODO:  - Changes on code side must be distinguished from discrepancies due to changes on Spotify side

# TODO: Actions described here should be doable via code
# Help text for all types and commands.
HELP_TEXT = {
    List: [
        "Represents a collection of Spotify resources. Items can be selected in multiple ways:",
        (
            "By index",
            "Entering an integer in range of the list will select the item. Keep in mind indexing starts from 1 to match how Spotify displays lists.",
        ),
        (
            "By name",
            "If any list entry matches the input by name, it will be selected. The name doesn't have to be complete to match. Available commands have priority over list entries. Whitespace and special symbols are ignored. Put the name in quotes to avoid matching a command and include whitespace and symbols. Without quotes, words after spaces will be interpreted as following commands. For example: `Back_In_Black`, `backinb`, `\"back in black\" would all match to 'Back In Black', but just typing `back in black` would first navigate you back one level and then print 'Invalid input' twice.`",
        ),
    ],
    "add": [
        "Adds the resource or items within a collection to a specified collection. Called without arguments will bring up a list of valid targets. By default, followed only by name of a valid target, will add the resource(s) to the collection. By default, items will be added to a custom collection exactly (f.e. adding a playlist will add the whole playlist, not just its tracks).",
        (
            "-collection",
            "Followed by the name of target collection. For example, `add collection1` and `add -c collection1` have the same result.",
        ),
        (
            "-tracks",
            "Adds just the tracks from the collection, instead of collection resources like artists and albums. For example, `Collection1 add Collection2 -t` has the same effect as `Collection1 tracks add Collection2`. Has no effect when adding to a Spotify playlists, where only tracks are added by default.",
        ),
    ],
    "heart": [
        "Requires an authorized user. Saves the resource to user's library.",
    ],
    "help": [
        "Prints this help text. By default includes a description for every currently available option.",
    ],
    "browse": [
        "Browse content promoted by Spotify.",
    ],
    "lyrics": [
        "Print lyrics for the song as available on Genius Lyrics. The lyrics are cached after the first request. Requires a valid Genius Lyrics API key. Pauses the execution of chained commands.",
        (
            "-refresh",
            "Clear the cached lyrics and make a new request to Genius Lyrics.",
        ),
        ("-languages", "Show the probabilities for different languages."),
    ],
    "new": [
        "Creates a new collection",
    ],
    "search": [
        "Search",
    ],
    "user": [
        "View verified user",
    ],
    "details": [
        "View all available details about a resource. By default has the same effect as `load`.",
        ("-refresh", "Clear and reload cached information."),
        ("-noload", "Don't load any new data, only display what's already cached."),
    ],
    "playback": [
        "Navigate to the track currently playing. If the display has not been refreshed since the track changed, it will be outdated. By default, `playback` displays the track playing at the moment of making the request.",
        (
            "-noload",
            "Navigate to the track being displayed as 'currently playing', even if the playback had already changed in Spotify.",
        ),
    ],
    "image": [
        "Open the link to the full-resolution album cover with the default system browser."
    ],
    # TODO: Clarify how recursive loading with multiple flags should work.
    "load": [
        "Downloads all available data about the object's children. Usually more efficient than loading each item separately. Not recursive by default (doesn't load children's children). Doesn't load lyrics by default. Once loaded, the collective statistics about the object's children can be accessed.",
        (
            "-tracks",
            "Load a collection recursively down to the tracks. Can take a lot of time.  Will apply all other flags to the recursively loaded objects. For example, `User1 load -recursive -artists` will load all tracks in all User1's playlists, including track details, but not lyrics, as well as all artists featuring in the playlists, but NOT any of these artists' other tracks or albums.",
        ),
        (
            "-artists",
            "Load all artists associated with the tracks and albums being loaded.",
        ),
        ("-albums", "Load all albums associated with tracks and artists being loaded."),
        ("-users", "Load users associated with the playlists being loaded."),
        (
            "-all",
            "Loads all available resources and details associated with the collection, excluding lyrics. Alias for `-tracks -artists -albums -users`",
        ),
        (
            "-lyrics",
            "Load lyrics for all tracks inside the collection. Needs to be included explicitly. Can cause a significant overhead. Each track needs a separate request to Genius Lyrics.",
        ),
    ],
    "tracks": [
        "Display the final list of all tracks within a collection after gathering them from collection resources and "
    ],
}

if __name__ == "__main__":
    # TODO: Using this shouldn't require running a script at all, just importing the SpotifySession from the package
    # TODO: On start should print if logged in and maybe if there's currently playing
    navigate_home_menu()
