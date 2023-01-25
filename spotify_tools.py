import typing
from typing import Any
import webbrowser
import tracemalloc
from dotenv import load_dotenv
from typing import Dict, List

# Test main file that will not be present in the library
import classes.spotify as spotify
from classes.spotify_session import SpotifySession
from classes.genius_session import GeniusSession

import helper

# The authorization scope for Spotify API needed to run this app
SCOPE = "user-top-read user-read-currently-playing user-modify-playback-state playlist-read-private playlist-read-collaborative playlist-modify-private"

load_dotenv()
sp = SpotifySession()
genius_session = GeniusSession()
sp.authorize()

navigation_stack = []
command_queue = []
collections = []


# TODO: Best way to avoid passing the session to every constructor
# TODO: Argument chaining to avoid unnecessary menus
# TODO: Navigate lists by name


def update_navigation_stack(item):
    navigation_stack.append(item)

    print(f"{'_' * 25}")
    arrow = False
    for item in navigation_stack:
        if arrow:
            print(" -> ", end="")
        else:
            arrow = True
        if isinstance(item, List):
            print(f"{type(item[0]).__name__ + 's'}", end="")
        if isinstance(item, spotify.Object):
            print(f"{item.name}", end="")
        if isinstance(item, spotify.Track):
            print(f" ({item.artists})", end="")
    print()


def navigate_back():
    navigation_stack.pop()
    if navigation_stack:
        navigate(navigation_stack.pop())
    else:
        navigate_home_menu()


def navigate_playback():
    currently_playing = sp.fetch_currently_playing()
    navigate(currently_playing)


def navigate_home_menu():
    navigation_stack.clear()
    command_queue.clear()
    print(f"{'_' * 25}")
    if sp.authorized:
        user = sp.fetch_user()
        print(f"Logged in as {user.name}")
        currently_playing = sp.fetch_currently_playing()
        print(
            f"Currently playing: {currently_playing.name} by {currently_playing.artists}"
        )
        lists = {"collections": collections}
        take_input(loaded_lists=lists)
    else:
        print("Not logged in")


def navigate(item):
    update_navigation_stack(item)
    if isinstance(item, List):
        navigate_list(item)
    if isinstance(item, spotify.Object):
        navigate_spotify_object(item)


def navigate_spotify_object(spotify_object: spotify.Object):
    """String representing the spotify_object"""
    loaded, unloaded = {}, {}
    # Choose option for viewing object's children depending on if they're loaded already or not
    if isinstance(spotify_object, spotify.Collection):
        # print(f"Children loaded: {spotify_object.children_loaded}")
        # print(f"Children number: {len(spotify_object.children)}")
        child_type_name = spotify_object.child_type.__name__.lower() + "s"
        if spotify_object.children_loaded:
            loaded[child_type_name] = spotify_object.children
        else:
            unloaded[child_type_name] = spotify_object.load_children

    take_input(loaded_lists=loaded, unloaded_lists=unloaded)


def navigate_list(items: List, start=0, number=None):
    """Prints all entries in a list with options for navigating"""
    # TODO: Add pagination
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
    take_input()


# TODO: Separate presenting choices or taking input for a list and a menu
def take_input(loaded_lists: Dict = None, unloaded_lists: Dict = None):
    global command_queue

    # Update available actions with type-specific defaults
    actions = {}

    item = navigation_stack[-1] if navigation_stack else None
    for item_type in TYPE_ACTIONS:
        if isinstance(item, item_type):
            actions.update(TYPE_ACTIONS[item_type])

    # TODO: Actually check for authorization
    for item_type in AUTHORIZED_ACTIONS:
        if isinstance(item, item_type):
            actions.update(AUTHORIZED_ACTIONS[item_type])

    # Display the available choices
    if loaded_lists or unloaded_lists:
        print_list_choices(loaded_lists, unloaded_lists)
    if actions:
        print_choices(actions.keys())
    letterize_menu(actions, loaded_lists, unloaded_lists)

    # Take user input if none is queued
    while not command_queue:
        full_input = input()
        commands = full_input.lower().split()
        command_queue = commands

    # Execute the selected action
    command = command_queue.pop(0)
    i = command[0]
    if actions and i in actions:
        actions[i]()
    elif loaded_lists and i in loaded_lists:
        navigate(loaded_lists[i])
    elif unloaded_lists and i in unloaded_lists:
        navigate(unloaded_lists[i]())
    elif (
        navigation_stack
        and isinstance(item := navigation_stack[-1], List)
        and command.isnumeric()
    ):
        index = int(command)
        # All lists displayed are indexed starting from 1, this warns the user if input is '0'.
        if index == 0:
            print(
                "'0' is not a valid index. Remember lists are indexed starting from 1.",
                end=" ",
            )
        elif index > len(item):
            print("Out of range.", end=" ")
        else:
            navigate(item[int(command) - 1])
    print("Invalid input.")


