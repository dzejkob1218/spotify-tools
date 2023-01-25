import re

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


# Removes podcast episodes and local tracks
def filter_false_tracks(items):
    result = []
    for item in items:
        # Filter out local tracks and items with no 'track' (they're usually podcast episodes)
        if not item['is_local'] and 'track' in item:
            result.append(item['track'])
    return result


def uniform_title(title):
    """Does the best it can to get the actual song title from whatever the name of the track is
    Track names on Spotify are riddled with information on remixes, remasters, features, live versions etc.
    This function tries to remove these, but it might not work in every case, especially in languages other
    than English since it works by looking for keywords
    """
    keywords = ['remaster', 'delux', 'from', 'mix', 'version', 'edit', 'live', 'track', 'session', 'extend', 'feat',
                'studio']
    if not any(keyword in title.lower() for keyword in keywords):
        return title

    newtitle = title
    #  uses split to remove - everything after hyphen if there's a keyword there
    #  (doesn't separate ones without spaces since some titles are like-this)
    if ' - ' in newtitle:
        newtitle = newtitle.split(" - ", 1)
        if any(keyword in newtitle[1].lower() for keyword in keywords):
            newtitle = newtitle[0]

    # removes everything in parentheses if there's a keyword inside
    if '(' in newtitle:
        regex = re.compile(".*?\((.*?)\)")
        result = re.findall(regex, title)
        if len(result) > 0:
            if any(keyword in result[0].lower() for keyword in keywords):
                tag = '(' + result[0] + ')'
                newtitle = newtitle.replace(tag, '')

    newtitle = newtitle.strip()
    return newtitle
