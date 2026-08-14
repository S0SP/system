import os
from PIL import Image

def compress_image_in_place(filepath):
    """
    Compresses an image file in-place using Pillow.
    Uses palette quantization for PNGs and quality reduction for JPEGs.
    """
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.webp']:
            return False
            
        original_size = os.path.getsize(filepath)
        if original_size < 10240: # Skip very small icons (< 10 KB)
            return False
            
        with Image.open(filepath) as img:
            # Check image format
            if img.format == 'PNG':
                # Convert to palette mode (indexed color) which is perfect for diagrams
                if img.mode != 'P':
                    # Handle transparency
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        # Convert to RGBA, then quantize with alpha support
                        alpha = img.split()[-1]
                        img_rgb = img.convert('RGB')
                        # Quantize the RGB image
                        img_quant = img_rgb.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
                        # We save it back as PNG with optimization
                        img_quant.save(filepath, format='PNG', optimize=True)
                    else:
                        img_quant = img.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
                        img_quant.save(filepath, format='PNG', optimize=True)
                else:
                    img.save(filepath, format='PNG', optimize=True)
            elif img.format in ['JPEG', 'MPO']:
                # Save with quality=75 and optimization
                img.convert('RGB').save(filepath, format='JPEG', quality=75, optimize=True)
            elif img.format == 'WEBP':
                img.save(filepath, format='WEBP', quality=75, method=6)
                
        new_size = os.path.getsize(filepath)
        saved = original_size - new_size
        percent = (saved / original_size) * 100
        if saved > 0:
            print(f"Compressed {os.path.basename(filepath)}: {original_size/1024:.1f}KB -> {new_size/1024:.1f}KB (Saved {saved/1024:.1f}KB, {percent:.1f}%)")
            return True
        return False
    except Exception as e:
        print(f"Error compressing {filepath}: {e}")
        return False

def compress_all_images(images_dir):
    print(f"Scanning images in {images_dir} for compression...")
    total_saved = 0
    count = 0
    
    for filename in os.listdir(images_dir):
        filepath = os.path.join(images_dir, filename)
        if os.path.isfile(filepath):
            original_size = os.path.getsize(filepath)
            if compress_image_in_place(filepath):
                new_size = os.path.getsize(filepath)
                total_saved += (original_size - new_size)
                count += 1
                
    print(f"\nFinished! Compressed {count} images and saved {total_saved / (1024*1024):.2f} MB of space.")

if __name__ == '__main__':
    images_dir = 'd:/wa/neokim/archive/assets/images'
    if os.path.exists(images_dir):
        compress_all_images(images_dir)
    else:
        print("Images directory does not exist.")