def print_details(
    details,
):  # resource: classes.spotify_objects.spotify_resource.SpotifyResource):
    for detail in details:
        print(f"{detail}:{'.' * (30 - len(detail))}{details[detail]}")


def letterize_menu(*menus: Dict):
    options = set()
    for menu in menus:
        if menu:
            for choice in menu.copy():
                initial = choice[0]
                options.add(initial)
                menu[choice[0]] = menu.pop(choice)


def print_current_user():
    navigate(sp.fetch_user())


def show_details():
    pass


def show_lyrics():
    item = navigation_stack[-1]
    lyrics = item.get_lyrics(genius_session)
    print("\n" + lyrics)
    input()
    navigate(navigation_stack.pop())


def open_image():
    item = navigation_stack[-1]
    webbrowser.open(item.image, new=2)
    navigate(navigation_stack.pop())


def print_help():
    item = navigation_stack[-1] if navigation_stack else None

    print("_" * 25)
    print(f"Spotify Tools Help:")

    # Check the exact type of the latest item and print the description
    if item:
        item_class_name = type(item).__name__
        print(f"{item_class_name} {'.' * (25 - len(item_class_name))} ", end="")
    for help_type in HELP_TEXT:
        if type(item) == help_type:
            help_text = HELP_TEXT[help_type]
            break

    def print_command_help(command, text):
        print(f"{' ' * 4}{command} {'.' * (20 - len(command))} {text[0]}")
        if len(text) > 1:
            for option in text[1:]:
                print(f"{' ' * 8}{option[0]} {'.' * (20 - len(option[0]))} {option[1]}")

    for text in DEFAULT_HELP_TEXT:
        print_command_help(text[0], text[1])

    # TODO: Actually check for authorization
    available_actions = []
    for actions_type in TYPE_ACTIONS:
        if isinstance(item, actions_type):
            available_actions.extend(TYPE_ACTIONS[actions_type])

    for actions_type in AUTHORIZED_ACTIONS:
        if isinstance(item, actions_type):
            available_actions.extend(AUTHORIZED_ACTIONS[actions_type])

    print("Available commands:")

    for action in available_actions:
        # TODO: Write a test to check all possible options have a help text
        if action not in HELP_TEXT:
            raise Exception(f"Option defined without a help text ({action}).")
        print_command_help(action, HELP_TEXT[action])

    print("\nTip: Input anything to continue anytime you don't see navigation options.")
    input()
    if navigation_stack:
        navigate(navigation_stack.pop())
    else:
        navigate_home_menu()


def new_collection():
    print("Creating new collection")
    input("Name:")


def search():
    print("Search")
    input("Name:")


def print_choices(choices):
    print("|", end="")
    for action in choices:
        print(f" {action.capitalize()} |", end="")
    print()


def print_list_choices(loaded: Dict, unloaded: Dict):
    print("|", end="")
    if loaded:
        for choice in loaded:
            print(f" {choice.capitalize()}: {len(loaded[choice])} |", end="")
    if unloaded:
        for choice in unloaded:
            print(f" {choice.capitalize()} |", end="")
    print()


def load_object():
    """Forces the object to download all available data about its children."""
    pass


# Defines valid commands for navigating different types of objects.
TYPE_ACTIONS = {
    object: {"help": print_help},
    type(None): {"new": new_collection, "search": search, "browse": None},
    List: {"back": navigate_back, "filter": None, "add": None},
    spotify.Object: {
        "back": navigate_back,
        "load": load_object,
        "add": None,
    },
    spotify.Resource: {
        "details": show_details,
    },
    spotify.Collection: {"filter": None, "save": None},
    spotify.User: {},
    spotify.Playlist: {},
    spotify.Track: {"lyrics": show_lyrics, "image": open_image},
    # TODO: Add Artist and Album
}

