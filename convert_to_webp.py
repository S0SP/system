import os
import re
from PIL import Image

def convert_images_to_webp_and_update_html(base_dir):
    images_dir = os.path.join(base_dir, 'assets', 'images')
    if not os.path.exists(images_dir):
        print("Images directory not found.")
        return
        
    print("Step 1: Converting images to WebP...")
    # Map from old filename to new WebP filename
    mapping = {}
    total_original_size = 0
    total_webp_size = 0
    converted_count = 0
    
    for filename in os.listdir(images_dir):
        filepath = os.path.join(images_dir, filename)
        if not os.path.isfile(filepath):
            continue
            
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg']:
            webp_filename = os.path.splitext(filename)[0] + '.webp'
            webp_filepath = os.path.join(images_dir, webp_filename)
            
            try:
                orig_size = os.path.getsize(filepath)
                total_original_size += orig_size
                
                with Image.open(filepath) as img:
                    # Save as webp with quality=75
                    img.save(webp_filepath, format='WEBP', quality=75, method=6)
                    
                webp_size = os.path.getsize(webp_filepath)
                total_webp_size += webp_size
                converted_count += 1
                
                mapping[filename] = webp_filename
                # Delete the original PNG/JPG file
                os.remove(filepath)
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        elif ext == '.webp':
            total_webp_size += os.path.getsize(filepath)
            total_original_size += os.path.getsize(filepath)
            
    print(f"Converted {converted_count} images to WebP.")
    print(f"Original size: {total_original_size / (1024*1024):.2f} MB")
    print(f"WebP size: {total_webp_size / (1024*1024):.2f} MB")
    saved_mb = (total_original_size - total_webp_size) / (1024*1024)
    print(f"Space saved: {saved_mb:.2f} MB")
    
    print("\nStep 2: Updating HTML files to reference .webp extensions...")
    html_count = 0
    # We will search for all html files in base_dir
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Let's replace any occurrences of old image filenames with webp
                    new_content = content
                    replaced = False
                    
                    # We can use regex to find all img tags or assets/images/... references
                    # e.g. assets/images/img_xxx.png
                    # Let's do a simple replacement for all keys in mapping
                    for old_name, new_name in mapping.items():
                        if old_name in new_content:
                            new_content = new_content.replace(old_name, new_name)
                            replaced = True
                            
                    if replaced:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        html_count += 1
                except Exception as e:
                    print(f"Error updating HTML {file}: {e}")
                    
    print(f"Updated image references in {html_count} HTML files.")

if __name__ == '__main__':
    base_dir = 'd:/wa/neokim/archive'
    convert_images_to_webp_and_update_html(base_dir)
