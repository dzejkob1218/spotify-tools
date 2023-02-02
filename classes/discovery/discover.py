import time
import classes.spotify as spotify
import helpers
from classes.spotify_session import SpotifySession


class Source:
    """
    Wrapper for any actor object in the discovery algorithm, like artist or album.

    Valid types of resource are classes that inherit both spotify.Resource and spotify.Collection.
    """

    def __init__(self, resource: spotify.Collection, quick):
        # `quick` means the artist will have less than 10 tracks and it's not needed to load everything.
        # TODO: In the future this will probably be replaced by an entire dictionary of rules and variables.
        self.quick = quick
        self.resource = resource
        self.source_tracks = []  # All tracks from this source present in the source collection.
        self.total_tracks = None  # In quick mode is summed up from albums' 'total_tracks' attribute.
        self.undiscovered_tracks = None  # Unique tracks that aren't in the source collection.
        self.exploitation = None  # Fraction of this resource's material already present in the source collection.
        self.source_share = None  # Fraction of the original collection contributed by this resource.
        # Copy over the resource's attributes to skip unnecessary calls to resource.
        self.__dict__.update(self.resource.__dict__)

    def __eq__(self, other):
        """Allow comparing to uri strings and resource objects to simplify code."""
        match other:
            case str():
                return other == self.uri
            case spotify.Artist() | spotify.Album():
                return self.resource == other
            case _:
                return other is self

    def calculate_exploitation(self):
        self.exploitation = len(self.source_tracks) / self.total_tracks
        # Uniqueness must be decided by the same rules, so the exploitation quotient must be between 0 and 1.
        if self.exploitation > 1 or self.exploitation < 0:
            raise Exception(f"Discovery exploitation quotient is not a valid fraction: {self.exploitation}.")
        return self.exploitation

    def calculate_source_share(self, source_length):
        self.source_share = len(self.source_tracks) / source_length
        return self.source_share


class Artist(Source):
    def __init__(self, resource, quick):
        super().__init__(resource, quick)
        self.result_share = None  # Tracks this artist will contribute to the resulting collection.

    def load_undiscovered_tracks(self, source_tracks):
        """If quick mode is on and less than 10 tracks are needed, load top tracks."""
        if self.quick and round(self.result_share) <= 10:
            # In quick mode, estimate total tracks using metadata and get top 10 tracks.
            self.total_tracks = self.resource.count_tracks()
            unique_top_tracks = self.resource.get_top_tracks(remove_duplicates=True)
            undiscovered_top_tracks = helpers.remove_duplicates(unique_top_tracks, source_tracks)
            # Use top tracks as source if it's sufficient
            if len(undiscovered_top_tracks) >= self.result_share:
                print(f"{self.name} using top 10.")
                self.undiscovered_tracks = undiscovered_top_tracks
                return self.undiscovered_tracks
        # If quick mode was off or more tracks are contributed than are available in top tracks, load everything.
        self.quick = False
        unique_tracks = self.resource.get_complete_tracks(remove_duplicates=True)
        # Remember the original length to calculate exploitation.
        self.total_tracks = len(unique_tracks)
        self.undiscovered_tracks = helpers.remove_duplicates(unique_tracks, source_tracks)
        return self.undiscovered_tracks

    def set_discovery_priority(self, albums):
        """
        Arrange undiscovered tracks in discovery priority.

        The order is decided by track sorting rules and album priority.
        By default tracks are sorted by popularity and albums gain priority only by their shares and exploitation.
        """

        # TODO: Expand this method to accept custom track and album sorting rules.
        def album_priority(track):
            return next((album.priority for album in albums if track.album == album), 1)

        def track_priority(track):
            return track.popularity

        sorting_key = lambda track: track_priority(track) * album_priority(track)
        self.undiscovered_tracks = sorted(self.undiscovered_tracks, key=sorting_key, reverse=True)

    def calculate_result_share(self, result_size):
        """
        Approximates the share of the result for this artist when the source share is calculated.

        This is significant in quick mode, and is used to check if the entire artist resource should be loaded.
        """
        self.result_share = self.source_share * result_size
        return self.result_share

    def calculate_final_share(self, result_size, average_exploitation, exploitation_bonus_modifier):
        """
        Calculates how many songs the artist will contribute to the resulting collection.
        """
        exploitation_quotient = (self.exploitation / average_exploitation)  # * exploitation_bonus_modifier
        exploitation_bonus = (exploitation_quotient - 1) * exploitation_bonus_modifier
        self.result_share = round(self.source_share * result_size * (1 + exploitation_bonus))
        return self.result_share