# Defines additional commands which are available if the session has an authorized user.
AUTHORIZED_ACTIONS = {
    type(None): {"user": print_current_user, "playback": navigate_playback},
    List: {},
    spotify.Object: {"back": navigate_back, "load": load_object, "add": None},
    spotify.Resource: {
        "play": None,
        "queue": None,
    },
    spotify.Collection: {"filter": None, "save": None},
    spotify.User: {"follow": None},
    spotify.Playlist: {"heart": None},
    spotify.Album: {"heart": None},
    spotify.Track: {"lyrics": show_lyrics, "image": open_image, "heart": None},
}

# Help text displayed always
DEFAULT_HELP_TEXT = [
    (
        "Navigation",
        [
            "This command line interface is navigated by inspecting the resource hierarchy one collection or item at a time.",
            (
                "Commands",
                "Commands available at any time are always displayed separated by `|`. Commands can be chained by separating them with spaces. For example, `back back' would navigate back twice.",
            ),
            (
                "Collections",
                "If available, lists of collection's children will be presented in the top row of available commands. If the items within had been loaded into memory, their quantity will appear next to the name. Otherwise, the items will be downloaded from Spotify once the list is opened.",
            ),
            (
                "Display commands",
                "Some commands, like 'help' or 'lyrics' pause the execution to display the result. Input anything to continue. This input is ignored. Any queued up commands will then be executed. For example, `playback lyrics back` would display the lyrics of the currently playing song, await any input and then return one step back.",
            ),
            (
                "Options",
                "Some commands have additional options that can be passed by following the command with a flag. For example, `help -all` will print help text for all commands including their options.",
            ),
            (
                "Matching",
                "Capitalization of input doesn't matter. Commands and names don't have to be complete to match. For example, `b`, `back`, `Back` would all match 'Back', but `bxx` or `Backxx` wouldn't. It's sufficient to use single letters in most cases. Options also match this way, but the `-` symbol must not be omitted. For example, `p l -r` would refresh and display the lyrics of the currently played song (for `playback lyrics -refresh`).",
            ),
        ],
    ),
    ("Filters", [""]),
    ("Authorization", [""]),
    (
        "Objects types",
        [
            "In this documentation, the terms 'collection' and 'resource' refer to different kinds of data.",
            (
                "Resource",
                "Anything that can be viewed and manipulated in Spotify. Resources include tracks, playlists, users, artists and albums. Podcasts aren't supported yet.",
            ),
            (
                "Collection",
                "Anything that contains resources. Collections can be created, modified and stored within this program.",
            ),
            (
                "Collection resource",
                "Refers to a Spotify resource which also stores other resources. Playlists and albums resources store tracks, artist resources store albums, user resources store their public playlists. These cannot be modified, unless it's the authorized user's playlists.",
            ),
        ],
    ),
]

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
        (
            "select",
            "Followed by a name or index has the same effect as the name or index alone, but excludes possibility of mistaking the name for a command. For example, `s back` would match to 'Back In Black'.",
        ),
    ],
    spotify.Collection: [
        "Represents a custom collection of Spotify resources stored in the program's memory. Any type of Spotify resource, like artists and albums, can be added to a custom collection. Collections can be mixed (f.e. contain both tracks and artists).",
    ],
    spotify.User: [
        "Represents a Spotify user. User's public playlists and information can be accessed. More options are available when viewing the user who is verified with Spotify in this session."
    ],
    spotify.Playlist: [
        "Represents a Spotify playlist. Tracks as well as basic information about the playlist can be accessed. More options are available if the playlist belongs to the user verified in this session. Statistics for the playlist can be viewed once the track data is loaded."
    ],
    spotify.Track: [
        "Represents a Spotify track. Details and lyrics need to be loaded with additional requests and are then cached."
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
        ("-all", "Print help text for every option possible."),
        (
            "-nooptions",
            "Skips all information about command options for a more streamlined overview of available commands.",
        ),
        (
            "-search",
            "Only print the help text for a given command. Same effect can be achieved by enclosing the name in quotes. For example, `help -s help` and `help 'help'` will both print help text about the 'help' command, while `help help` will just print the whole help text, pause, then print the whole text again.",
        ),
    ],
    "browse": [
        "Browse content promoted by Spotify.",
    ],
    "back": [
        "Return to the previous Spotify resource, collection or list in the navigation stack.",
        ("-home", "Return to home menu and clear the navigation stack."),
    ],
    "lyrics": [
        "Print lyrics for the song as available on Genius Lyrics. The lyrics are cached after the first request. Requires a valid Genius Lyrics API key. Pauses the execution of chained commands.",
        (
            "-refresh",
            "Clear the cached lyrics and make a new request to Genius Lyrics.",
        ),
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
    navigate_home_menu()
