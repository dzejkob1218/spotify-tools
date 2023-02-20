import random
import time
import classes.spotify as spotify
import helpers
from classes.spotify_session import SpotifySession
from .album import Album
from .artist import Artist

class Discover:
    """Extends a source collection with related tracks."""
    # TODO: Check local market available before adding tracks
    def __init__(self, sp, quick=False):
        # TODO: Add an option to completely block related artists and only use related artists
        # 0 spillover means that related artists will be reached only when tracks run out
        self.spillover = 0.35
        self.quick = quick
        self.sp: SpotifySession = sp
        self.album_share_bonus_modifier = 0.1  # How much tracks benefit from being in an album with many shares.
        self.artist_exploitation_bonus_modifier = 0.1  # How much high exploitation benefits an artist's share of the result.
        # TODO: Add a variable that buffs smaller artists

    # For now only support playlist for simplicity
    def extend(self, source: spotify.Playlist, result_size):
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
                    artist_source = Artist(artist, self.quick)
                    artists.append(artist_source)
                artist_source.source_tracks.append(track)
        print(f"There are {len(artists)} artists and {len(albums)} albums in {source.name}")

        # Load all unique tracks from the featuring artists and calculate variables.
        source_size = len(source_tracks)
        average_album_exploitation = 0
        average_album_share = 0
        times = time.time()
        i = 0
        for album in albums:
            i += 1
            album.load_tracks()
            average_album_share += album.calculate_source_share(source_size)
            average_album_exploitation += album.calculate_exploitation()
        for album in sorted(albums, key = lambda a: a.source_share, reverse = True):
            print(
                f"{i:3}  {helpers.uniform_title(album.name)[:30]:30} Share: {round(album.source_share * 100, 2):2}%, Exploitation: {round(album.exploitation * 100, 2):2}%")
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
            print(f"{i:5} ({round(100 * i/len(artists))}%) - {len(artist.source_tracks):5} track{'s' if len(artist.source_tracks) == 1 else ' '} - {artist.name}")
            # Calculate how much of the share an artist has.
            artist.calculate_source_share(source_size)
            if self.quick and artist.estimate_result_share(result_size) > 10:
                artist.quick = False

            # Load only top 10 tracks if quick mode is on and it seems to be sufficient.
            if artist.quick:
                artist.load_top_tracks()
                # TODO: This could be skipped to speed up discovery, hence a separate function
                artist.estimate_total_tracks()

            # Load all tracks if quick mode is off or top 10 tracks weren't sufficient.
            if not artist.quick:  # This is intentionally not an else
                artist.load_undiscovered_tracks()
                # Sort the tracks in order of priority, according to discovery configuration.
                artist.set_discovery_priority(albums)

            # TODO: Add a configuration options to skip this
            # Exploitation is calculated for each artist
            average_artist_exploitation += artist.calculate_exploitation()



        # Average exploitation is calculated to serve as benchmark for each individual artist
        average_artist_exploitation /= len([artist for artist in artists if artist.total_tracks != 0])

        print(f"Average artist exploitation: {round(average_artist_exploitation * 100, 2)}%")
        print(f"{round(time.time() - times, 2)}s to load artists.\n")

        result = []
        for artist in artists:
            # Once it is known how an artist compares on average, modify the number of shares
            artist.calculate_result_total(result_size, average_artist_exploitation, self.artist_exploitation_bonus_modifier)
            #print(f"{artist.result_share:4} out of {len(artist.undiscovered_tracks):4} - {artist.name}")

        # Sort the artists according to shares they have in the result
        artists = sorted(artists, key=lambda a: a.result_total, reverse=True)
        spillover_artists = []

        i = 0
        # TODO: Right now two artists can contribute all their tracks twice if changing names (Vulfpeck, Osees)
        for artist in artists:
            i += 1

            # See how much of the artist's material will be used for the result
            #artist.calculate_result_exploitation()
            artist.calculate_spillover(self.spillover)

            print(f"{i:3} - ", end="")
            print(f"{artist.name[:25]:25} - ", end="")
            print(f"Source share: {round(artist.source_share * 100, 2):5}%, ", end="")
            print(f"Exploitation: {round(artist.exploitation * 100, 2):5}%, ", end="")
            print(f"End exploitation: {round(artist.calculate_result_exploitation() * 100, 2):5}%, ", end="")
            print(f"Available: {len(artist.undiscovered_tracks):3}, ", end="")
            print(f"Result total: {artist.result_total:3}, ", end="")
            print(f"Bleed: {artist.spillover:3}, ", end="")
            print(f"Contribution: {artist.contribution:3}, ", end="")
            print(f"{'top 10' if artist.top10 else ''}", end="")
            print(f"{[contributor.name + ', ' for contributor in artist.share_contributors]}")

            if artist.spillover:
                new_artists = []
                existing_artists = []
                source_artists = []
                artist_resources = self.sp.fetch_related_artists(artist)
                # Some artists don't have relates
                if artist_resources:
                    for resource in artist_resources:
                        related_artist = next((artist for artist in artists if artist == resource), None)
                        if related_artist:
                            if related_artist.source_tracks and related_artist.result_total < artist.result_total:
                                source_artists.append(related_artist)
                        else:
                            related_artist = next((artist for artist in spillover_artists if artist == resource), None)
                            if related_artist:
                                existing_artists.append(related_artist)
                            else:
                                new_artist = Artist(resource, self.quick)
                                spillover_artists.append(new_artist)
                                new_artists.append(new_artist)

                    artist.related_artists.extend(new_artists)
                    artist.related_artists.extend(existing_artists)
                    artist.related_artists.extend(source_artists)
                    artist.load_related_artists()


        artists.extend([artist for artist in spillover_artists if artist.contribution])

        total_tracks = 0

        for artist in artists:
            total_tracks += artist.contribution

        print(f"TOTAL: {total_tracks}")

        # Distribute the artists randomly while keeping their track order in the result playlist.
        # TODO: Maybe shift the balance somehow to favor popular artists at first
        most_popular = 0  # start with the four most popular artists to get a nice playlist miniature.
        while artists and len(result) < result_size:
            if len(artists) >= 4 and most_popular < 4:
                i = most_popular
                most_popular += 1
            else:
                i = random.randint(0, len(artists) - 1)
            artist = artists[i]
            if not artist.undiscovered_tracks:
                print(f"Artist {artist.name} queued with no tracks and {artist.contribution} contributions.")
            else:
                result.append(artist.undiscovered_tracks.pop(0))
            artist.contribution -= 1
            if artist.contribution <= 0:
                artists.pop(i)



        #for track in result:
        #    print(f"{track.name} - {track.artists[0].name}")



        # TODO: Add sorting options for the results, including default to reflect the hierarchy
        self.sp.create_playlist(name=f"{source.name} Discovery", tracks=result)
