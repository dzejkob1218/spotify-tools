from langdetect.lang_detect_exception import LangDetectException
from typing import List
import re
import langdetect
from langcodes import Language


def details_adapter(details):
    """
    Processes resource data from Spotify API for easier processing.
    """

    # These entries contain data representing another Spotify resource.
    related_resources = ['owner', 'artist', 'artists', 'tracks', 'album', 'albums']

    # Alias and procedure to extract each parsed detail.
    procedures = {
        'external_urls': ('url', lambda data: data['spotify']),
        'followers': ('followers', lambda data: data["total"]),
        'tracks': ('total_tracks', lambda data: data["total"]),
        'images': ('images', lambda data: sort_image_urls(data)),
        'duration_ms': ('duration', None),
        'display_name': ('name', None),
    }
    parsed_details = {}

    for detail in details:
        if detail in procedures:
            new_name, procedure = procedures[detail]
            parsed_details[new_name] = procedure(details[detail]) if procedure else details[detail]
            if new_name == detail:
                # If no alias was defined, continue to the next detail.
                continue
        if detail in related_resources:
            # Append '_data' to the key so it doesn't conflict with the field containing the Resource object.
            parsed_details[detail + '_data'] = details[detail]
        else:
            parsed_details[detail] = details[detail]

    return parsed_details


def features_adapter(features):
    """
    Processes track audio features from Spotify API for easier processing.

    Shortens all features ending in '-ness' or '-ability'.
    """

    # Features are intentionally left black on some tracks.
    if not features:
        return features

    feature_names = ['valence', 'energy', 'danceability', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'tempo', 'key', 'mode',
                     'time_signature']

    feature_aliases = {
        'danceability': 'dance',
        'speechiness': 'speech',
        'acousticness': 'acoustic',
        'instrumentalness': 'instrumental',
        'liveness': 'live',
        'time_signature': 'signature'
    }

    parsed_features = {}
    for feature in feature_names:
        key = feature_aliases[feature] if feature in feature_aliases else feature
        if feature not in features:
            pass
        parsed_features[key] = features[feature]

    return parsed_features

def uri_list(uris):
    """
    Returns the parameter enclosed in a list if the parameter was a string.

    Intended for use with some Spotify API endpoints that only accept a list of uris.
    """
    match uris:
        case str():
            return[uris]
        case _:
            return uris


def detect_language(text):
    return langdetect.detect_langs(text)

def language_name(lang_code):
    return Language.get(lang_code).display_name()

def quick_language(track):
    # TODO: Measure accuracy of this against lyrics language analysis
    """Return the best guess at a track's language from names alone."""
    total_text = " ".join([track.name, track.album.name, track.artists[0].name])
    try:
        return langdetect.detect_langs(total_text)[0].lang
    except LangDetectException:
        return None


def show_dict(d):
    for i in d:
        print(f"{i} {'.' * (25 - len(i))} {d[i]}")


# generates a url to get a resource with a specified uri
def uri_to_url(uri):
    fields = uri.split(':')
    if len(fields) == 3:
        return fields[1] + 's/' + fields[2]


def parse_item(item, item_type):
    result = {
        'miniature': get_img_urls(item, item_type)[0] if get_img_urls(item, item_type) else None,
        'name': item['name'],
        'uri': item['uri']
    }
    if 'artists' in item:
        result['artists'] = parse_artists(item['artists'])
    return result


# Takes a list of artists and return a nice, comma separated, string, of their, names
def parse_artists(artists):
    result = ''
    comma = False
    for artist in artists:
        if comma:
            result += ', '
        else:
            comma = True
        result += artist['name']
    return result


# returns a list of image urls for an item sorted according to their resolution
def sort_image_urls(image_urls):
    sorted_urls = sorted(image_urls, key=lambda x: x['height'])  # sort to get the smallest image first
    return [image['url'] for image in sorted_urls]


# Spotify represents song keys with numbers 0-11 starting with C, the key is minor when mode = 0 and major when mode = 1
def track_key(key, mode):
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return keys[key] + ('m' if not mode else '')

# TODO: This name is misleading
# Removes podcast episodes and local tracks
def filter_false_tracks(items):
    """Filter out local tracks and items with no 'track' (they're usually podcast episodes)"""
    result = []
    for item in items:
        # Check if the item contains a track. Sometimes a response contains empty husks of items without a track inside.
        if 'track' in item and item['track']:
            # Item is track context.
            track = item['track']
        elif 'type' in item and item['type'] == 'track':
            # Item is track.
            track = item
        else:
            continue
        # Check if track is local.
        if not track['is_local'] and ':local:' not in track['uri']:
            result.append(track)
    return result


def remove_duplicates(items, compare: List = None, sanitize_names=True, show=False):
    """
    Returns a list where only the first track of the same name is kept.

    If the compare list is given, items with names in the compare list will be rejected as well.
    """
    # TODO: Naming suggests this changes the original list when in fact it returns a new one
    # TODO: The result is completely up to the sorting of the list, introduce option to keep the 'purest' name
    unique_items = []
    unique_names = {}

    # Populate the sets of unique names with entries from the compare list.
    if compare:
        for item in compare:
            name = uniform_title(item.name).lower() if sanitize_names else item.name.lower()
            for artist in item.artists:
                if artist.name not in unique_names:
                    unique_names[artist.name] = set()
                unique_names[artist.name].add(name)

    for item in items:
        name = uniform_title(item.name).lower() if sanitize_names else item.name.lower()
        unique = True
        # Reject the item if any of the featuring artists already has an item of that title
        for artist in item.artists:
            if artist.name not in unique_names:
                unique_names[artist.name] = set()
            elif name in unique_names[artist.name]:
                unique = False
                if show:
                    print(f"Rejecting {item.name}")
                break
            unique_names[artist.name].add(name)
        if unique:
            unique_items.append(item)
    return unique_items


def uniform_title(title):
    """Does the best it can to get the actual song title from whatever the name of the track is
    Track names on Spotify are riddled with information on remixes, remasters, features, live versions etc.
    This function tries to remove these, but it might not work in every case, especially in languages other
    than English since it works by looking for keywords
    """
    keywords = ['remaster', 'delux', 'demo', 'mix', 'version', 'edit', 'live', 'track', 'session', 'extend', 'feat',
                'studio', 'instrumental', 'mono', 'take']
    # TODO: Right now it's impossible to remove anything with 'mix', but keep 'remix'

    if not any(keyword in title.lower() for keyword in keywords):
        return title
    # TODO: Look for ways to break this
    #  uses split to remove - everything after hyphen if there's a keyword there
    #  (doesn't separate ones without spaces since some titles are like-this)


    # Removes everything in parentheses if there's a keyword inside.
    if any(symbol in title for symbol in ['(', ')', '[', ']']):
        for r in ["\(.*?\)", "\[.*?\]"]:
            regex = re.compile(r)
            results = re.findall(regex, title)
            if len(results) > 0:
                for result in results:
                    if any(keyword in result.lower() for keyword in keywords):
                        title = title.replace(result, '')

    if ' - ' in title:
        segments = title.split(" - ")
        title = ''
        for segment in segments:
            if any(keyword in segment.lower() for keyword in keywords):
                continue
            title = title + segment + ' - '
        title = title[:-3]

    title = title.strip()
    return title
