# spotify-tools
Python library for easy managing of Spotify resources with a built-in command line interface. 

# Authentication
Valid Spotify Developer credentials are required to run this module.

These credentials must all be set as environment variables or pasted as an `.env` file in the working directory:
`SPOTIPY_REDIRECT_URI`, `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`

The redirect must also be whitelisted in the Spotify Developer Dashboard.

To get lyrics from Genius you'll also need to set the following API credentials:
`GENIUS_ID`, `GENIUS_SECRET`, `GENIUS_TOKEN`

# Usage
 
```
load_dotenv()
spotify_session = SpotifySession()
genius_session = GeniusSession()
```


# Connecting
You have to log in with Spotify to access and manipulate your library, change playback etc. 

This module uses [spotipy](https://github.com/spotipy-dev/spotipy) to handle authorization.

Calling `SpotifySession.authorize()` will open Spotify login in the browser.

Upon success, it will redirect to the specified URL with the authorization code, which by default is cached in the root directory.

```
spotify_session = SpotifySession()
spotify_session.authorize()
spotify_session.fetch_currently_playing() 
```



# CLI
Running the module as main will launch the command-line interface which lets you navigate and manipulate Spotify resources.

-- example output --

The CLI is not fully implemented yet and more features are coming soon.

Type `help` or just `h` at any point to bring up help text describing available options.