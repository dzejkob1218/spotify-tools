from typing import List, Dict
import classes.spotify as spotify
import helpers

"""
Module for functions that should go somewhere else eventually
"""


class Parser:

    resources = {}

    def __init__(self, sp):
        self.sp = sp

    def get_resource(self, raw_data: Dict):
        """Return an existing resource by uri or create a new one."""
        uri = raw_data['uri']

        # TODO: In some cases the incoming raw_data can contain new information which currently would be ignored

        if uri in self.resources:
            return self.resources[uri]

        resource = self.parse_resource(raw_data)
        self.resources[uri] = resource
        return resource

    def parse_resource(self, raw_data: Dict):
        """This should be the only method through which instances of Resource are initialized."""
        if "type" in raw_data and raw_data["type"] == "playlist":
            # Parse track data that may be included with the playlist data
            # TODO: This assumes that 'items' is always present in response objects of type 'playlist', make sure this is true
            children_data = raw_data["tracks"].pop("items", None)
            children = (
                [self.get_resource(child["track"]) for child in children_data]
                if children_data
                else None
            )
            return spotify.Playlist(self.sp, raw_data=raw_data, children=children)

        if "type" in raw_data and raw_data["type"] == "user":
            return spotify.User(self.sp, raw_data=raw_data)

        if "type" in raw_data and raw_data["type"] == "album":
            artists = [self.get_resource(artist) for artist in raw_data['artists']]
            return spotify.Album(self.sp, raw_data, artists)

        if "type" in raw_data and raw_data["type"] == "artist":
            return spotify.Artist(self.sp, raw_data=raw_data)

        elif "type" in raw_data and raw_data["type"] == "track" or "track" in raw_data:
            # TODO: Album and artist data acquired through track is not complete. Making two more requests for each track tanks the performance.
            album = self.get_resource(raw_data['album'])
            artists = [self.get_resource(artist) for artist in raw_data['artists']]
            track = spotify.Track(self.sp, raw_data, artists=artists, album=album)
            # TODO: Does adding incomplete tracks to an album help anything right now?
            album.children.append(track)
            return track

        else:
            raise Exception("Parser didn't recognize object")