class Album(Source):
    def __init__(self, resource, quick):
        super().__init__(resource, quick)
        self.priority = 1

    def calculate_priority(self, average_share, average_exploitation, share_bonus_modifier):
        # TODO: Add priority rules such as similarity in release time and features to exploited records.
        """
        Calculates album priority based on source shares, exploitation and discovery configuration.

        Priority is calculated by the following steps:
        - Any share of source increases priority, how much depends on average album shares in the source collection.
        - Exploitation of the album as compared to the average further modifies the priority.
        - Additional discovery rules can influence the album priority.
        """
        # TODO: Check is the exploitation multiplier doesn't get too crazy
        # Alternative
        # extra_priority = share_bonus_modifier * (self.source_share/average_share) * (self.exploitation/average_exploitation)
        extra_priority = ((share_bonus_modifier * (self.source_share / average_share)) + (
                share_bonus_modifier * (self.exploitation / average_exploitation))) / 2
        self.priority = 1 + extra_priority

    def load_tracks(self):
        """Load all tracks calculate collection length."""
        # TODO: Albums only load tracks to precisely calculate length, which is pretty overkill even with quick mode off, make it a separate option
        if self.quick:
            # In quick mode estimate number of tracks from metadata.
            self.total_tracks = self.resource.count_tracks()
        else:
            self.total_tracks = len(self.resource.get_complete_tracks(remove_duplicates=True))


class Discover:
    """Extends a source collection with related tracks."""

    def __init__(self, sp, quick=False):
        self.quick = quick
        self.sp: SpotifySession = sp
        self.album_share_bonus_modifier = 0.1  # How much tracks benefit from being in an album with many shares.
        self.artist_exploitation_bonus_modifier = 0.1  # How much high exploitation benefits an artist's share of the result.
        # TODO: Add a variable that buffs smaller artists

    # For now only support playlist for simplicity
    def extend(self, result_size, source: spotify.Playlist):
        # TODO: Would it be better to make these dicts for faster indexing?
        artists = []
        albums = []
        # TODO: Duplicates have to be removed from the source at some point, for now it's at the start for simplicity.
        source_tracks = source.get_complete_tracks(remove_duplicates=True)
        # Count occurrences of each artist and album in source collection.
        for track in source_tracks:
            album_source = next((x for x in albums if x == track.album), None)
            if not album_source:
                albums.append(album_source := Album(track.album, self.quick))
            album_source.source_tracks.append(track)
            for artist in track.artists:
                # TODO: Rules about sharing a collaboration
                artist_source = next((x for x in artists if x == artist), None)
                if not artist_source:
                    artists.append(artist_source := Artist(artist, self.quick))
                artist_source.source_tracks.append(track)
        print(f"There are {len(artists)} artists and {len(albums)} albums in {source.name}")

        # Load all unique tracks from the featuring artists and calculate variables.
        source_length = len(source_tracks)
        average_album_exploitation = 0
        average_album_share = 0
        times = time.time()
        i = 0
        for album in albums:
            i += 1
            album.load_tracks()
            average_album_share += album.calculate_source_share(source_length)
            average_album_exploitation += album.calculate_exploitation()
            print(
                f"{i:3}  {helpers.uniform_title(album.name):30} Share: {round(album.source_share * 100, 2):2}%, Exploitation: {round(album.exploitation * 100, 2):2}% - {album.name}")
        average_album_exploitation /= len(albums)
        average_album_share /= len(albums)
        print(f"Average album exploitation: {round(average_album_exploitation * 100, 2)}%")
        print(f"Average album share: {round(average_album_share * 100, 2)}%")
        for album in albums:
            album.calculate_priority(average_album_share, average_album_exploitation, self.album_share_bonus_modifier)
        print(f"{round(time.time() - times, 2)}s to load albums.\n")

        # Do the same for artists. This shouldn't take long since all tracks should've been loaded in the previous step.
        average_artist_exploitation = 0
        times = time.time()
        i = 0
        for artist in artists:
            i += 1
            artist.calculate_source_share(source_length)
            artist.calculate_result_share(result_size)
            artist.load_undiscovered_tracks(source_tracks)
            artist.set_discovery_priority(albums)
            average_artist_exploitation += artist.calculate_exploitation()
            print(
                f"{i:3} - {artist.name} - Share: {round(artist.source_share * 100, 2)}%, Exploitation: {round(artist.exploitation * 100, 2)}%, Result: {artist.result_share}")
        average_artist_exploitation /= len(artists)
        print(f"Average artist exploitation: {round(average_artist_exploitation * 100, 2)}%")
        print(f"{round(time.time() - times, 2)}s to load artists.\n")

        result = []
        for artist in artists:
            artist.calculate_final_share(result_size, average_artist_exploitation,
                                         self.artist_exploitation_bonus_modifier)
            result.extend(artist.undiscovered_tracks[:artist.result_share])
            print(f"{artist.result_share:4} out of {len(artist.undiscovered_tracks):4} - {artist.name}")

        # TODO: Do something to make result size match the setting
        total_tracks = len(result)
        print(total_tracks)

        # TODO: Add sorting options for the results, including default to reflect the hierarchy
        # self.sp.create_playlist(name=f"{source.name} Discovery", tracks=result)
