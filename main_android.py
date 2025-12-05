import flet as ft
import yt_dlp
import os
import certifi

# SSL Fix
os.environ['SSL_CERT_FILE'] = certifi.where()

def main(page: ft.Page):
    # App Settings
    page.title = "YouTube İndirici"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0F0F0F"  # Deep Black
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    # Data
    video_info = {}
    download_dir = "/storage/emulated/0/Download" # Android default
    # For testing on Desktop, fallback to home downloads
    if not os.path.exists(download_dir):
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    # --- UI Elements ---
    
    # Header
    header = ft.Column(
        controls=[
            ft.Text("YouTube İndirme Aracı", size=28, weight=ft.FontWeight.BOLD, color="#E50914"),
            ft.Text("byPhurki", size=12, color="#AAAAAA")
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Input
    url_input = ft.TextField(
        label="Video Bağlantısı",
        hint_text="https://youtu.be/...",
        border_color="#333333",
        bgcolor="#2A2A2A",
        color="white"
    )

    def fetch_info_click(e):
        url = url_input.value
        if not url: return

        fetch_btn.disabled = True
        status_text.value = "Bilgiler alınıyor..."
        progress_bar.visible = True
        page.update()

        try:
            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_info.update(info)
                
                # Update UI
                title_text.value = info.get('title', 'Başlık Yok')
                meta_text.value = f"Süre: {info.get('duration_string')} • İzlenme: {info.get('view_count')}"
                thumb_img.src = info.get('thumbnail')
                thumb_img.visible = True
                
                # Parse Formats
                formats = info.get('formats', [])
                seen_res = set()
                valid_formats = []
                
                def get_height(f):
                    h = f.get('height')
                    return h if h else 0

                formats.sort(key=get_height, reverse=True)

                for f in formats:
                    if f.get('vcodec') != 'none':
                        h = f.get('height')
                        if h and h not in seen_res:
                            seen_res.add(h)
                            valid_formats.append(h)
                
                format_dropdown.options = []
                if valid_formats:
                    for h in valid_formats:
                        format_dropdown.options.append(ft.dropdown.Option(str(h), f"{h}p"))
                    format_dropdown.value = str(valid_formats[0])
                    format_dropdown.disabled = False
                else:
                    format_dropdown.options.append(ft.dropdown.Option("best", "En İyi"))
                    format_dropdown.value = "best"

                if type_dropdown.value == "audio":
                     format_dropdown.disabled = True

                download_btn.disabled = False
                status_text.value = "Video hazır."
                
        except Exception as err:
            status_text.value = f"Hata: {err}"
        
        fetch_btn.disabled = False
        progress_bar.visible = False
        page.update()

    fetch_btn = ft.ElevatedButton(
        "BİLGİLERİ GETİR", 
        on_click=fetch_info_click,
        bgcolor="#E50914",
        color="white",
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    # Video Info Display
    thumb_img = ft.Image(src="", width=400, height=220, fit=ft.ImageFit.COVER, border_radius=10, visible=False)
    title_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    meta_text = ft.Text("", size=12, color="#AAAAAA")

    # Options
    type_dropdown = ft.Dropdown(
        label="Tür",
        value="video",
        options=[
            ft.dropdown.Option("video", "Video (MP4)"),
            ft.dropdown.Option("audio", "Ses (MP3)"),
        ],
        bgcolor="#2A2A2A",
        border_color="#333333",
        color="white",
        on_change=lambda e: update_format_visibility(e)
    )

    format_dropdown = ft.Dropdown(
        label="Kalite",
        options=[],
        bgcolor="#2A2A2A",
        border_color="#333333",
        color="white",
        disabled=True
    )

    def update_format_visibility(e):
        if type_dropdown.value == "audio":
            format_dropdown.disabled = True
            format_dropdown.value = None
        else:
            format_dropdown.disabled = False
            if format_dropdown.options:
                format_dropdown.value = format_dropdown.options[0].key
        page.update()

    # Progress
    progress_bar = ft.ProgressBar(width=400, color="#E50914", visible=False)
    status_text = ft.Text("Hazır", color="#AAAAAA")

    def download_click(e):
        if not video_info: return
        
        download_btn.disabled = True
        status_text.value = "İndirme başlatılıyor..."
        progress_bar.visible = True
        progress_bar.value = None # Indeterminate
        page.update()

        url = url_input.value
        dl_type = type_dropdown.value
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                if d.get('total_bytes'):
                    p = d['downloaded_bytes'] / d['total_bytes']
                    progress_bar.value = p
                    status_text.value = f"İndiriliyor: {p*100:.1f}%"
                    page.update()
            elif d['status'] == 'finished':
                status_text.value = "İşleniyor..."
                page.update()

        ydl_opts = {
            'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'quiet': True
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
            quality = format_dropdown.value
            if quality and quality != "best":
                ydl_opts['format'] = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"
            else:
                ydl_opts['format'] = "bestvideo+bestaudio/best"
            
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            status_text.value = f"İndirme Tamamlandı!\nKayıt yeri: {download_dir}"
            progress_bar.value = 1
        except Exception as err:
            status_text.value = f"Hata: {err}"

        download_btn.disabled = False
        page.update()

    download_btn = ft.ElevatedButton(
        "İNDİRMEYİ BAŞLAT",
        on_click=download_click,
        bgcolor="#E50914",
        color="white",
        height=55,
        width=250,
        disabled=True
    )

    # Layout
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Divider(color="transparent", height=20),
                    url_input,
                    fetch_btn,
                    ft.Divider(color="transparent", height=20),
                    thumb_img,
                    title_text,
                    meta_text,
                    ft.Divider(color="transparent", height=20),
                    type_dropdown,
                    format_dropdown,
                    ft.Divider(color="transparent", height=20),
                    progress_bar,
                    status_text,
                    ft.Divider(color="transparent", height=20),
                    download_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20
        )
    )

ft.app(target=main)
