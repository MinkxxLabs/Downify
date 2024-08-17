import os
import sys
import getpass
import threading
import requests
import pytube
import customtkinter as ctk
from customtkinter import filedialog

current_windows_username = getpass.getuser()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x350")
        self.title("Spotify Downloader")
        self.resizable(False, False)
        self.iconbitmap(resource_path("assets\ico_icons\spotify_512px.ico"))
        ctk.set_appearance_mode("dark")

        self.download_path = ctk.StringVar(value=f"C:/Users/{current_windows_username}/Downloads")
        self.output_var = ctk.StringVar()
        self.progress_var = ctk.StringVar(value="0 %")
        self.url_var = ctk.StringVar()

        self.thread_running = False

        self.create_widgets()
        
    def create_widgets(self):
        # Title text
        title_label = ctk.CTkLabel(self, text="Spotify Downloader", fg_color="transparent", font=("Inter", 30))
        title_label.place(x=170, y=20)

        # URL entry
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Enter URL to download", font=("Inter", 12), width=500, textvariable=self.url_var)
        self.url_entry.place(x=50, y=90)

        # Download path entry
        self.dir_path_entry = ctk.CTkEntry(self, placeholder_text="Download path", font=("Inter", 12), width=400, textvariable=self.download_path)
        self.dir_path_entry.place(x=50, y=140)

        # Browse button
        self.dir_browse_btn = ctk.CTkButton(self, text="Browse", command=self.browse_path, width=70)
        self.dir_browse_btn.place(x=480, y=140)

        # Download button
        self.download_btn = ctk.CTkButton(self, text="Download", command=self.download, width=100)
        self.download_btn.place(x=250, y=190)

        # Progress bar
        self.progressbar = ctk.CTkProgressBar(self, width=400)
        self.progressbar.set(0)
        self.progressbar.place(x=70, y=250)

        # Progress label
        self.progress_label = ctk.CTkLabel(self, text="%", fg_color="transparent", font=("Inter", 14), textvariable=self.progress_var)
        self.progress_label.place(x=500, y=238)

        # Output label
        self.output_label = ctk.CTkLabel(self, text="test", fg_color="transparent", font=("Inter", 12), textvariable=self.output_var)
        self.output_label.place(x=50, y=300)

    def browse_path(self):
        download_directory = filedialog.askdirectory(initialdir=self.download_path.get(), title="Select Download Directory")
        self.download_path.set(download_directory)

    def download(self):
        if self.thread_running:
            return
        
        self.thread_running = True
        self.url_entry.configure(state="disabled")
        self.download_btn.configure(state="disabled")

        link = self.url_var.get()
        track_type, track_id = link.split("/")[-2:]

        if track_type == "track":
            self.start_download_track_thread(track_type, track_id)
        elif track_type == "album":
            self.start_download_album_thread(track_type, track_id)
        elif track_type == "playlist":
            self.start_download_playlist_thread(track_type, track_id)

    def reset_ui(self):
        self.progressbar.set(0)
        self.progress_var.set("0 %")
        self.url_var.set("")
        self.url_entry.configure(state="normal")
        self.download_btn.configure(state="normal")
        self.thread_running = False

    def download_track(self, track_type, track_id):
        try:
            res = requests.get(f"https://spotipy-api.vercel.app/spotipy?type={track_type}&id={track_id}")
            data = res.json()

            name = data["track_name"]
            artists = data["artists"]

            self.output_var.set(f"Downloading : {name} {artists}")
            
            query = pytube.Search(f"{name} {artists}")
            yt = query.results[0]
            yt.register_on_progress_callback(self.on_progress)

            audio_streams = self.get_audio_streams(yt.streams)
            abr = ["160kbps", "128kbps", "70kbps", "50kbps", "48kbps"]

            for quality in abr:
                if quality in audio_streams:
                    try:
                        stream = audio_streams[quality][0]
                        stream.download(output_path=self.download_path.get())
                        break
                    except Exception as e:
                        print(e)
                        continue
            self.output_var.set(f"Downloaded : {name} {artists}")
            self.output_var.set(f"")

        except Exception as e:
            print(f"Error downloading track: {e}")
            self.output_var.set("Error downloading track")

        finally:
            self.reset_ui()

    def start_download_track_thread(self, track_type, track_id):
        track_thread = threading.Thread(target=self.download_track, args=(track_type, track_id))
        track_thread.start()

    def download_album(self, track_type, track_id):
        try:
            res = requests.get(f"https://spotipy-api.vercel.app/spotipy?type={track_type}&id={track_id}")
            data = res.json()

            album_name = data["album_name"]
            tracks = data["tracks"]
            total_tracks = len(tracks)
            count = 1

            for track in tracks:
                query = pytube.Search(f"{track['track_name']} {track['artists']}")
                self.output_var.set(f"Downloading : ({count}/{total_tracks}) {track['track_name']} {track['artists']}")

                yt = query.results[0]
                yt.register_on_progress_callback(self.on_progress)

                audio_streams = self.get_audio_streams(yt.streams)
                abr = ["160kbps", "128kbps", "70kbps", "50kbps", "48kbps"]

                for quality in abr:
                    if quality in audio_streams:
                        try:
                            stream = audio_streams[quality][0]
                            stream.download(output_path=os.path.join(self.download_path.get(), album_name))
                            break
                        except Exception as e:
                            print(e)
                            continue
                count += 1
                self.progressbar.set(0)
                self.progress_var.set("0 %")
                self.output_var.set(f"Downloaded : {track['track_name']} {track['artists']}")
            self.output_var.set("")

        except Exception as e:
            print(f"Error downloading album: {e}")
            self.output_var.set("Error downloading album")

        finally:
            self.reset_ui()

    def start_download_album_thread(self, track_type, track_id):
        album_thread = threading.Thread(target=self.download_album, args=(track_type, track_id))
        album_thread.start()

    def download_playlist(self, track_type, track_id):
        try:
            res = requests.get(f"https://spotipy-api.vercel.app/spotipy?type={track_type}&id={track_id}")
            data = res.json()
            playlist_owner = data["owner"]
            playlist_name = data["playlist_name"]
            tracks = data["tracks"]
            total_tracks = len(tracks)
            count = 1

            for track in tracks:
                query = pytube.Search(f"{track['track_name']} {track['artists']}")
                self.output_var.set(f"Downloading : ({count}/{total_tracks}) {track['track_name']} {track['artists']}")

                yt = query.results[0]
                yt.register_on_progress_callback(self.on_progress)

                audio_streams = self.get_audio_streams(yt.streams)
                abr = ["160kbps", "128kbps", "70kbps", "50kbps", "48kbps"]

                for quality in abr:
                    if quality in audio_streams:
                        try:
                            stream = audio_streams[quality][0]
                            stream.download(output_path=os.path.join(self.download_path.get(), f"{playlist_name} - {playlist_owner}"))
                            break
                        except Exception as e:
                            print(e)
                            continue
                count += 1
                self.progressbar.set(0)
                self.progress_var.set("0 %")
                self.output_var.set(f"Downloaded : {track['track_name']} {track['artists']}")
            self.output_var.set("")

        except Exception as e:
            print(f"Error downloading playlist: {e}")
            self.output_var.set("Error downloading playlist")

        finally:
            self.reset_ui()

    def start_download_playlist_thread(self, track_type, track_id):
        playlist_thread = threading.Thread(target=self.download_playlist, args=(track_type, track_id))
        playlist_thread.start()

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        completed = (bytes_downloaded / total_size) * 100
        self.progress_var.set(f"{int(completed)} %")
        self.progressbar.set(float(completed) / 100)
        self.progressbar.update()

    def get_audio_streams(self, streams):
        data = {}
        abr = ["160kbps", "128kbps", "70kbps", "50kbps", "48kbps"]
        for q in abr:
            for i in streams:
                if i.abr == q:
                    if q in data:
                        data[q].append(i)
                    else:
                        data[q] = [i]
        return data

if __name__ == "__main__":
    app = App()
    app.mainloop()
