import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys
import ctypes
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import time
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import subprocess
import winreg
from PIL import Image, ImageTk
import logging
from mutagen import File
from mutagen.wave import WAVE
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioPlayer:
    def __init__(self):
        self.current_song = None
        self.paused = False
        self.stop_flag = False
        self.current_frame = 0
        self.volume = 0.95  # Volumen por defecto al 95%
        self.stream = None
        self.samplerate = 44100

    def load(self, file_path):
        self.stop()
        try:
            data, self.samplerate = sf.read(file_path, dtype='float32')
            if data.ndim == 1:  # Mono
                self.current_song = np.column_stack((data, data))
            elif data.ndim == 2:  # Estéreo o más canales
                if data.shape[1] > 2:
                    self.current_song = data[:, :2]  # Tomar solo los dos primeros canales
                else:
                    self.current_song = data
            else:
                raise ValueError("Formato de audio no soportado")

            self.current_frame = 0
            self.paused = False
            self.stop_flag = False
        except Exception as e:
            logging.error(f"Error al cargar el archivo {file_path}: {str(e)}")
            messagebox.showerror("Error", f"No se pudo cargar el archivo: {os.path.basename(file_path)}\nError: {str(e)}")
            return False
        return True

    def play(self):
        if self.paused:
            self.paused = False
            return
        
        def callback(outdata, frames, time, status):
            if status:
                print(status)
            chunksize = min(len(self.current_song) - self.current_frame, frames)
            outdata[:chunksize] = self.current_song[self.current_frame:self.current_frame + chunksize]
            if chunksize < frames:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()
            self.current_frame += chunksize
            
            # Apply volume
            outdata *= self.volume

        self.stream = sd.OutputStream(
            samplerate=self.samplerate, channels=self.current_song.shape[1],
            callback=callback, finished_callback=self.song_finished)
        self.stream.start()

    def song_finished(self):
        self.stop()

    def pause(self):
        if self.stream:
            self.stream.stop()
        self.paused = True

    def stop(self):
        self.stop_flag = True
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.current_frame = 0
        self.paused = False

    def set_position(self, position):
        if self.current_song is not None:
            self.current_frame = int(position * len(self.current_song))

    def get_position(self):
        if self.current_song is not None and len(self.current_song) > 0:
            return self.current_frame / len(self.current_song)
        return 0

    def set_volume(self, volume):
        self.volume = volume

