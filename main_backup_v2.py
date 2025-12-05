import customtkinter as ctk
import yt_dlp
import threading
import os
import shutil
import certifi
import requests
from PIL import Image, ImageTk
from io import BytesIO
from tkinter import filedialog, messagebox

# macOS SSL sertifika doğrulama hatası için düzeltme
os.environ['SSL_CERT_FILE'] = certifi.where()

# Tema Ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue") 

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere Kurulumu
        self.title("YouTube İndirme Aracı")
        self.geometry("850x800")
        self.resizable(True, True)

        # Premium Renk Paleti
        self.bg_color = "#0F0F0F"       # En Koyu Siyah
        self.card_color = "#1E1E1E"     # Kartlar için Koyu Gri
        self.accent_color = "#E50914"   # Netflix/Premium Kırmızısı
        self.accent_hover = "#B20710"   # Daha Koyu Kırmızı
        self.text_color = "#FFFFFF"     # Saf Beyaz
        self.sub_text = "#AAAAAA"       # Açık Gri
        
        # Pencere Arka Planını Ayarla
        self.configure(fg_color=self.bg_color)

        # Premium Yazı Tipi Ayarları
        self.font_header = ("Helvetica", 28, "bold")
        self.font_main = ("Helvetica", 16)
        self.font_button = ("Helvetica", 14, "bold")
        self.font_sub = ("Helvetica", 12)

        # Veri Değişkenleri
        self.video_info = None
        self.download_folder = os.path.expanduser("~/Downloads")

        self.create_widgets()

    def create_widgets(self):
        # --- Üst Bilgi (Header) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(30, 10))

        self.logo_label = ctk.CTkLabel(
            self.header_frame, 
            text="YouTube İndirme Aracı", 
            font=self.font_header,
            text_color=self.accent_color
        )
        self.logo_label.pack()

        self.credit_label = ctk.CTkLabel(
            self.header_frame,
            text="byPhurki",
            font=self.font_sub,
            text_color=self.sub_text
        )
        self.credit_label.pack(pady=(2, 10))

        # --- Giriş Bölümü (Kart Stili) ---
        self.input_frame = ctk.CTkFrame(self, fg_color=self.card_color, corner_radius=15)
        self.input_frame.pack(fill="x", padx=30, pady=10)

        self.url_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Video bağlantısını buraya yapıştırın...",
            height=50,
            font=self.font_main,
            border_width=0,
            fg_color="#2A2A2A",
            text_color="white"
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(20, 15), pady=20)

        self.fetch_btn = ctk.CTkButton(
            self.input_frame, 
            text="BİLGİLERİ GETİR", 
            command=self.start_fetch_info,
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            height=50,
            width=150,
            font=self.font_button,
            corner_radius=10
        )
        self.fetch_btn.pack(side="right", padx=(0, 20), pady=20)

        # --- Bilgi Bölümü (Temiz görünüm için şeffaf) ---
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Kapak Resmi Yer Tutucusu
        self.thumbnail_label = ctk.CTkLabel(
            self.info_frame, 
            text="", 
            height=220, 
            corner_radius=15, 
            fg_color="#1a1a1a"
        )
        self.thumbnail_label.pack(fill="x", pady=(0, 15))

        self.title_label = ctk.CTkLabel(
            self.info_frame, 
            text="İndirilecek videoyu bekliyorum...", 
            font=("Helvetica", 18, "bold"),
            text_color=self.text_color,
            wraplength=750
        )
        self.title_label.pack()

        self.meta_label = ctk.CTkLabel(
            self.info_frame, 
            text="", 
            font=self.font_sub,
            text_color=self.sub_text
        )
        self.meta_label.pack(pady=(5,0))

        # --- Seçenekler Bölümü (Kart Stili) ---
        self.options_frame = ctk.CTkFrame(self, fg_color=self.card_color, corner_radius=15)
        self.options_frame.pack(fill="x", padx=30, pady=10)

        # Tür Seçimi
        self.type_var = ctk.StringVar(value="video")
        
        self.radio_video = ctk.CTkRadioButton(
            self.options_frame, text="Video", variable=self.type_var, value="video", 
            fg_color=self.accent_color, hover_color=self.accent_hover, 
            font=self.font_main, text_color=self.text_color,
            command=self.update_format_options
        )
        self.radio_video.pack(side="left", padx=(30, 20), pady=25)

        self.radio_audio = ctk.CTkRadioButton(
            self.options_frame, text="Ses (MP3)", variable=self.type_var, value="audio", 
            fg_color=self.accent_color, hover_color=self.accent_hover,
            font=self.font_main, text_color=self.text_color,
            command=self.update_format_options
        )
        self.radio_audio.pack(side="left", padx=20, pady=25)

        # Format Açılır Menüsü
        self.format_var = ctk.StringVar(value="Format Seçiniz")
        self.format_menu = ctk.CTkOptionMenu(
            self.options_frame, 
            variable=self.format_var,
            fg_color="#2A2A2A",
            button_color="#333",
            button_hover_color="#444", 
            text_color="white",
            font=self.font_main,
            width=180,
            height=35
        )
        self.format_menu.pack(side="left", padx=30, pady=25)

        # Klasör Seçimi
        self.folder_btn = ctk.CTkButton(
            self.options_frame, 
            text="KONUM SEÇ", 
            command=self.select_folder,
            fg_color="#333",
            hover_color="#444",
            font=("Helvetica", 12, "bold"),
            height=35,
            width=120
        )
        self.folder_btn.pack(side="right", padx=30, pady=25)

        # --- Durum ve İşlemler ---
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=30, pady=(10, 30))

        self.progress_bar = ctk.CTkProgressBar(
            self.status_frame, 
            orientation="horizontal", 
            progress_color=self.accent_color,
            height=15
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 15))

        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="Hazır", 
            text_color=self.sub_text,
            font=self.font_sub
        )
        self.status_label.pack(side="left")

        self.download_btn = ctk.CTkButton(
            self.status_frame, 
            text="İNDİRMEYİ BAŞLAT", 
            command=self.start_download,
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            height=55,
            width=200,
            font=("Helvetica", 16, "bold"),
            corner_radius=25,
            state="disabled"
        )
        self.download_btn.pack(side="right")

    # --- Mantık İşlemleri ---

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            # Görüntüleme için yolu kısalt
            display_path = os.path.basename(folder)
            if not display_path: display_path = folder
            self.status_label.configure(text=f"Konum: .../{display_path}")

    def start_fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        
        self.fetch_btn.configure(state="disabled", text="...")
        self.status_label.configure(text="Video bilgileri alınıyor...")
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
            self.after(0, lambda: messagebox.showerror("Hata", f"Hata:\n{e}"))
            self.after(0, lambda: self.status_label.configure(text="Hata oluştu"))
        finally:
            self.after(0, self.reset_fetch_ui)

    def reset_fetch_ui(self):
        self.fetch_btn.configure(state="normal", text="BİLGİLERİ GETİR")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)

    def update_ui_with_info(self, info):
        self.title_label.configure(text=info.get('title', 'Başlık Yok'))
        duration = info.get('duration_string', '??:??')
        view_count = info.get('view_count', 0)
        self.meta_label.configure(text=f"Süre: {duration}  •  İzlenme: {view_count:,}")
        self.status_label.configure(text="Video hazır.")
        self.download_btn.configure(state="normal")

        thumb_url = info.get('thumbnail')
        if thumb_url:
            self.load_thumbnail(thumb_url)
        
        self.update_format_options()

    def load_thumbnail(self, url):
        try:
            response = requests.get(url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            
            # Premium Düzen: Eğer mümkünse daha büyük kapak resmi
            target_h = 220
            w_percent = (target_h / float(img.size[1]))
            w_size = int((float(img.size[0]) * float(w_percent)))
            
            img = img.resize((w_size, target_h), Image.Resampling.LANCZOS)
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w_size, target_h))
            self.thumbnail_label.configure(image=ctk_img, text="")
        except Exception as e:
            print(f"Thumb error: {e}")

    def update_format_options(self):
        if not self.video_info:
            return

        dl_type = self.type_var.get()
        if dl_type == "audio":
            self.format_menu.configure(values=["MP3 (Yüksek Kalite)"])
            self.format_var.set("MP3 (Yüksek Kalite)")
        else:
            formats = self.video_info.get('formats', [])
            seen_res = set()
            valid_formats = []
            
            # Yükseklik bilgisini almak için yardımcı fonksiyon
            def get_height(f):
                h = f.get('height')
                return h if h else 0

            # Yüksekliğe göre azalan şekilde sırala
            formats.sort(key=get_height, reverse=True)

            for f in formats:
                if f.get('vcodec') != 'none':
                    h = f.get('height')
                    if h and h not in seen_res:
                        seen_res.add(h)
                        valid_formats.append(f"{h}p")
            
            if not valid_formats:
                valid_formats = ["En İyi Kalite"]

            self.format_menu.configure(values=valid_formats)
            self.format_var.set(valid_formats[0])

    def start_download(self):
        if not self.video_info:
            return
        
        self.download_btn.configure(state="disabled", text="İNDİRİLİYOR...", fg_color="#333")
        self.status_label.configure(text="İndirme başlatılıyor...")
        
        url = self.url_entry.get().strip()
        type_choice = self.type_var.get()
        fmt_choice = self.format_var.get()

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
                    
                    self.after(0, lambda: self.progress_bar.set(p))
                    percent_str = f"{p*100:.1f}%"
                    self.after(0, lambda: self.status_label.configure(text=f"İndiriliyor: {percent_str}"))
                except Exception:
                    pass
            elif d['status'] == 'finished':
                self.after(0, lambda: self.status_label.configure(text="Birleştiriliyor..."))
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
            if "p" in fmt_string:
                height = fmt_string.replace('p', '')
                ydl_opts['format'] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            else:
                ydl_opts['format'] = "bestvideo+bestaudio/best"
            
            ydl_opts['merge_output_format'] = 'mp4'

        # FFmpeg yolunu manuel olarak ekle (Mac uygulaması için gerekli)
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: messagebox.showinfo("Başarılı", "İndirme Tamamlandı!"))
            self.after(0, lambda: self.status_label.configure(text="İşlem Başarılı."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Hata", f"İndirme başarısız:\n{e}"))
        finally:
            self.after(0, self.reset_download_ui)

    def get_ffmpeg_path(self):
        # 1. Sistem PATH kontrolü
        path = shutil.which('ffmpeg')
        if path: return path
        
        # 2. Yaygın macOS yolları (Homebrew, MacPorts vb.)
        possible_paths = [
            '/opt/homebrew/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/usr/bin/ffmpeg',
            '/bin/ffmpeg'
        ]
        
        for p in possible_paths:
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p
                
        return None

    def reset_download_ui(self):
        self.download_btn.configure(state="normal", text="İNDİRMEYİ BAŞLAT", fg_color=self.accent_color)
        self.progress_bar.set(0)

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
