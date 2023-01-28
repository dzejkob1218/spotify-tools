from typing import List, Dict
import classes.spotify as spotify
import langdetect
"""
Module for functions that should go somewhere else eventually
"""

def detect_language(text):
    return langdetect.detect_langs(text)

def show_dict(d):
    for i in d:
        print(f"{i} {'.' * (25 - len(i))} {d[i]}")


def parse_resource(sp, raw_data: Dict):
    if "type" in raw_data and raw_data["type"] == "playlist":
        # Parse track data that may be included with the playlist data
        # TODO: This assumes that 'items' is always present in response objects of type 'playlist', make sure this is true
        children_data = raw_data["tracks"].pop("items", None)
        children = (
            [parse_resource(sp, child["track"]) for child in children_data]
            if children_data
            else None
        )
        return spotify.Playlist(sp, raw_data=raw_data, children=children)
    if "type" in raw_data and raw_data["type"] == "user":
        return spotify.User(sp, raw_data=raw_data)
    elif "type" in raw_data and raw_data["type"] == "track" or "track" in raw_data:
        return spotify.Track(sp, raw_data=raw_data)
    else:
        raise Exception("Parser didn't recognize object")
