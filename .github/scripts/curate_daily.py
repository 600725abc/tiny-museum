import os
import re
import sys
import datetime

import json
from pathlib import Path
POOL = json.loads(Path('automation/catalog.json').read_text(encoding='utf-8'))

def generate_exhibit_image(title, prompt_desc, filename, room=""):
    from pathlib import Path
    from PIL import Image
    path = Path("images") / filename.replace(".html", ".jpg")
    with Image.open(path) as image:
        image.verify()
    return path.as_posix()

def checked_sub(pattern, replacement, content, flags=0):
    updated, count = re.subn(pattern, replacement, content, flags=flags)
    if count != 1:
        raise ValueError("Expected one match for template pattern: " + pattern)
    return updated

def run(target_room=None):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if not target_room and len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--room="):
                target_room = arg.split("=", 1)[1]
            elif not arg.startswith("-"):
                target_room = arg

    # 1. Pick first object not yet in repo
    selected = None
    for item in POOL:
        if target_room and item["room"].lower() != target_room.lower():
            continue
        if not os.path.exists(item["filename"]):
            selected = item
            break
            
    if not selected:
        print("All pool exhibits have already been added.")
        return False

    selected = dict(selected)
    import html
    selected["title"] = html.escape(selected["title"], quote=True)
    selected["card_preview"] = html.escape(selected["card_preview"], quote=True)

    print(f"Adding new exhibit: {selected['title']}")

    # 2. Generate Image with GPT Image 2.6 (if API key is present or local file exists)
    image_path = generate_exhibit_image(selected['title'], selected['card_preview'], selected['filename'], selected['room'])
    image_tag = f"""\n        <div class="exhibit-image">\n          <img src="{image_path}" alt="{selected['title']}">\n        </div>""" if image_path else ""

    source = selected.get("source", "Tiny Museum fictional collection")
    import html
    source_note = '<p class="source-note">AI-generated illustration. Acquired refers to the digital collection. Source: ' + html.escape(source) + '</p>'
    # 3. Create the exhibit HTML file
    kitchen_active = ' class="active"' if selected['room'] == 'kitchen' else ''
    desk_active = ' class="active"' if selected['room'] == 'desk' else ''
    garage_active = ' class="active"' if selected['room'] == 'garage' else ''

    exhibit_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{selected['title']} — Tiny Museum of Everyday Objects</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header>
    <a href="index.html" class="site-title">Tiny Museum of Everyday Objects</a>
    <p class="tagline">Welcome to a quiet celebration of the simple tools and artifacts that quietly shape our days.</p>
    <nav>
      <a href="index.html">Home</a>
      <a href="kitchen.html"{kitchen_active}>Kitchen</a>
      <a href="desk.html"{desk_active}>Desk</a>
      <a href="garage.html"{garage_active}>Garage</a>
    </nav>
  </header>

  <main>
    <div class="exhibit-container">
      <article class="museum-plaque">
        <header class="plaque-header">
          <span class="plaque-year">Acquired {selected['year']}</span>
          <h1 class="plaque-title">{selected['title']}</h1>
          <p class="plaque-room">{selected['catalog']}</p>
        </header>{image_tag}

        <div class="museum-label">
          <p>{selected['label']}</p>
        </div>

        <div class="fun-fact-box">
          <div class="fun-fact-title">Curator's Note &bull; Fun Fact</div>
          <p class="fun-fact-text">{selected['fun_fact']}</p>
        </div>
        {source_note}
      </article>

      <a href="{selected['room']}.html" class="back-link">&larr; Back to {selected['room_name']}</a>
    </div>
  </main>

  <footer>
    <p>Tiny Museum of Everyday Objects &copy; 2026</p>
  </footer>
