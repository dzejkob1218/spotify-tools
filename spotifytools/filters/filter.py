from typing import List
import spotifytools.spotify as spotify

"""
A filter is applied to a collection to change the output of tracks

Filters have:
- Name
- Category
- Description
- Polarity (addition or subtraction)
- Help text
- Code that modifies output
- Reverse mode (plus help text)
- Options (plus help text)

"""


class Filter:
    def filter_collection(self, items: List[spotify.Object]):
        pass
