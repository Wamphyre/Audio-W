import os
import sys
import tkinter as tk
from tkinter import messagebox
import time as python_time
import threading
import concurrent.futures

def _get_tkdnd_library_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'tkinterdnd2', 'tkdnd')
    else:
        import tkinterdnd2
        return os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

os.environ['TKDND_LIBRARY'] = _get_tkdnd_library_path()

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    print("No se pudo importar tkinterdnd2. La funcionalidad de arrastrar y soltar estará deshabilitada.")
    TkinterDnD = tk.Tk
    DND_FILES = None

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import sounddevice as sd
import soundfile as sf
from mutagen import File
from mutagen.wave import WAVE
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import numpy as np
import win32event
import win32api
import winerror
import win32gui
import win32con
import pywintypes

class SingleInstanceApp:
    def __init__(self):
        self.mutexname = "AudioW_v1.2_{D0E858DF-985E-4907-B7FB-8D732C3FC3B9}"
        self.mutex = win32event.CreateMutex(None, False, self.mutexname)
        self.lasterror = win32api.GetLastError()
        
    def already_running(self):
        return (self.lasterror == winerror.ERROR_ALREADY_EXISTS)

    def activate_running_instance(self, file_path=None):
        try:
            handle = win32gui.FindWindow(None, "Audio-W v1.2")
            if handle:
                win32gui.ShowWindow(handle, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(handle)
                
                if file_path:
                    win32gui.PostMessage(handle, win32con.WM_USER + 1, 0, 0)
                    with open('temp_file_path.txt', 'w') as f:
                        f.write(file_path)
                return True
        except Exception as e:
            print(f"Error al activar la instancia en ejecución: {e}")
        return False

class AudioW(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Audio-W v1.2")
        self.geometry("300x450")  # Ajustado el tamaño de la ventana
        self.configure(bg='#1E1E1E')
        
        icon_path = self.get_icon_path()
        if icon_path:
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                print(f"No se pudo cargar el icono desde {icon_path}. Usando el icono por defecto.")
        
        self.style = ttk.Style("darkly")
        self.style.configure("TFrame", background='#1E1E1E')
        self.style.configure("TLabel", background='#1E1E1E', foreground='#FFFFFF')
        self.style.configure("TButton", background='#2E2E2E', foreground='#FFFFFF')
        self.style.configure("Horizontal.TScale", background='#1E1E1E', troughcolor='#2E2E2E')
        self.style.configure('Treeview', background='#2E2E2E', fieldbackground='#2E2E2E', foreground='#FFFFFF')
        self.style.configure('Treeview.Heading', background='#1E1E1E', foreground='#FFFFFF', relief='flat')
        self.style.map('Treeview', background=[('selected', '#3E3E3E')])
        
        self.current_song = None
        self.playlist = []
        self.is_playing = False
        self.audio_thread = None
        self.stream = None
        
        self.visualizer_update_interval = 100  # Actualizar el visualizador cada 100ms
        self.last_visualizer_update = 0
        
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.play_future = None
        self.buffer_size = 2048  # Tamaño de buffer aumentado
        
        self.total_duration = 0  # Variable para almacenar la duración total
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        if DND_FILES:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)

        self.bind("<Map>", self.on_map)
        self.after(100, self.check_for_new_file)

    def get_icon_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            return 'icon.ico' if os.path.exists('icon.ico') else None
    
    def on_map(self, event):
        message = win32gui.RegisterWindowMessage("AudioWNewFile")
        self.bind(f"<<Message-{message}>>", self.handle_new_file)

    def handle_new_file(self, event):
        try:
            with open('temp_file_path.txt', 'r') as f:
                file_path = f.read().strip()
            os.remove('temp_file_path.txt')
            self.add_and_play_file(file_path)
        except Exception as e:
            print(f"Error al manejar el nuevo archivo: {e}")

    def add_and_play_file(self, file_path):
        self.add_file_to_playlist(file_path)
        self.play_song(file_path)

    def check_for_new_file(self):
        try:
            if os.path.exists('temp_file_path.txt'):
                with open('temp_file_path.txt', 'r') as f:
                    file_path = f.read().strip()
                os.remove('temp_file_path.txt')
                self.add_and_play_file(file_path)
        except Exception as e:
            print(f"Error al verificar nuevo archivo: {e}")
        self.after(100, self.check_for_new_file)
    
    def on_drop(self, event):
        files = self.tk.splitlist(event.data)
        for file_path in files:
            self.add_file_to_playlist(file_path)
        self.sort_playlist()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        self.metadata_frame = ttk.Frame(main_frame)
        self.metadata_frame.pack(fill=X, pady=5)
        
        self.title_label = ttk.Label(self.metadata_frame, text="", font=("TkDefaultFont", 10, "bold"))
        self.title_label.pack(fill=X)
        
        self.artist_label = ttk.Label(self.metadata_frame, text="", font=("TkDefaultFont", 9))
        self.artist_label.pack(fill=X)
        
        self.visualizer = tk.Canvas(main_frame, height=50, bg='#000000', highlightthickness=0)
        self.visualizer.pack(fill=X, pady=5)
        
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=X, pady=5)
        
        self.current_time = ttk.Label(self.progress_frame, text="0:00", width=5)
        self.current_time.pack(side=LEFT)
        
        self.progress_bar = ttk.Scale(self.progress_frame, orient=HORIZONTAL, from_=0, to=100)
        self.progress_bar.pack(side=LEFT, fill=X, expand=YES, padx=5)
        self.progress_bar.bind("<ButtonRelease-1>", self.set_position)
        
        self.total_time = ttk.Label(self.progress_frame, text="0:00", width=5)
        self.total_time.pack(side=RIGHT)
        
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.pack(pady=5)
        
        button_style = lambda name: ttk.Button(self.control_frame, style='info-outline', width=3)
        
        self.prev_button = button_style("prev")
        self.prev_button.configure(text="⏮", command=self.previous_song)
        self.prev_button.pack(side=LEFT, padx=2)
        
        self.play_button = button_style("play")
        self.play_button.configure(text="▶", command=self.play_pause)
        self.play_button.pack(side=LEFT, padx=2)
        
        self.stop_button = button_style("stop")
        self.stop_button.configure(text="⏹", command=self.stop)
        self.stop_button.pack(side=LEFT, padx=2)
        
        self.next_button = button_style("next")
        self.next_button.configure(text="⏭", command=self.next_song)
        self.next_button.pack(side=LEFT, padx=2)
        
        self.playlist_frame = ttk.Frame(main_frame)
        self.playlist_frame.pack(pady=5, fill=BOTH, expand=YES)
        
        self.playlist_box = ttk.Treeview(self.playlist_frame, columns=("title",), show="headings", style='info', height=10)
        self.playlist_box.heading("title", text="Playlist", anchor=W)
        self.playlist_box.column("title", width=200)
        self.playlist_box.pack(side=LEFT, fill=BOTH, expand=YES)
        
        scrollbar = ttk.Scrollbar(self.playlist_frame, orient=VERTICAL, command=self.playlist_box.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.playlist_box.configure(yscrollcommand=scrollbar.set)
        
        if DND_FILES:
            self.playlist_box.drop_target_register(DND_FILES)
            self.playlist_box.dnd_bind("<<Drop>>", self.add_file)
        self.playlist_box.bind("<Delete>", self.remove_selected_song)
        self.playlist_box.bind("<Double-1>", self.on_double_click)
        
        # Widget para mostrar la duración total de la playlist
        self.total_duration_label = ttk.Label(main_frame, text="Duración total: 0:00:00")
        self.total_duration_label.pack(pady=5)
        
    def play_pause(self):
        if not self.is_playing and self.current_song:
            self.play()
        elif self.is_playing:
            self.pause()
        elif not self.current_song and self.playlist:
            self.play_song(self.playlist[0])
    
    def play(self):
        if not self.is_playing:
            self.is_playing = True
            self.play_button.configure(text="⏸")
            if not self.audio_thread or not self.audio_thread.is_alive():
                self.audio_thread = threading.Thread(target=self.audio_callback)
                self.audio_thread.start()
    
    def pause(self):
        self.is_playing = False
        self.play_button.configure(text="▶")
    
    def stop(self):
        self.is_playing = False
        self.play_button.configure(text="▶")
        self.progress_bar.set(0)
        self.current_time.configure(text="0:00")
        self.current_sample = 0
        if self.stream:
            self.stream.stop()
        if self.audio_thread:
            self.audio_thread.join(timeout=0.5)
    
    def set_position(self, event):
        if self.current_song and self.total_samples > 0:
            width = self.progress_bar.winfo_width()
            click_position = event.x / width
            self.current_sample = int(click_position * self.total_samples)
            self.current_sample = max(0, min(self.current_sample, self.total_samples - 1))
            if not self.is_playing:
                self.play()
    
    def next_song(self):
        if self.playlist:
            current_index = self.playlist.index(self.current_song) if self.current_song in self.playlist else -1
            if current_index < len(self.playlist) - 1:
                next_index = current_index + 1
                self.play_song(self.playlist[next_index])
            else:
                self.stop()
                self.update_playlist_highlight()

    def previous_song(self):
        if self.playlist:
            current_index = self.playlist.index(self.current_song) if self.current_song in self.playlist else 0
            if current_index > 0:
                prev_index = current_index - 1
                self.play_song(self.playlist[prev_index])
            else:
                self.play_song(self.playlist[0])
    
    def add_file(self, event):
        files = self.tk.splitlist(event.data)
        for f in files:
            self.add_file_to_playlist(f)
        self.sort_playlist()
    
    def add_file_to_playlist(self, file_path):
        if file_path.lower().endswith(('.mp3', '.wav', '.flac')):
            try:
                with sf.SoundFile(file_path) as f:
                    duration = len(f) / f.samplerate
                self.total_duration += duration
                
                self.playlist.append(file_path)
                metadata = self.get_metadata(file_path)
                title = metadata['title'] or os.path.basename(file_path)
                self.playlist_box.insert('', tk.END, values=(title,))
                
                self.update_total_duration_display()
            except Exception as e:
                print(f"Error al verificar el archivo {file_path}: {e}")
                messagebox.showerror("Error", f"El archivo {os.path.basename(file_path)} no es un archivo de audio válido.")
    
    def sort_playlist(self):
        sorted_playlist = sorted(self.playlist, key=lambda x: self.get_track_number(x))
        self.playlist = sorted_playlist
        self.update_playlist_display()
        self.update_total_duration_display()
    
    def get_track_number(self, file_path):
        try:
            audio = File(file_path, easy=True)
            track = audio.get('tracknumber', ['0'])[0]
            return int(track.split('/')[0])
        except Exception:
            return 0
    
    def update_playlist_display(self):
        self.playlist_box.delete(*self.playlist_box.get_children())
        for file_path in self.playlist:
            metadata = self.get_metadata(file_path)
            title = metadata['title'] or os.path.basename(file_path)
            self.playlist_box.insert('', tk.END, values=(title,))
        self.update_playlist_highlight()
    
    def remove_selected_song(self, event=None):
        selection = self.playlist_box.selection()
        if selection:
            for item in selection:
                index = self.playlist_box.index(item)
                file_path = self.playlist[index]
                self.playlist_box.delete(item)
                del self.playlist[index]
                
                # Restar la duración de la canción eliminada
                with sf.SoundFile(file_path) as f:
                    duration = len(f) / f.samplerate
                self.total_duration -= duration
            
            if self.current_song not in self.playlist:
                self.stop()
                self.current_song = None
                if self.playlist:
                    self.play_song(self.playlist[0])
                else:
                    self.title_label.config(text="")
                    self.artist_label.config(text="")
            self.update_playlist_highlight()
            self.update_total_duration_display()
    
    def on_double_click(self, event):
        item = self.playlist_box.identify('item', event.x, event.y)
        if item:
            index = self.playlist_box.index(item)
            self.play_song(self.playlist[index])
    
    def get_metadata(self, file_path):
        try:
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path)
                title = str(audio.get('TIT2', [''])[0])
                artist = str(audio.get('TPE1', [''])[0])
            elif file_path.lower().endswith('.wav'):
                audio = WAVE(file_path)
                title = str(audio.get('title', [''])[0])
                artist = str(audio.get('artist', [''])[0])
            elif file_path.lower().endswith('.flac'):
                audio = FLAC(file_path)
                title = str(audio.get('title', [''])[0])
                artist = str(audio.get('artist', [''])[0])
            else:
                return {'title': '', 'artist': ''}
            
            return {
                'title': title or os.path.basename(file_path),
                'artist': artist or 'Desconocido'
            }
        except Exception as e:
            print(f"Error al obtener metadatos de {file_path}: {e}")
            return {'title': os.path.basename(file_path), 'artist': 'Desconocido'}
    
    def play_song(self, song):
        if self.play_future:
            self.play_future.cancel()
        self.stop()
        self.current_song = song
        self.play_future = self.executor.submit(self._load_and_play_song, song)

    def _load_and_play_song(self, song):
        try:
            self.data, self.fs = sf.read(song)
            if self.data.dtype != np.float32:
                self.data = self.data.astype(np.float32)
            self.total_samples = len(self.data)
            self.current_sample = 0
            
            metadata = self.get_metadata(song)
            self.after(0, lambda: self.title_label.config(text=metadata['title']))
            self.after(0, lambda: self.artist_label.config(text=metadata['artist']))
            
            duration = self.total_samples / self.fs
            self.after(0, lambda: self.total_time.config(text=f"{int(duration//60)}:{int(duration%60):02d}"))
            
            self.after(0, self.update_playlist_highlight)
            self.after(0, self.play)
        except Exception as e:
            print(f"Error al reproducir la canción {song}: {e}")
            self.after(0, self.next_song)

    def update_playlist_highlight(self):
        for item in self.playlist_box.get_children():
            self.playlist_box.item(item, tags=())
        
        if self.current_song in self.playlist:
            index = self.playlist.index(self.current_song)
            item = self.playlist_box.get_children()[index]
            self.playlist_box.item(item, tags=('playing',))
            self.playlist_box.tag_configure('playing', background='#4E4E4E')

    def audio_callback(self):
        def callback(outdata, frames, time, status):
            if status:
                print(f'Error de estado: {status}')
            
            if self.is_playing and self.current_sample < self.total_samples:
                end_sample = min(self.current_sample + frames, self.total_samples)
                data = self.data[self.current_sample:end_sample]
                if len(data) < frames:
                    outdata[:len(data)] = data
                    outdata[len(data):] = np.zeros((frames - len(data), self.data.shape[1]))
                else:
                    outdata[:] = data
                self.current_sample = end_sample
                
                progress = self.current_sample / self.total_samples
                current_time = self.current_sample / self.fs
                
                self.after(0, lambda: self.update_ui(progress, current_time))
                
                current_time_ms = python_time.time() * 1000
                if current_time_ms - self.last_visualizer_update >= self.visualizer_update_interval:
                    self.after(0, self.update_visualizer)
                    self.last_visualizer_update = current_time_ms
            else:
                outdata.fill(0)
                if self.current_sample >= self.total_samples:
                    self.after(0, self.next_song)
        
        try:
            self.stream = sd.OutputStream(
                samplerate=self.fs, 
                channels=self.data.shape[1], 
                callback=callback,
                blocksize=self.buffer_size,
                latency='high'
            )
            with self.stream:
                while self.is_playing:
                    sd.sleep(100)
        except Exception as e:
            print(f"Error en audio_callback: {e}")
            self.after(0, self.next_song)

    def update_ui(self, progress, current_time):
        self.progress_bar.set(progress * 100)
        self.current_time.configure(text=f"{int(current_time//60)}:{int(current_time%60):02d}")
    
    def update_visualizer(self):
        self.visualizer.delete("all")
        for i in range(20):
            height = np.random.randint(1, 50)
            self.visualizer.create_rectangle(i*15, 50-height, (i+1)*15-1, 50, fill="#00FF00", outline="")
    
    def update_total_duration_display(self):
        hours, remainder = divmod(int(self.total_duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.total_duration_label.config(text=f"Duración total: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def on_closing(self):
        self.is_playing = False
        if self.play_future:
            self.play_future.cancel()
        if self.stream:
            self.stream.stop()
        if self.audio_thread:
            self.audio_thread.join(timeout=0.5)
        self.executor.shutdown(wait=False)
        self.destroy()

def main():
    app_instance = SingleInstanceApp()
    
    if app_instance.already_running():
        print("La aplicación ya está en ejecución. Activando la ventana existente.")
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if app_instance.activate_running_instance(file_path):
                sys.exit(0)
        else:
            if app_instance.activate_running_instance():
                sys.exit(0)
        print("No se pudo activar la instancia en ejecución. Iniciando una nueva instancia.")
    
    app = AudioW()
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        app.after(100, lambda: app.add_and_play_file(file_path))
    
    app.mainloop()

if __name__ == "__main__":
    main()