class AudioW(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.style = ttk.Style(theme="darkly")
        self.configure_styles()
        self.title("Audio-W")
        self.geometry("300x400")
        self.configure(bg='#2E2E2E')

        # Configurar el icono de la aplicación
        if os.path.exists('icon.ico'):
            self.iconbitmap('icon.ico')
        else:
            logging.warning("No se encontró el archivo 'icon.ico'")

        self.player = AudioPlayer()
        self.playlist = []
        self.current_song_index = -1

        self.create_gui()

        if len(sys.argv) > 1:
            self.add_song(sys.argv[1])

        self.update_thread = threading.Thread(target=self._update_thread, daemon=True)
        self.update_thread.start()

        # Iniciar el sistema de actualizaciones
        self.check_for_updates()

    def configure_styles(self):
        self.style.configure('TFrame', background='#2E2E2E')
        self.style.configure('TLabel', background='#2E2E2E', foreground='#E0E0E0')
        self.style.configure('TButton', background='#404040', foreground='#E0E0E0')
        self.style.map('TButton', background=[('active', '#505050')])
        self.style.configure('Horizontal.TProgressbar', background='#606060', troughcolor='#2E2E2E')
        self.style.configure('Horizontal.TScale', background='#2E2E2E', troughcolor='#404040')
        self.style.configure('Treeview', background='#363636', fieldbackground='#363636', foreground='#E0E0E0')
        self.style.map('Treeview', background=[('selected', '#505050')])

    def create_gui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.columnconfigure(0, weight=1)

        # Información de la canción
        self.song_info = ttk.Label(main_frame, text="", font=("Helvetica", 10), anchor="center", justify="center", wraplength=280)
        self.song_info.grid(row=0, column=0, sticky="ew", pady=(5, 10))

        # Barra de progreso
        self.progress_bar = ttk.Progressbar(main_frame, length=290, mode='determinate')
        self.progress_bar.grid(row=1, column=0, pady=(0, 5), sticky="ew")
        self.progress_bar.bind("<Button-1>", self.set_position)

        # Etiquetas de tiempo
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=2, column=0, sticky="ew")
        time_frame.columnconfigure(1, weight=1)

        self.current_time_label = ttk.Label(time_frame, text="0:00", font=("Helvetica", 8))
        self.current_time_label.grid(row=0, column=0, sticky="w")
        self.total_time_label = ttk.Label(time_frame, text="0:00", font=("Helvetica", 8))
        self.total_time_label.grid(row=0, column=2, sticky="e")

        # Botones de control
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, pady=10)

        ttk.Button(control_frame, text="⏮", command=self.prev_song, width=3).pack(side=tk.LEFT, padx=2)
        self.play_pause_button = ttk.Button(control_frame, text="▶", command=self.play_pause, width=3)
        self.play_pause_button.pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⏹", command=self.stop, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⏭", command=self.next_song, width=3).pack(side=tk.LEFT, padx=2)

        # Control de volumen
        volume_frame = ttk.Frame(main_frame)
        volume_frame.grid(row=4, column=0, pady=5, sticky="ew")
        volume_frame.columnconfigure(1, weight=1)

        self.volume_label = ttk.Label(volume_frame, text="Vol: 95%", font=("Helvetica", 8))
        self.volume_label.grid(row=0, column=0, padx=(0, 5))
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume, value=95)
        self.volume_scale.grid(row=0, column=1, sticky="ew")

        # Lista de reproducción
        playlist_frame = ttk.Frame(self)
        playlist_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        playlist_frame.columnconfigure(0, weight=1)
        playlist_frame.rowconfigure(0, weight=1)

        self.playlist_box = ttk.Treeview(playlist_frame, columns=("Título"), show="headings")
        self.playlist_box.heading("Título", text="Playlist")
        self.playlist_box.column("Título", anchor="w")
        self.playlist_box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(playlist_frame, orient="vertical", command=self.playlist_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.playlist_box.configure(yscrollcommand=scrollbar.set)

        self.playlist_box.drop_target_register(DND_FILES)
        self.playlist_box.dnd_bind('<<Drop>>', self.drop_files)
        self.playlist_box.bind('<Double-1>', self.on_playlist_double_click)
        self.playlist_box.bind('<Delete>', self.remove_song)

    def _update_thread(self):
        while True:
            self.update_progress()
            time.sleep(0.1)

    def set_position(self, event):
        if self.player.current_song is not None:
            width = self.progress_bar.winfo_width()
            click_position = event.x / width
            self.player.set_position(click_position)
            self.update_progress()

    def drop_files(self, event):
        files = self.tk.splitlist(event.data)
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                self.add_song(file)

    def add_song(self, file_path):
        if os.path.isfile(file_path):
            try:
                title, artist = self.get_audio_metadata(file_path)
                self.playlist.append((file_path, title, artist))
                self.playlist_box.insert("", tk.END, values=(f"{artist} - {title}",))
                if self.player.current_song is None:
                    self.current_song_index = 0
                    if self.player.load(file_path):
                        self.play_song()
                    else:
                        raise Exception("No se pudo cargar el archivo de audio")
            except Exception as e:
                logging.error(f"No se pudo añadir el archivo: {file_path}. Error: {str(e)}")
                messagebox.showerror("Error", f"No se pudo añadir el archivo: {os.path.basename(file_path)}\nError: {str(e)}")

    def get_audio_metadata(self, file_path):
        try:
            logging.debug(f"Procesando archivo: {file_path}")
            audio = File(file_path, easy=True)
            logging.debug(f"Metadatos raw: {audio}")
            
            title = self.get_first_value(audio.get('title', []))
            artist = self.get_first_value(audio.get('artist', []))
            
            if not title:
                title = os.path.splitext(os.path.basename(file_path))[0]
            if not artist:
                artist = 'Desconocido'
            
            logging.debug(f"Metadatos procesados - Título: {title}, Artista: {artist}")
            return title, artist
        except Exception as e:
            logging.error(f"Error al obtener metadatos de {file_path}: {str(e)}")
            return os.path.splitext(os.path.basename(file_path))[0], 'Desconocido'

    def get_first_value(self, value):
        if isinstance(value, (list, tuple)) and value:
            return self.get_first_value(value[0])
        elif isinstance(value, str):
            return value
        elif isinstance(value, np.ndarray):
            if value.size > 0:
                return self.get_first_value(value.item())
            else:
                return ''
        elif hasattr(value, 'text'):
            return value.text
        else:
            return str(value)

    def remove_song(self, event=None):
        selected = self.playlist_box.selection()
        if selected:
            index = self.playlist_box.index(selected[0])
            self.playlist_box.delete(selected[0])
            del self.playlist[index]
            if not self.playlist:
                self.stop()
                self.player.current_song = None
                self.current_song_index = -1
                self.update_song_info()

    def on_playlist_double_click(self, event):
        selection = self.playlist_box.selection()
        if selection:
            index = self.playlist_box.index(selection[0])
            self.current_song_index = index
            if self.player.load(self.playlist[index][0]):
                self.play_song()

    def play_pause(self):
        if self.player.current_song is None:
            return
        if self.player.paused:
            self.player.play()
            self.play_pause_button.config(text="⏸")
        else:
            self.player.pause()
            self.play_pause_button.config(text="▶")

    def play_song(self):
        self.player.play()
        self.play_pause_button.config(text="⏸")
        self.update_song_info()

    def stop(self):
        self.player.stop()
        self.progress_bar["value"] = 0
        self.play_pause_button.config(text="▶")
        self.current_time_label.config(text="0:00")

    def prev_song(self):
        if self.playlist:
            self.current_song_index = (self.current_song_index - 1) % len(self.playlist)
            if self.player.load(self.playlist[self.current_song_index][0]):
                self.play_song()

    def next_song(self):
        if self.playlist:
            self.current_song_index = (self.current_song_index + 1) % len(self.playlist)
            if self.player.load(self.playlist[self.current_song_index][0]):
                self.play_song()

    def set_volume(self, val):
        volume = float(val) / 100
        self.player.set_volume(volume)
        self.volume_label.config(text=f"Vol: {int(float(val))}%")

    def update_song_info(self):
        if self.player.current_song is not None and 0 <= self.current_song_index < len(self.playlist):
            song_info = self.playlist[self.current_song_index]
            info_text = f"{song_info[2]}\n{song_info[1]}"
            self.song_info.config(text=info_text)
        else:
            self.song_info.config(text="No se ha seleccionado ninguna canción")

    def update_progress(self):
        if self.player.current_song is not None:
            position = self.player.get_position()
            self.progress_bar["value"] = position * 100
            
            current_time = int(position * len(self.player.current_song) / self.player.samplerate)
            total_time = len(self.player.current_song) // self.player.samplerate
            
            self.current_time_label.config(text=self.format_time(current_time))
            self.total_time_label.config(text=self.format_time(total_time))

    def format_time(self, seconds):
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes}:{seconds:02d}"

    def get_app_data_path(self):
        if getattr(sys, 'frozen', False):
            # Si es una aplicación empaquetada (exe)
            return os.path.dirname(sys.executable)
        else:
            # Si se está ejecutando desde el script
            return os.path.dirname(os.path.abspath(__file__))

    def check_for_updates(self):
        last_check = self.load_last_check_date()
        if datetime.now() - last_check >= timedelta(days=1):
            threading.Thread(target=self._check_and_update, daemon=True).start()

    def load_last_check_date(self):
        try:
            check_file = os.path.join(self.get_app_data_path(), 'last_update_check.txt')
            with open(check_file, 'r') as f:
                return datetime.fromisoformat(f.read().strip())
        except FileNotFoundError:
            return datetime.min
        except Exception as e:
            logging.error(f"Error al cargar la fecha de última comprobación: {e}")
            return datetime.min

    def save_last_check_date(self):
        try:
            check_file = os.path.join(self.get_app_data_path(), 'last_update_check.txt')
            with open(check_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logging.error(f"Error al guardar la fecha de última comprobación: {e}")

    def _check_and_update(self):
        try:
            response = requests.get('https://api.github.com/repos/Wamphyre/Audio-W/releases/latest')
            latest_release = json.loads(response.text)
            latest_version = latest_release['tag_name']
            current_version = self.get_current_version()

            if latest_version > current_version:
                messagebox.showinfo("Actualización disponible", 
                                    f"Hay una nueva versión disponible: {latest_version}\n"
                                    f"Por favor, visite nuestro repositorio para descargarla e instalarla:\n"
                                    f"https://github.com/Wamphyre/Audio-W/releases")
            else:
                logging.info("El software está actualizado.")
        except Exception as e:
            logging.error(f"Error al buscar actualizaciones: {str(e)}")
        finally:
            self.save_last_check_date()

    def get_current_version(self):
        return "v1.1"

def register_file_types():
    file_types = ['.mp3', '.wav', '.ogg', '.flac']
    executable = sys.executable
    if executable.endswith('python.exe'):  # Si se está ejecutando desde el intérprete
        executable = os.path.abspath(sys.argv[0])

    for file_type in file_types:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{file_type}")
            winreg.SetValue(key, "", winreg.REG_SZ, "Audio-W")
            winreg.CloseKey(key)
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Classes\\Audio-W\\shell\\open\\command")
            winreg.SetValue(key, "", winreg.REG_SZ, f'"{executable}" "%1"')
            winreg.CloseKey(key)
        except WindowsError as e:
            logging.error(f"Error al registrar {file_type}: {e}")

def main():
    if sys.platform.startswith('win'):
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    app = AudioW()
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--register":
        register_file_types()
    else:
        main()