</body>
</html>
"""
    with open(selected["filename"], "w", encoding="utf-8") as f:
        f.write(exhibit_html)

    # 4. Update room gallery HTML (prepend to gallery-grid so newest items appear at the very front)
    room_file = f"{selected['room']}.html"
    if os.path.exists(room_file):
        with open(room_file, "r", encoding="utf-8") as f:
            room_content = f.read()

        card_snippet = f"""      <a href="{selected['filename']}" class="object-card">
        <span class="card-year">Acquired {selected['year']}</span>
        <h3 class="card-title">{selected['title']}</h3>
        <p class="card-preview">{selected['card_preview']}</p>
        <span class="card-action">View Exhibit &rarr;</span>
      </a>\n\n"""

        marker = '<div class="gallery-grid">\n'
        if room_content.count(marker) != 1:
            raise ValueError("Room marker missing or duplicated")
        if marker in room_content:
            room_content = room_content.replace(marker, marker + card_snippet, 1)
        with open(room_file, "w", encoding="utf-8") as f:
            f.write(room_content)

    # 5. Update index.html Object of the Day
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            index_content = f.read()

        img_daily_tag = f"""\n        <div class="exhibit-image">\n          <img src="{image_path}" alt="{selected['title']}" style="max-height: 380px; object-fit: cover; width: 100%;">\n        </div>""" if image_path else ""

        new_plaque = f"""      <article class="museum-plaque" style="margin-bottom: 1rem;">
        <header class="plaque-header">
          <span class="plaque-year">Acquired {selected['year']}</span>
          <h3 class="plaque-title" style="font-size: 1.8rem;"><a href="{selected['filename']}" style="color: inherit; text-decoration: none;">{selected['title']}</a></h3>
          <p class="plaque-room">{selected['catalog']}</p>
        </header>{img_daily_tag}
        <div class="museum-label">
          <p>{selected['label']}</p>
        </div>
        <div class="fun-fact-box">
          <div class="fun-fact-title">Curator's Note &bull; Fun Fact</div>
          <p class="fun-fact-text">{selected['fun_fact']}</p>
        </div>
        <div style="margin-top: 1.5rem; text-align: right;">
          <a href="{selected['filename']}" class="card-action">View Full Exhibit &rarr;</a>
        </div>
        {source_note}
      </article>"""

        index_content, count = re.subn(
            r'<article class="museum-plaque" style="margin-bottom: 1rem;">.*?</article>',
            new_plaque,
            index_content,
            flags=re.DOTALL
        )
        if count != 1:
            raise ValueError("Homepage marker missing or duplicated")
        index_content = checked_sub(r'(?:Daily Feature|Latest Addition) &bull; [^<]+', f'Latest Addition &bull; {now_str}', index_content)
        index_content = index_content.replace('Objects of the Day', 'Featured Objects')
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(index_content)

    # 7. Update dashboard.html (prepend newest item to table and update banner)
    if os.path.exists("dashboard.html"):
        with open("dashboard.html", "r", encoding="utf-8") as f:
            dash_content = f.read()

        new_row = f"""        <tr>
          <td><span class="room-tag">{selected['room_title_zh']} {selected['room_name']}</span></td>
          <td><strong>{selected['title']}</strong> ⭐</td>
          <td>{selected['year']}</td>
          <td><a href="{selected['filename']}" class="quick-open-btn">開啟展品 &rarr;</a></td>
        </tr>\n"""

        marker = "<tbody>\n"
        if dash_content.count(marker) != 1:
            raise ValueError("Dashboard marker missing or duplicated")
        if marker in dash_content:
            dash_content = dash_content.replace(marker, marker + new_row, 1)

        dash_content = checked_sub(
            r'<span class="plaque-year">最新自動入庫項目</span>\s*<h3.*?>.*?</h3>\s*<p.*?>.*?</p>\s*<a href=".*?" class="card-action">.*?</a>',
            f'<span class="plaque-year">最新自動入庫項目</span>\n      <h3 style="font-family: var(--font-serif); font-size: 1.4rem; margin: 0.35rem 0;">{selected["title"]}（{selected["title_zh"]}）</h3>\n      <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.75rem;">展廳：{selected["room_title_zh"]} ({selected["room_name"]}) &bull; 收購年份：{selected["year"]} &bull; 字數：{selected["word_count"]}</p>\n      <a href="{selected["filename"]}" class="card-action">點此直接查看展品頁面 &rarr;</a>',
            dash_content,
            flags=re.DOTALL
        )

        # Update dynamic stats count
        total_exhibits = len([f for f in os.listdir(".") if f.endswith(".html") and "-" in f and not f.endswith(".bak")])
        kitchen_count = len([f for f in os.listdir(".") if f.startswith("kitchen-") and f.endswith(".html")])
        desk_count = len([f for f in os.listdir(".") if f.startswith("desk-") and f.endswith(".html")])
        garage_count = len([f for f in os.listdir(".") if f.startswith("garage-") and f.endswith(".html")])
        dash_content = checked_sub(
            r'<div class="stat-number">\d+</div>\s*<div class="stat-label">現有展品總數</div>',
            f'<div class="stat-number">{total_exhibits}</div>\n        <div class="stat-label">現有展品總數</div>',
            dash_content
        )
        dash_content = checked_sub(
            r'<div class="stat-number">\d+ / \d+ / \d+</div>\s*<div class="stat-label">廚房 / 書桌 / 車庫</div>',
            f'<div class="stat-number">{kitchen_count} / {desk_count} / {garage_count}</div>\n        <div class="stat-label">廚房 / 書桌 / 車庫</div>',
            dash_content
        )

        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(dash_content)

    print(f"Successfully added {selected['title']} and updated all pages.")

    return True

