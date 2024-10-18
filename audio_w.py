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

class AudioW(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.initialize_window()
        self.initialize_variables()
        self.create_widgets()
        self.bind_events()

    def initialize_window(self):
        self.title("Audio-W v1.3")
        self.geometry("400x500")
        self.configure(bg='#1E1E1E')
        self.set_icon()
        self.setup_style()

    def initialize_variables(self):
        self.current_song = None
        self.playlist = []
        self.is_playing = False
        self.audio_thread = None
        self.stream = None
        self.visualizer_update_interval = 100
        self.last_visualizer_update = 0
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.play_future = None
        self.buffer_size = 2048
        self.total_duration = 0

    def set_icon(self):
        icon_path = self.get_icon_path()
        if icon_path:
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass

    def get_icon_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            return 'icon.ico' if os.path.exists('icon.ico') else None

    def setup_style(self):
        self.style = ttk.Style("darkly")
        self.style.configure("TFrame", background='#1E1E1E')
        self.style.configure("TLabel", background='#1E1E1E', foreground='#FFFFFF')
        self.style.configure("TButton", background='#2E2E2E', foreground='#FFFFFF')
        self.style.configure("Horizontal.TScale", background='#1E1E1E', troughcolor='#2E2E2E')
        self.style.configure('Treeview', background='#2E2E2E', fieldbackground='#2E2E2E', foreground='#FFFFFF')
        self.style.configure('Treeview.Heading', background='#1E1E1E', foreground='#FFFFFF', relief='flat')
        self.style.map('Treeview', background=[('selected', '#3E3E3E')])

    def create_widgets(self):
        self.create_main_frame()
        self.create_metadata_frame()
        self.create_visualizer()
        self.create_progress_frame()
        self.create_control_frame()
        self.create_playlist_frame()
        self.create_total_duration_label()

    def create_main_frame(self):
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.pack(fill=BOTH, expand=YES)

    def create_metadata_frame(self):
        self.metadata_frame = ttk.Frame(self.main_frame)
        self.metadata_frame.pack(fill=X, pady=5)
        
        self.title_label = ttk.Label(self.metadata_frame, text="", font=("TkDefaultFont", 10, "bold"))
        self.title_label.pack(fill=X)
        
        self.artist_label = ttk.Label(self.metadata_frame, text="", font=("TkDefaultFont", 9))
        self.artist_label.pack(fill=X)

    def create_visualizer(self):
        self.visualizer = tk.Canvas(self.main_frame, height=50, bg='#000000', highlightthickness=0)
        self.visualizer.pack(fill=X, pady=5)

    def create_progress_frame(self):
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=X, pady=5)
        
        self.current_time = ttk.Label(self.progress_frame, text="0:00", width=5)
        self.current_time.pack(side=LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(self.progress_frame, orient=HORIZONTAL, from_=0, to=100, variable=self.progress_var)
        self.progress_bar.pack(side=LEFT, fill=X, expand=YES, padx=5)
        self.progress_bar.bind("<ButtonRelease-1>", self.set_position)
        
        self.total_time = ttk.Label(self.progress_frame, text="0:00", width=5)
        self.total_time.pack(side=RIGHT)

    def create_control_frame(self):
        self.control_frame = ttk.Frame(self.main_frame)
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

    def create_playlist_frame(self):
        self.playlist_frame = ttk.Frame(self.main_frame)
        self.playlist_frame.pack(pady=5, fill=BOTH, expand=YES)
        
        self.playlist_box = ttk.Treeview(self.playlist_frame, columns=("title", "artist", "duration"), show="headings", style='info', height=10)
        self.playlist_box.heading("title", text="Título")
        self.playlist_box.heading("artist", text="Artista")
        self.playlist_box.heading("duration", text="Duración")
        self.playlist_box.column("title", width=150)
        self.playlist_box.column("artist", width=100)
        self.playlist_box.column("duration", width=70, anchor=E)
        self.playlist_box.pack(side=LEFT, fill=BOTH, expand=YES)
        
        scrollbar = ttk.Scrollbar(self.playlist_frame, orient=VERTICAL, command=self.playlist_box.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.playlist_box.configure(yscrollcommand=scrollbar.set)

    def create_total_duration_label(self):
        self.total_duration_label = ttk.Label(self.main_frame, text="Duración total: 0:00:00")
        self.total_duration_label.pack(pady=5)

    def bind_events(self):
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        if DND_FILES:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
            self.playlist_box.drop_target_register(DND_FILES)
            self.playlist_box.dnd_bind("<<Drop>>", self.add_file)

        self.playlist_box.bind("<Delete>", self.remove_selected_song)
        self.playlist_box.bind("<Double-1>", self.on_double_click)
        self.playlist_box.bind("<ButtonPress-1>", self.on_drag_start)
        self.playlist_box.bind("<B1-Motion>", self.on_drag_motion)
        self.playlist_box.bind("<ButtonRelease-1>", self.on_drag_release)

    def on_drop(self, event):
        files = self.tk.splitlist(event.data)
        for file_path in files:
            self.add_file_to_playlist(file_path)
        self.sort_playlist()

    def play_pause(self):
        if not self.is_playing and self.current_song:
            self.play()
        elif self.is_playing:
            self.pause()
        elif not self.current_song and self.playlist:
            self.play_song(self.playlist[0]['file'])

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
        self.progress_var.set(0)
        self.current_time.configure(text="0:00")
        self.current_sample = 0
        if self.stream:
            self.stream.stop()
        if self.audio_thread:
            self.audio_thread.join(timeout=0.5)

    def set_position(self, event):
        if self.current_song and hasattr(self, 'total_samples'):
            width = self.progress_bar.winfo_width()
            click_position = event.x / width
            self.current_sample = int(click_position * self.total_samples)
            self.current_sample = max(0, min(self.current_sample, self.total_samples - 1))
            if not self.is_playing:
                self.play()

    def next_song(self):
        if self.playlist:
            current_index = next((i for i, song in enumerate(self.playlist) if song['file'] == self.current_song), -1)
            if current_index < len(self.playlist) - 1:
                next_index = current_index + 1
                self.play_song(self.playlist[next_index]['file'])
            else:
                self.stop()
                self.update_playlist_highlight()

    def previous_song(self):
        if self.playlist:
            current_index = next((i for i, song in enumerate(self.playlist) if song['file'] == self.current_song), 0)
            if current_index > 0:
                prev_index = current_index - 1
                self.play_song(self.playlist[prev_index]['file'])
            else:
                self.play_song(self.playlist[0]['file'])

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
                
                metadata = self.get_metadata(file_path)
                title = metadata['title'] or os.path.basename(file_path)
                artist = metadata['artist']
                duration_str = self.format_duration(duration)
                
                new_song = {
                    'file': file_path,
                    'title': title,
                    'artist': artist,
                    'duration': duration,
                    'album': metadata.get('album', ''),
                    'track': metadata.get('track', '0')
                }
                
                self.playlist.append(new_song)
                
                self.playlist_box.insert('', tk.END, values=(title, artist, duration_str))
                
                self.update_total_duration_display()
            except Exception as e:
                print(f"Error al verificar el archivo {file_path}: {e}")
                messagebox.showerror("Error", f"El archivo {os.path.basename(file_path)} no es un archivo de audio válido.")

    def sort_playlist(self):
        if not self.playlist:
            return

        groups = {}
        for song in self.playlist:
            key = (song['artist'], song['album'])
            if key not in groups:
                groups[key] = []
            groups[key].append(song)

        for group in groups.values():
            group.sort(key=lambda x: (int(x['track']), x['title']))

        self.playlist = [song for group in groups.values() for song in group]

        self.update_playlist_display()

    def update_playlist_display(self):
        self.playlist_box.delete(*self.playlist_box.get_children())
        for song in self.playlist:
            self.playlist_box.insert('', tk.END, values=(song['title'], song['artist'], self.format_duration(song['duration'])))
        self.update_playlist_highlight()

    def remove_selected_song(self, event=None):
        selection = self.playlist_box.selection()
        if selection:
            for item in selection:
                index = self.playlist_box.index(item)
                song = self.playlist[index]
                self.playlist_box.delete(item)
                del self.playlist[index]
                
                self.total_duration -= song['duration']
            
            if self.current_song not in [song['file'] for song in self.playlist]:
                self.stop()
                self.current_song = None
                if self.playlist:
                    self.play_song(self.playlist[0]['file'])
                else:
                    self.title_label.config(text="")
                    self.artist_label.config(text="")
            self.update_playlist_highlight()
            self.update_total_duration_display()

    def on_double_click(self, event):
        item = self.playlist_box.identify('item', event.x, event.y)
        if item:
            index = self.playlist_box.index(item)
            self.play_song(self.playlist[index]['file'])

    def on_drag_start(self, event):
        item = self.playlist_box.identify_row(event.y)
        if item:
            self.drag_data = {'item': item, 'index': self.playlist_box.index(item)}

    def on_drag_motion(self, event):
        if hasattr(self, 'drag_data'):
            target = self.playlist_box.identify_row(event.y)
            if target and target != self.drag_data['item']:
                self.playlist_box.move(self.drag_data['item'], self.playlist_box.parent(target), self.playlist_box.index(target))

    def on_drag_release(self, event):
        if hasattr(self, 'drag_data'):
            target = self.playlist_box.identify_row(event.y)
            if target:
                new_index = self.playlist_box.index(target)
                old_index = self.drag_data['index']
                item = self.playlist.pop(old_index)
                self.playlist.insert(new_index, item)
            del self.drag_data

    def get_metadata(self, file_path):
        try:
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path)
                title = str(audio.get('TIT2', [''])[0])
                artist = str(audio.get('TPE1', [''])[0])
                album = str(audio.get('TALB', [''])[0])
                track = str(audio.get('TRCK', ['0'])[0]).split('/')[0]
            elif file_path.lower().endswith('.wav'):
                audio = WAVE(file_path)
                title = str(audio.get('title', [''])[0])
                artist = str(audio.get('artist', [''])[0])
                album = str(audio.get('album', [''])[0])
                track = '0'
            elif file_path.lower().endswith('.flac'):
                audio = FLAC(file_path)
                title = str(audio.get('title', [''])[0])
                artist = str(audio.get('artist', [''])[0])
                album = str(audio.get('album', [''])[0])
                track = str(audio.get('tracknumber', ['0'])[0])
            else:
                return {'title': '', 'artist': '', 'album': '', 'track': '0'}
            
            return {
                'title': title or os.path.basename(file_path),
                'artist': artist or 'Desconocido',
                'album': album or 'Desconocido',
                'track': track
            }
        except Exception as e:
            print(f"Error al obtener metadatos de {file_path}: {e}")
            return {'title': os.path.basename(file_path), 'artist': 'Desconocido', 'album': 'Desconocido', 'track': '0'}

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
            self.after(0, lambda: self.total_time.config(text=self.format_duration(duration)))
            
            self.after(0, self.update_playlist_highlight)
            self.after(0, self.play)
        except Exception as e:
            print(f"Error al reproducir la canción {song}: {e}")
            self.after(0, self.next_song)

    def update_playlist_highlight(self):
        for item in self.playlist_box.get_children():
            self.playlist_box.item(item, tags=())
        
        if self.current_song in [song['file'] for song in self.playlist]:
            index = next((i for i, song in enumerate(self.playlist) if song['file'] == self.current_song), None)
            if index is not None:
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
        self.progress_var.set(progress * 100)
        self.current_time.configure(text=self.format_duration(current_time))

    def update_visualizer(self):
        self.visualizer.delete("all")
        width = self.visualizer.winfo_width()
        height = self.visualizer.winfo_height()
        num_bars = 20
        bar_width = width / num_bars
        for i in range(num_bars):
            bar_height = np.random.randint(1, height)
            self.visualizer.create_rectangle(
                i * bar_width, height - bar_height, 
                (i + 1) * bar_width, height, 
                fill="#00FF00", outline=""
            )

    def update_total_duration_display(self):
        self.total_duration_label.config(text=f"Duración total: {self.format_duration(self.total_duration)}")

    def format_duration(self, duration):
        hours, remainder = divmod(int(duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def add_and_play_file(self, file_path):
        if file_path.lower().endswith(('.mp3', '.wav', '.flac')):
            self.add_file_to_playlist(file_path)
            self.sort_playlist()
            if not self.is_playing:
                self.play_song(file_path)
        else:
            print(f"Formato de archivo no soportado: {file_path}")

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
    app = AudioW()
    
    if len(sys.argv) > 1:
        file_path = os.path.abspath(sys.argv[1])
        app.after(100, lambda: app.add_and_play_file(file_path))
    
    app.mainloop()

if __name__ == "__main__":
    main()