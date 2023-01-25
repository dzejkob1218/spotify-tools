import classes.spotify as spotify
from classes.spotify.track import Track as Track
from helpers.parser import filter_false_tracks, sort_image_urls


# TODO: Data about when a track was added to a playlist is being lost right now
class Playlist(spotify.Resource, spotify.Collection):
    child_type = Track

    # Viable children types: Track
    def __init__(self, sp, raw_data, children=None):
        # Resource init
        spotify.Resource.__init__(self, sp, raw_data)
        # Collection init
        spotify.Collection.__init__(self, sp, children)

        self.children_loaded = len(self.children) == self.total
        self.user_is_owner = self.owner == sp.fetch_user().uri

    def load_details(self, raw_data):
        # Get a list of image urls sorted by size
        image_urls = (
            sort_image_urls(raw_data["images"]) if "images" in raw_data else None
        )

        # Write object attributes
        self.attributes = {
            "uri": raw_data["uri"],
            "name": raw_data["name"],
            "miniature": image_urls[0] if image_urls else None,
            "image": image_urls[-1] if image_urls else None,
            "followers": raw_data["followers"]["total"]
            if "followers" in raw_data
            else 0,
            "owner": raw_data["owner"]["uri"],
            "owner_name": raw_data["owner"]["display_name"],
            "public": raw_data["public"],
            "total": raw_data["tracks"]["total"],
            "description": raw_data["description"],
        }

    def load_children(self):
        total_tracks = self.attributes["total"]
        total_tracks_downloaded = len(self.children)
        # TODO: Generalize this check and move up to Collection class
        if total_tracks_downloaded >= total_tracks:
            raise Exception("Load children called on loaded collection")
        # TODO: Test this
        # Request all remaining tracks
        self.children.extend(
            self.sp.fetch_playlist_tracks(
                self.uri, total_tracks, start=total_tracks_downloaded
            )
        )
        self.children_loaded = True
        return self.children

    """
    Legacy code:
        # TODO: Is this the best time to download track features?
        track_features = self.sp.fetch_track_features([item['uri'] for item in all_tracks])
        # Some requests for track features return None - count only the valid results for use in calculations
        features_count = sum(x is not None for x in track_features)

        # Saves all tracks and their audio features into a list of children objects
        for i in range(len(all_tracks)):
            self.children.append(
                Track(all_tracks[i]['uri'], self.sp, raw_object=all_tracks[i], audio_features=track_features[i]))

        # Count up attributes of included songs which can be nicely averaged out and presented
        # TODO : Add a functionality for presenting attributes which can't be just averaged (date, key, signature, most popular artist etc.)
        summable_child_attributes = {'signature', 'release_year', 'tempo', 'popularity', 'duration', 'valence', 'dance',
                                     'speech', 'acoustic', 'instrumental', 'live', 'number', 'energy', 'explicit',
                                     'mode'}

        self.average_children_details(summable_child_attributes, features_count)


    def get_track_features(self):
        " Returns a list of track attributes that successfully loaded their features and can be filtered and sorted "
        loaded, unloaded = [], []
        for track in self.children:
            loaded.append(track.attributes) if track.audio_features else unloaded.append(track.attributes)
        return loaded, unloaded
    """
