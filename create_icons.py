import os
import subprocess
from PIL import Image

def create_icons(source_path):
    img = Image.open(source_path)
    
    # 1. Create Windows ICO
    img.save("app_icon.ico", format='ICO', sizes=[(256, 256)])
    print("Created app_icon.ico")

    # 2. Create macOS Iconset
    iconset_dir = "YouTubeDownloader.iconset"
    if not os.path.exists(iconset_dir):
        os.makedirs(iconset_dir)

    sizes = [16, 32, 128, 256, 512]
    
    for size in sizes:
        # Standard resolution
        resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
        resized_img.save(os.path.join(iconset_dir, f"icon_{size}x{size}.png"))
        
        # High resolution (@2x)
        double_size = size * 2
        resized_img_2x = img.resize((double_size, double_size), Image.Resampling.LANCZOS)
        resized_img_2x.save(os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png"))

    print("Created iconset images.")

    # 3. Convert iconset to ICNS using iconutil
    try:
        subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", "YouTubeDownloader.icns"], check=True)
        print("Created YouTubeDownloader.icns")
    except subprocess.CalledProcessError as e:
        print(f"Error creating ICNS: {e}")

if __name__ == "__main__":
    create_icons("app_icon.png")
