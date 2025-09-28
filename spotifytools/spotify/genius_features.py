class GeniusFeatures:
    """Contains genius.com metadata and lyrics if available """
    annotation_count: int  # The number of annotations on the track.
    api_path: str  # The API path of the track.
    apple_music_id: str  # The Apple Music ID of the track.
    apple_music_player_url: str  # The Apple Music player URL of the track.
    artist_names: str  # The names of the artists associated with the track.
    description: dict  # The description of the track.
    embed_content: str  # The embedded content of the track.
    featured_video: bool  # True if the track has a featured video.
    full_title: str  # The full title of the track.
    header_image_thumbnail_url: str  # The thumbnail URL of the header image of the track.
    header_image_url: str  # The URL of the header image of the track.
    id: int  # The ID of the track.
    language: str  # The language of the track.
    lyrics_owner_id: int  # The ID of the lyrics owner of the track.
    lyrics_placeholder_reason: None  # The reason for the lyrics placeholder (None if not applicable).
    lyrics_state: str  # The state of the lyrics of the track.
    path: str  # The path of the track.
    pyongs_count: int  # The number of pyongs (votes) on the track.
    recording_location: str  # The recording location of the track.
    relationships_index_url: str  # The URL of the relationships index of the track.
    release_date: str  # The release date of the track.
    release_date_for_display: str  # The release date of the track for display.
    release_date_with_abbreviated_month_for_display: str  # The release date of the track with abbreviated month for display.
    song_art_image_thumbnail_url: str  # The thumbnail URL of the song art image of the track.
    song_art_image_url: str  # The URL of the song art image of the track.
    stats: dict  # Genius-specific stats of the track.
    title: str  # The title of the track.
    title_with_featured: str  # The title of the track with featured artists.
    url: str  # The URL of the track.
    current_user_metadata: dict  # The metadata of the current user for the track.
    album: dict  # The album associated with the track.
    custom_performances: list  # The custom performances of the track.
    description_annotation: dict  # The annotation of the description of the track.
    featured_artists: list  # The featured artists on the track.
    lyrics_marked_complete_by: None  # The user who marked the lyrics as complete (None if not applicable).
    lyrics_marked_staff_approved_by: None  # The user who marked the lyrics as staff-approved (None if not applicable).
    media: list  # Links to media provider platforms where the song can be accessed.
    primary_artist: dict  # The primary artist of the track.
    producer_artists: list  # The producer artists of the track.
    song_relationships: list  # The relationships of the track with other songs.
    translation_songs: list  # The translation songs of the track.
    verified_annotations_by: list  # The verified annotations by users on the track.
    verified_contributors: list  # The verified contributors on the track.
    verified_lyrics_by: list  # The verified lyrics by users on the track.
    writer_artists: list  # The writer artists of the track.

    def __init__(self, data: dict):
        self.__dict__.update(data)