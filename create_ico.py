from PIL import Image
import os

def create_ico_from_png(png_path="ozon_monitor_icon.png", ico_path="ozon_monitor_icon.ico"):
    """Convert PNG to ICO file"""
    try:
        img = Image.open(png_path)

        # ICO format requires specific sizes, let's create multiple sizes
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        img.save(ico_path, format='ICO', sizes=sizes)

        print(f"ICO file created at: {os.path.abspath(ico_path)}")
    except Exception as e:
        print(f"Error creating ICO file: {str(e)}")

if __name__ == "__main__":
    create_ico_from_png()
