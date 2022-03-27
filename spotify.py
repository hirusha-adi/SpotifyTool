import json
import os

import requests
from youtubesearchpython import VideosSearch


class Playlist:
    def __init__(self, musicListFile: str = None):
        self.musicListFile = musicListFile

        self.musicListData = None
        self.customMusicList = None
        self._spotifyToken = None

    def loadSpotifyToken(self, fileName: str = "token.txt"):
        with open("token.txt", "r", encoding="utf-8") as file:
            self._spotifyToken = file.read()
            if not(self._spotifyToken.startswith("Bearer ")):
                self._spotifyToken = "Bearer " + self._spotifyToken

    def setListFile(self, musicListFile):
        self.musicListFile = musicListFile

    def _loadList(self):
        with open(self.musicListFile, "r", encoding="utf-8") as file:
            self.musicListData = json.load(file)

    def _getSpotifyID(self, url: str):
        return url.split("/")[-1]

    def showInfoList(self):
        if self.musicListData is None:
            self._loadList()

        count = 1
        for item in self.musicListData["items"]:
            track = item["track"]
            print(f"""
{count} - {track["name"]}
    Song Info -
        Name: {track["href"]}
        URL: {track["name"]}
        Spotify ID: {self._getSpotifyID(url=track["href"])}
    Album Info -
        Name: {track["album"]["name"]}
        URL: {track["album"]["href"]}
        """)
            count += 1

    def getYouTubeLink(self, name: str):
        search = VideosSearch(name + " song", limit=1)
        x = search.result()
        return x['result'][0]['link']

    def makeCustomMusicList(self):
        if self.musicListData is None:
            self._loadList()

        if self.customMusicList is None:
            self.customMusicList = {}

        count = 1
        items = []
        for item in self.musicListData["items"]:
            track = item["track"]
            items.append(
                {
                    "id": count,
                    "name": track["name"],
                    "url": track["href"],
                    "spotify_id": self._getSpotifyID(url=track["href"]),
                }
            )
            break
            count += 1
        self.customMusicList["items"] = items

    def saveCustomMusicList(self, filename: str = "Custom-1.json"):
        if not(filename.lower().endswith(".json")):
            filename += ".json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.customMusicList, file,
                      ensure_ascii=False,
                      indent=4)

    def makeFinalMusicList(self):
        if self.musicListData is None:
            self._loadList()

        if self.customMusicList is None:
            self.makeCustomMusicList()

        folder_name = os.path.join(os.getcwd(), "musicdata")
        os.chdir(folder_name)
        for item in self.customMusicList["items"]:
            id = item["id"]
            name = item["name"]

            with open(str(id) + ".json", "r", encoding="utf-8") as f1:
                data = json.load(f1)

            item["artist"] = {
                "name": data["artists"][0]["name"],
                "spotify": data["artists"][0]["external_urls"]["spotify"]
            }

            item["adjusted_name"] = f'{data["artists"][0]["name"]} - {name}'

            item["yt_link"] = self.getYouTubeLink(name=item["adjusted_name"])

            print(data)
            item["art"] = data["images"]

        os.chdir("..")

        self.saveCustomMusicList("Custom-2.json")

    def getListLenght(self):
        if self.musicListData is None:
            self._loadList()

        return len(self.musicListData["items"])

    def showLenght(self):
        print(self.getListLenght())

    def getSongInfoFromSpotifyAPI(self, spotifyID: str):
        headers = {
            "Content-Type": "application/json",
            "Authorization": self._spotifyToken
        }
        r = requests.get(
            url=f"https://api.spotify.com/v1/tracks/{spotifyID}?market=US", headers=headers)
        data = r.json()
        return data

    def getEverySongInfo(self):
        if not(isinstance(self.customMusicList, dict)):
            self.makeCustomMusicList()

        folder_name = os.path.join(os.getcwd(), "musicdata")

        if not(os.path.exists(folder_name)):
            os.makedirs(folder_name)

        if not(os.listdir(folder_name) == self.getListLenght()):
            os.chdir(folder_name)
            for item in self.customMusicList["items"]:
                spotify_id = item["spotify_id"]
                with open(str(item["id"]) + ".json", "w", encoding="utf-8") as file:
                    json.dump(
                        self.getSongInfoFromSpotifyAPI(spotifyID=spotify_id),
                        file,
                        ensure_ascii=False,
                        indent=4)
            os.chdir("..")

    def downloadMusic(self):
        try:
            temp = self.customMusicList["items"][0]["yt_link"]
        except KeyError:
            self.makeFinalMusicList()

        folder_name = os.path.join(os.getcwd(), "music")

        if not(os.path.exists(folder_name)):
            os.makedirs(folder_name)

        if not(os.listdir(folder_name) == self.getListLenght()):
            os.chdir(folder_name)
            for item in self.customMusicList["items"]:
                os.system(
                    f"youtube-dl -x --audio-format mp3 {item['yt_link']}")
            os.chdir("..")

    def run(self,
            musicListFile: str = None,
            spotifyToken: str = None,
            spotifyTokenFileName: str = None
            ):

        if spotifyToken:
            self._spotifyToken = spotifyToken
            if not(self._spotifyToken.startswith("Bearer ")):
                self._spotifyToken = "Bearer " + self._spotifyToken
        else:
            if spotifyTokenFileName:
                self.loadSpotifyToken(fileName=spotifyTokenFileName)

        self.setListFile(musicListFile=musicListFile)

        self.getEverySongInfo()
        self.downloadMusic()


if __name__ == "__main__":
    obj = Playlist()
    obj.setListFile("album.json")
    obj.loadSpotifyToken("token.txt")
    obj.getEverySongInfo()
    obj.downloadMusic()
