import os
import json

def generate_dashboard(url_mapping, output_dir):
    """
    Generates a premium index.html search portal linking to all archived articles.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Categorize the articles
    categories = {
        "case-studies": {"name": "Case Studies", "articles": [], "color": "#3b82f6", "bg": "#eff6ff"},
        "fundamentals": {"name": "Fundamentals", "articles": [], "color": "#10b981", "bg": "#ecfdf5"},
        "interview": {"name": "Interview Prep", "articles": [], "color": "#f59e0b", "bg": "#fffbeb"},
        "ai-engineering": {"name": "AI Engineering", "articles": [], "color": "#8b5cf6", "bg": "#f5f3ff"},
        "white-papers": {"name": "White Papers", "articles": [], "color": "#ec4899", "bg": "#fdf2f8"}
    }
    
    total_articles = 0
    for url, info in url_mapping.items():
        cat = info["category"]
        if cat in categories:
            categories[cat]["articles"].append(info)
            total_articles += 1
            
    # Write CSS stylesheet
    css_content = """
    :root {
        --primary: #4f46e5;
        --primary-hover: #4338ca;
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
    }

    body {
        margin: 0;
        font-family: 'Outfit', 'Inter', -apple-system, sans-serif;
        background-color: var(--bg-main);
        color: var(--text-main);
        line-height: 1.5;
    }

    /* Header Layout */
    .header {
        background: linear-gradient(135deg, #1e1b4b 0%, #311042 50%, #4338ca 100%);
        color: white;
        padding: 50px 20px;
        text-align: center;
        position: relative;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }

    .header-content {
        max-width: 800px;
        margin: 0 auto;
    }

    .header h1 {
        margin: 0 0 10px 0;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.025em;
    }

    .header p {
        margin: 0 0 30px 0;
        font-size: 1.15rem;
        color: #c7d2fe;
    }

    /* Stats Grid */
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }

    .stat-badge {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 0.9rem;
        font-weight: 600;
        color: white;
    }

    /* Search Container */
    .search-wrapper {
        position: relative;
        max-width: 600px;
        margin: 0 auto;
    }

    .search-input {
        width: 100%;
        padding: 16px 24px 16px 56px;
        font-size: 1.1rem;
        border-radius: 50px;
        border: none;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        outline: none;
        box-sizing: border-box;
        transition: all 0.2s ease;
        font-family: inherit;
    }

    .search-input:focus {
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.3);
        transform: scale(1.02);
    }

    .search-icon {
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--text-muted);
        width: 24px;
        height: 24px;
    }

    /* Main Container */
    .main-container {
        display: grid;
        grid-template-columns: 280px 1fr;
        gap: 30px;
        max-width: 1400px;
        margin: 40px auto;
        padding: 0 20px;
    }

    @media (max-width: 900px) {
        .main-container {
            grid-template-columns: 1fr;
        }
    }

    /* Category Navigation */
    .sidebar {
        background: var(--bg-card);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        height: fit-content;
        position: sticky;
        top: 20px;
    }

    .sidebar h2 {
        margin-top: 0;
        font-size: 1.1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 20px;
    }

    .cat-btn {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        padding: 12px 16px;
        margin-bottom: 8px;
        background: transparent;
        border: none;
        border-radius: 8px;
        text-align: left;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-main);
        cursor: pointer;
        transition: all 0.2s;
        box-sizing: border-box;
    }

    .cat-btn:hover {
        background: #f1f5f9;
    }

    .cat-btn.active {
        background: var(--primary);
        color: white;
    }

    .cat-count {
        font-size: 0.8rem;
        background: #e2e8f0;
        color: var(--text-muted);
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 700;
    }

    .cat-btn.active .cat-count {
        background: rgba(255,255,255,0.2);
        color: white;
    }

    /* Cards Grid */
    .cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
    }

    .article-card {
        background: var(--bg-card);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        padding: 24px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-decoration: none;
        color: inherit;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    .article-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.06);
        border-color: var(--primary);
    }

    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0 0 16px 0;
        line-height: 1.4;
        color: var(--text-main);
    }

    .card-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: auto;
    }

    .badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }

    .offline-indicator {
        display: flex;
        align-items: center;
        font-size: 0.8rem;
        color: #10b981;
        font-weight: 600;
        gap: 4px;
    }

    .no-results {
        grid-column: 1 / -1;
        text-align: center;
        padding: 80px 20px;
        color: var(--text-muted);
    }

    .no-results svg {
        width: 64px;
        height: 64px;
        margin-bottom: 16px;
        color: #cbd5e1;
    }

    .no-results h3 {
        margin: 0 0 8px 0;
        color: var(--text-main);
    }
    """
    
    # Save CSS to directory
    assets_css_dir = os.path.join(output_dir, "assets", "css")
    os.makedirs(assets_css_dir, exist_ok=True)
    with open(os.path.join(assets_css_dir, "dashboard.css"), "w", encoding="utf-8") as f:
        f.write(css_content)
        
    # Build Articles Cards JSON structure to embed in JS for fast live search
    articles_data = []
    for cat_id, cat_info in categories.items():
        for article in cat_info["articles"]:
            articles_data.append({
                "title": article["title"],
                "category": cat_id,
                "category_name": cat_info["name"],
                "filename": f"./{cat_id}/{article['filename']}",
                "color": cat_info["color"],
                "bg": cat_info["bg"]
            })
            
    # Build Sidebar Categories HTML
    sidebar_html = """
    <button class="cat-btn active" onclick="filterCategory('all', this)">
        <span>🌐 All Categories</span>
        <span class="cat-count">{}</span>
    </button>
    """.format(total_articles)
    
    for cat_id, cat_info in categories.items():
        sidebar_html += f"""
        <button class="cat-btn" onclick="filterCategory('{cat_id}', this)">
            <span>• {cat_info['name']}</span>
            <span class="cat-count">{len(cat_info['articles'])}</span>
        </button>
        """
        
    # Write HTML dashboard template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Design Academy — Offline Archive</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="./assets/css/dashboard.css">
</head>
<body>

    <!-- Header Section -->
    <header class="header">
        <div class="header-content">
            <h1>System Design Academy</h1>
            <p>Offline Reference Library & Learning Portal</p>
            
            <div class="stats-container">
                <span class="stat-badge">📚 {total_articles} Unique Articles</span>
                <span class="stat-badge">⚡ 163 Substack Newsletter</span>
                <span class="stat-badge">📝 19 Core Blog Posts</span>
                <span class="stat-badge">🟢 100% Offline Ready</span>
            </div>
            
            <div class="search-wrapper">
                <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.3-4.3"></path>
                </svg>
                <input type="text" id="search-bar" class="search-input" placeholder="Search 182 system design articles, companies, concepts..." oninput="handleSearch()">
            </div>
        </div>
    </header>

    <!-- Main Content Container -->
    <div class="main-container">
        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <h2>Categories</h2>
            <nav id="category-nav">
                {sidebar_html}
            </nav>
        </aside>

        <!-- Articles Grid -->
        <main>
            <div id="articles-grid" class="cards-grid">
                <!-- Javascript will render articles here -->
            </div>
        </main>
    </div>

    <script>
        // Inline articles payload
        const articles = {json.dumps(articles_data)};
        
        let activeCategory = 'all';
        let searchQuery = '';

        function renderArticles() {{
            const grid = document.getElementById('articles-grid');
            grid.innerHTML = '';
            
            const filtered = articles.filter(art => {{
                const matchesCategory = activeCategory === 'all' || art.category === activeCategory;
                const matchesSearch = art.title.toLowerCase().includes(searchQuery.toLowerCase());
                return matchesCategory && matchesSearch;
            }});

            if (filtered.length === 0) {{
                grid.innerHTML = `
                    <div class="no-results">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h3>No articles found</h3>
                        <p>Try adjusting your search keywords or category filters.</p>
                    </div>
                `;
                return;
            }}

            filtered.forEach(art => {{
                const card = document.createElement('a');
                card.className = 'article-card';
                card.href = art.filename;
                
                card.innerHTML = `
                    <h3 class="card-title">${{art.title}}</h3>
                    <div class="card-meta">
                        <span class="badge" style="background-color: ${{art.bg}}; color: ${{art.color}}">${{art.category_name}}</span>
                        <span class="offline-indicator">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: middle;">
                                <path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v13.5a.5.5 0 0 1-.777.416L8 13.101l-5.223 2.815A.5.5 0 0 1 2 15.5V2zm2-1a1 1 0 0 0-1 1v12.566l4.723-2.545a.5.5 0 0 1 .554 0L13 14.566V2a1 1 0 0 0-1-1H4z"/>
                            </svg>
                            Offline
                        </span>
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        function filterCategory(catId, btnEl) {{
            activeCategory = catId;
            
            // Manage active button class
            const buttons = document.querySelectorAll('.cat-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            btnEl.classList.add('active');
            
            renderArticles();
        }}

        function handleSearch() {{
            searchQuery = document.getElementById('search-bar').value;
            renderArticles();
        }}

        // Initial render on page load
        window.addEventListener('DOMContentLoaded', () => {{
            renderArticles();
        }});
    </script>
</body>
</html>
"""
    
    # Save index.html
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Generated search portal dashboard at: {os.path.join(output_dir, 'index.html')}")

if __name__ == '__main__':
    # Test script harness
    from archive_downloader import parse_readme, README_PATH, ARCHIVE_DIR
    mapping = parse_readme(README_PATH)
    generate_dashboard(mapping, ARCHIVE_DIR)
