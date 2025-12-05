import customtkinter as ctk
import yt_dlp
import threading
import os
import certifi
import requests
from PIL import Image, ImageTk
from io import BytesIO
from tkinter import filedialog, messagebox

# Fix for macOS SSL
os.environ['SSL_CERT_FILE'] = certifi.where()

# Theme Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")  # Will override with custom red colors

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("YouTube Downloader")
        self.geometry("800x650")
        self.resizable(False, False)

        # Custom Colors (YouTube Red-ish)
        self.yt_red = "#FF0000"
        self.yt_dark_red = "#CC0000"
        self.primary_color = self.yt_red

        # Data
        self.video_info = None
        self.download_folder = os.path.expanduser("~/Downloads")

        self.create_widgets()

    def create_widgets(self):
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.logo_label = ctk.CTkLabel(
            self.header_frame, 
            text="YouTube İndirme Aracı", 
            font=("Roboto", 24, "bold"),
            text_color=self.yt_red
        )
        self.logo_label.pack()

        self.credit_label = ctk.CTkLabel(
            self.header_frame,
            text="byPhurki",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.credit_label.pack(pady=(0, 5))

        # --- Input Section ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(fill="x", padx=20, pady=10)

        self.url_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="YouTube Video Linkini Yapıştırın...",
            height=40,
            font=("Roboto", 14)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)

        self.fetch_btn = ctk.CTkButton(
            self.input_frame, 
            text="Bilgileri Çek", 
            command=self.start_fetch_info,
            fg_color=self.yt_red,
            hover_color=self.yt_dark_red,
            height=40,
            font=("Roboto", 14, "bold")
        )
        self.fetch_btn.pack(side="right", padx=(0, 10), pady=10)

        # --- Info Section (Thumbnail & Title) ---
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Placeholder for Thumbnail
        self.thumbnail_label = ctk.CTkLabel(self.info_frame, text="", height=200, corner_radius=10, fg_color="#2b2b2b")
        self.thumbnail_label.pack(fill="x", pady=(0, 10))

        self.title_label = ctk.CTkLabel(
            self.info_frame, 
            text="Video bekleniyor...", 
            font=("Roboto", 16, "bold"),
            wraplength=700
        )
        self.title_label.pack()

        self.meta_label = ctk.CTkLabel(self.info_frame, text="", text_color="gray")
        self.meta_label.pack()

        # --- Options Section ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(fill="x", padx=20, pady=10)

        # Type Selection
        self.type_var = ctk.StringVar(value="video")
        self.radio_video = ctk.CTkRadioButton(
            self.options_frame, text="Video", variable=self.type_var, value="video", 
            fg_color=self.yt_red, hover_color=self.yt_dark_red, command=self.update_format_options
        )
        self.radio_video.pack(side="left", padx=20, pady=15)

        self.radio_audio = ctk.CTkRadioButton(
            self.options_frame, text="Ses (MP3)", variable=self.type_var, value="audio", 
            fg_color=self.yt_red, hover_color=self.yt_dark_red, command=self.update_format_options
        )
        self.radio_audio.pack(side="left", padx=20, pady=15)

        # Format Dropdown
        self.format_var = ctk.StringVar(value="Format Seçiniz")
        self.format_menu = ctk.CTkOptionMenu(
            self.options_frame, 
            variable=self.format_var,
            fg_color="#333",
            button_color="#444",
            button_hover_color="#555", 
            width=200
        )
        self.format_menu.pack(side="left", padx=20, pady=15)

        # Folder Selection
        self.folder_btn = ctk.CTkButton(
            self.options_frame, 
            text="Kaydetme Yeri", 
            command=self.select_folder,
            fg_color="#444",
            hover_color="#555"
        )
        self.folder_btn.pack(side="right", padx=20, pady=15)

        # --- Status & Actions ---
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, orientation="horizontal", progress_color=self.yt_red)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.status_label = ctk.CTkLabel(self.status_frame, text="Hazır", text_color="gray")
        self.status_label.pack(side="left")

        self.download_btn = ctk.CTkButton(
            self.status_frame, 
            text="İNDİR", 
            command=self.start_download,
            fg_color=self.yt_red,
            hover_color=self.yt_dark_red,
            height=50,
            font=("Roboto", 18, "bold"),
            state="disabled"
        )
        self.download_btn.pack(side="right")

    # --- Logic ---

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.status_label.configure(text=f"Konum: {os.path.basename(folder)}")

    def start_fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        
        self.fetch_btn.configure(state="disabled", text="Çekiliyor...")
        self.status_label.configure(text="Bilgiler alınıyor...")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        threading.Thread(target=self.fetch_info_thread, args=(url,), daemon=True).start()

    def fetch_info_thread(self, url):
        ydl_opts = {'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.video_info = info
                self.after(0, self.update_ui_with_info, info)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Hata", f"Bilgi çekilemedi:\n{e}"))
            self.after(0, lambda: self.status_label.configure(text="Hata oluştu"))
        finally:
            self.after(0, self.reset_fetch_ui)

    def reset_fetch_ui(self):
        self.fetch_btn.configure(state="normal", text="Bilgileri Çek")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)

    def update_ui_with_info(self, info):
        # Update text
        self.title_label.configure(text=info.get('title', 'Başlık Yok'))
        duration = info.get('duration_string', '??:??')
        view_count = info.get('view_count', 0)
        self.meta_label.configure(text=f"Süre: {duration} | İzlenme: {view_count:,}")
        self.status_label.configure(text="Video bulundu.")
        self.download_btn.configure(state="normal")

        # Update Thumbnail
        thumb_url = info.get('thumbnail')
        if thumb_url:
            self.load_thumbnail(thumb_url)
        
        self.update_format_options()

    def load_thumbnail(self, url):
        try:
            response = requests.get(url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            
            # Resize keeping aspect ratio (target width ~400)
            base_width = 400
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(base_width, h_size))
            self.thumbnail_label.configure(image=ctk_img, text="")
        except Exception as e:
            print(f"Thumbnail load error: {e}")

    def update_format_options(self):
        if not self.video_info:
            return

        dl_type = self.type_var.get()
        if dl_type == "audio":
            self.format_menu.configure(values=["MP3 (En İyi Kalite)"])
            self.format_var.set("MP3 (En İyi Kalite)")
        else:
            formats = self.video_info.get('formats', [])
            # Extract unique resolutions
            seen_res = set()
            valid_formats = []
            
            # Helper to get height
            def get_height(f):
                h = f.get('height')
                return h if h else 0

            # Pre-sort by height descending
            formats.sort(key=get_height, reverse=True)

            for f in formats:
                if f.get('vcodec') != 'none':
                    h = f.get('height')
                    if h and h not in seen_res:
                        seen_res.add(h)
                        # We store the height as value
                        valid_formats.append(f"{h}p")
            
            if not valid_formats:
                valid_formats = ["Best Available"]

            self.format_menu.configure(values=valid_formats)
            self.format_var.set(valid_formats[0])

    def start_download(self):
        if not self.video_info:
            return
        
        self.download_btn.configure(state="disabled", text="İndiriliyor...")
        self.status_label.configure(text="İndirme başlatılıyor...")
        
        url = self.url_entry.get().strip()
        type_choice = self.type_var.get()
        fmt_choice = self.format_var.get()  # e.g., "1080p" or "MP3..."

        threading.Thread(
            target=self.download_thread, 
            args=(url, type_choice, fmt_choice), 
            daemon=True
        ).start()

    def download_thread(self, url, dl_type, fmt_string):
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    p = 0
                    if d.get('total_bytes'):
                        p = d['downloaded_bytes'] / d['total_bytes']
                    elif d.get('total_bytes_estimate'):
                        p = d['downloaded_bytes'] / d['total_bytes_estimate']
                    
                    # Convert to reasonable float 0.0 - 1.0
                    self.after(0, lambda: self.progress_bar.set(p))
                    
                    percent_str = f"{p*100:.1f}%"
                    self.after(0, lambda: self.status_label.configure(text=f"İndiriliyor: {percent_str}"))
                except Exception as e:
                    print(f"Progress Error: {e}")
            elif d['status'] == 'finished':
                self.after(0, lambda: self.status_label.configure(text="İşleniyor/Tamamlandı..."))
                self.after(0, lambda: self.progress_bar.set(1))

        ydl_opts = {
            'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True
        }

        if dl_type == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Video
            if "p" in fmt_string:
                height = fmt_string.replace('p', '')
                # Download best video with specific height + best audio
                ydl_opts['format'] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            else:
                ydl_opts['format'] = "bestvideo+bestaudio/best"
            
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: messagebox.showinfo("Başarılı", "İndirme Tamamlandı!"))
            self.after(0, lambda: self.status_label.configure(text=f"Tamamlandı: {self.download_folder}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Hata", f"İndirme başarısız:\n{e}"))
        finally:
            self.after(0, self.reset_download_ui)

    def reset_download_ui(self):
        self.download_btn.configure(state="normal", text="İNDİR")
        self.progress_bar.set(0)

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
