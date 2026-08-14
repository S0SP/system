import os
import re
import urllib.parse
import hashlib
import requests
from bs4 import BeautifulSoup
from PIL import Image

def get_safe_filename(url, prefix="", ext=""):
    """
    Generates a unique, safe filename for any URL based on its hash.
    """
    clean_url = url.split('?')[0]
    # Extract original extension if exists
    orig_ext = os.path.splitext(clean_url)[1]
    if orig_ext and len(orig_ext) <= 5 and re.match(r'^\.[a-zA-Z0-9]+$', orig_ext):
        target_ext = orig_ext
    else:
        target_ext = ext if ext.startswith('.') else f".{ext}" if ext else ""
        
    hash_str = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
    return f"{prefix}{hash_str}{target_ext}"

def download_file(url, output_path):
    """
    Downloads a binary file with connection and read timeouts to prevent hangs.
    """
    if os.path.exists(output_path):
        return True
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Using a timeout tuple (connection timeout, read timeout per chunk)
        response = requests.get(url, headers=headers, timeout=(5, 10), stream=True)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                # Read from raw response stream to enforce socket read timeouts per chunk
                response.raw.decode_content = True
                while True:
                    chunk = response.raw.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
            return True
        else:
            print(f"Failed to download {url}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        # Clean up any partial file if download failed mid-stream
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass
        return False

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
        if original_size < 10240: # Skip small files (< 10 KB)
            return False
            
        with Image.open(filepath) as img:
            if img.format == 'PNG':
                if img.mode != 'P':
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        # Convert to RGB then quantize
                        img_rgb = img.convert('RGB')
                        img_quant = img_rgb.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
                        img_quant.save(filepath, format='PNG', optimize=True)
                    else:
                        img_quant = img.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
                        img_quant.save(filepath, format='PNG', optimize=True)
                else:
                    img.save(filepath, format='PNG', optimize=True)
            elif img.format in ['JPEG', 'MPO']:
                img.convert('RGB').save(filepath, format='JPEG', quality=75, optimize=True)
            elif img.format == 'WEBP':
                img.save(filepath, format='WEBP', quality=75, method=6)
        return True
    except Exception:
        return False

def parse_and_clean_url(url, base_url_context):
    """
    Resolves the URL relative to base_url_context, strips query parameters,
    and returns (clean_base_url, fragment).
    """
    resolved = urllib.parse.urljoin(base_url_context, url).strip()
    
    # Split fragment
    parts = resolved.split('#')
    url_without_frag = parts[0]
    fragment = f"#{parts[1]}" if len(parts) > 1 else ""
    
    # Split query parameters
    url_without_query = url_without_frag.split('?')[0]
    
    # Clean trailing slashes
    clean_base_url = url_without_query.rstrip('/')
    
    return clean_base_url, fragment

def clean_html_content(soup):
    """
    Remove unnecessary tracking scripts, dynamic overlays, cookie consents, and navigation panels.
    """
    # Remove google tag manager, scripts, and trackers
    for tag in soup.find_all(['script', 'noscript', 'iframe']):
        tag.decompose()
        
    # Remove top navigation bars, sign in buttons, and subscribe popups if they aren't part of the content
    for nav in soup.find_all(attrs={"data-testid": "navbar"}):
        nav.decompose()
        
    # Targeted overlay removals (Substack & Ghost overlays)
    for overlay in soup.find_all(class_=re.compile(r'newsletter-overlay|cc-window|cookieconsent|subscribe-widget|subscription-widget|login-button|nav-buttons', re.I)):
        overlay.decompose()
    for overlay in soup.find_all(id=re.compile(r'newsletter-overlay-id', re.I)):
        overlay.decompose()
        
    # Strip hardcoded absolute coordinates and widths from the TOC container so our responsive CSS overrides work
    toc_auto = soup.find(id='toc-auto')
    if toc_auto:
        if toc_auto.get('style'):
            del toc_auto['style']
            
    # Clean body tags (e.g. remove overflow: hidden style lock)
    if soup.body:
        body_style = soup.body.get('style', '')
        if 'overflow' in body_style and 'hidden' in body_style:
            new_style = re.sub(r'overflow\s*:\s*hidden\s*;?', '', body_style).strip()
            if new_style:
                soup.body['style'] = new_style
            else:
                del soup.body['style']
                
    # Remove inline onclick/onload scripts from all tags to prevent local JS errors
    for tag in soup.find_all():
        if tag.get('onload'):
            del tag['onload']
        if tag.get('onclick'):
            del tag['onclick']
            
    return soup

def write_offline_overrides(css_dir):
    """
    Writes the offline_overrides.css file to make TOC and page layouts fully responsive and functional.
    """
    css_content = """
    /* Offline Layout Overrides for Table of Contents (TOC) */
    @media (min-width: 1300px) {
        .container {
            position: relative !important;
        }
        #toc-auto {
            position: fixed !important;
            top: 100px !important;
            left: 50% !important;
            margin-left: 420px !important; /* Perfectly offset to the right of the centered 800px main text */
            width: 280px !important;
            max-width: 280px !important;
            visibility: visible !important;
            display: block !important;
            border-left: 1px solid rgba(0,0,0,0.08) !important;
            padding-left: 15px !important;
            overflow-y: auto !important;
            max-height: calc(100vh - 150px) !important;
            z-index: 10 !important;
        }
        [theme=dark] #toc-auto {
            border-left-color: rgba(255,255,255,0.08) !important;
        }
    }

    @media (max-width: 1300px) {
        #toc-auto {
            display: none !important; /* Hide absolute floating TOC on smaller screens to prevent overlapping content */
        }
    }

    /* Ensure TOC links wrap naturally and do not clip text boundaries */
    .toc-content a {
        white-space: normal !important;
        word-break: break-word !important;
        display: inline-block !important;
        width: 100% !important;
        padding-top: 4px !important;
        padding-bottom: 4px !important;
    }

    /* Standard content width limits for premium layout */
    .page.single {
        max-width: 800px !important;
        margin: 0 auto !important;
    }
    """
    os.makedirs(css_dir, exist_ok=True)
    overrides_file = os.path.join(css_dir, "offline_overrides.css")
    with open(overrides_file, 'w', encoding='utf-8') as f:
        f.write(css_content)

def process_assets(html_content, page_url, base_archive_dir, category_subfolder, urls_mapping):
    """
    Extracts, downloads, and rewrites assets (images, stylesheets) and internal links.
    Returns the modified HTML string.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    soup = clean_html_content(soup)
    
    # Establish local directory paths
    # Output file will be at: base_archive_dir / category_subfolder / <slug>.html
    # Shared assets directories
    assets_rel_path = "../assets" if category_subfolder else "./assets"
    
    images_dir = os.path.join(base_archive_dir, "assets", "images")
    css_dir = os.path.join(base_archive_dir, "assets", "css")
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(css_dir, exist_ok=True)
    
    # Write the offline overrides stylesheet
    write_offline_overrides(css_dir)
    
    # 1. Process Stylesheets (normal & preloads)
    for link in soup.find_all('link'):
        rel = link.get('rel')
        is_css = False
        if rel:
            if isinstance(rel, list):
                is_css = any(r in ['stylesheet', 'preload'] for r in rel) and link.get('as') == 'style' or any('stylesheet' in r for r in rel)
            else:
                is_css = rel in ['stylesheet', 'preload'] and link.get('as') == 'style' or 'stylesheet' in rel
                
        href = link.get('href')
        if href and (is_css or href.split('?')[0].endswith('.css')):
            absolute_css_url = urllib.parse.urljoin(page_url, href)
            css_filename = get_safe_filename(absolute_css_url, prefix="style_", ext=".css")
            css_dest_path = os.path.join(css_dir, css_filename)
            
            # Download file
            download_file(absolute_css_url, css_dest_path)
            
            # Normalize to clean, synchronous stylesheet link
            link['rel'] = 'stylesheet'
            link['href'] = f"{assets_rel_path}/css/{css_filename}"
            if link.get('as'):
                del link['as']
            if link.get('onload'):
                del link['onload']

    # Link the custom offline overrides stylesheet in the head
    if soup.head:
        overrides_tag = soup.new_tag('link', rel='stylesheet', href=f"{assets_rel_path}/css/offline_overrides.css")
        soup.head.append(overrides_tag)

    # 2. Process Images
    for img in soup.find_all('img'):
        src = img.get('data-src') or img.get('src')
        if src:
            absolute_img_url = urllib.parse.urljoin(page_url, src)
            img_filename = get_safe_filename(absolute_img_url, prefix="img_", ext=".png")
            img_dest_path = os.path.join(images_dir, img_filename)
            
            if download_file(absolute_img_url, img_dest_path):
                # Compress the image in-place on the fly
                compress_image_in_place(img_dest_path)
                
                img['src'] = f"{assets_rel_path}/images/{img_filename}"
                if img.get('data-src'):
                    del img['data-src']
                if img.get('srcset'):
                    del img['srcset']
            else:
                img['src'] = absolute_img_url

    # 3. Rewrite internal links
    for a in soup.find_all('a'):
        href = a.get('href')
        if href:
            # Resolve relative context, strip queries/trailing slashes, extract fragment
            clean_base_url, fragment = parse_and_clean_url(href, page_url)
            
            # Check if this base URL is in our scanned list of articles
            if clean_base_url in urls_mapping:
                mapped_info = urls_mapping[clean_base_url]
                mapped_subfolder = mapped_info["category"]
                mapped_filename = mapped_info["filename"]
                
                # Compute relative link based on directories
                if category_subfolder == mapped_subfolder:
                    new_href = f"./{mapped_filename}{fragment}"
                elif category_subfolder and not mapped_subfolder:
                    new_href = f"../{mapped_filename}{fragment}"
                elif not category_subfolder and mapped_subfolder:
                    new_href = f"./{mapped_subfolder}/{mapped_filename}{fragment}"
                else:
                    new_href = f"../{mapped_subfolder}/{mapped_filename}{fragment}"
                    
                a['href'] = new_href
                a['class'] = a.get('class', []) + ['offline-link']
                # Strip blank targets for internal pages
                if a.get('target'):
                    del a['target']
            else:
                # Make external links absolute and open in new tab
                a['href'] = urllib.parse.urljoin(page_url, href)
                a['target'] = '_blank'
                a['rel'] = 'noopener noreferrer'

    # Add offline support styles banner to the top of the body
    banner_html = f"""
    <div style="background-color: #3b82f6; color: white; text-align: center; padding: 10px; font-family: sans-serif; font-size: 14px; position: sticky; top: 0; z-index: 10000; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        💾 <strong>Offline Archive Mode</strong> — You are viewing a local copy of <em>{page_url}</em>. <a href="../index.html" style="color: white; text-decoration: underline; margin-left: 10px; font-weight: bold;">Back to Library Dashboard</a>
    </div>
    """
    if soup.body:
        soup.body.insert(0, BeautifulSoup(banner_html, 'html.parser'))
        
        # Inject inline local JS to support theme switching (Dark/Light mode) without external scripts
        theme_js = """
        <script>
        (function() {
            // Read saved theme preference from local storage
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                document.body.setAttribute('theme', savedTheme);
            }
            
            // Bind click event to all theme-switch buttons (.theme-switch class)
            const switches = document.querySelectorAll('.theme-switch');
            switches.forEach(el => {
                el.setAttribute('href', '#');
                el.removeAttribute('target');
                el.removeAttribute('rel');
                el.addEventListener('click', function(e) {
                    e.preventDefault();
                    const currentTheme = document.body.getAttribute('theme') || 'light';
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    document.body.setAttribute('theme', newTheme);
                    localStorage.setItem('theme', newTheme);
                });
            });
        })();
        </script>
        """
        soup.body.append(BeautifulSoup(theme_js, 'html.parser'))
        
    return str(soup)
