import os
import re
import datetime

POOL = [
    {
        "filename": "garage-torpedo-level.html",
        "room": "garage",
        "room_name": "Garage",
        "room_title_zh": "車庫",
        "title": "Brass Spirit Torpedo Level",
        "title_zh": "黃銅水準尺",
        "year": "1962",
        "catalog": "The Garage Room &bull; Catalog No. G-06",
        "label": "<strong>Brass Spirit Torpedo Level</strong>. Acquired 1962. Machined from solid brass and fitted with glowing vials, it registers true horizontal balance. Its floating green bubble speaks silent judgment to unsteady surfaces.",
        "fun_fact": "Melchisedech Thevenot invented the spirit level around 1661.",
        "card_preview": "Machined from solid brass with glowing vials, registering true horizontal balance with silent mechanical authority.",
        "word_count": "33 字"
    },
    {
        "filename": "kitchen-bottle-opener.html",
        "room": "kitchen",
        "room_name": "Kitchen",
        "room_title_zh": "廚房",
        "title": "Cast Iron Bottle Opener",
        "title_zh": "鑄鐵開瓶器",
        "year": "1959",
        "catalog": "Kitchen Collection &bull; Catalog No. K-06",
        "label": "<strong>Cast Iron Bottle Opener</strong>. Acquired 1959. Molded in unpolished iron, it levers crown caps with crisp, metallic satisfaction. Decades of evening gatherings have burnished its grip to satin perfection.",
        "fun_fact": "William Painter invented both the crown bottle cap and opener in 1892.",
        "card_preview": "Molded in unpolished iron, levering crown caps with crisp satisfaction across decades of celebratory gatherings.",
        "word_count": "33 字"
    },
    {
        "filename": "garage-iron-c-clamp.html",
        "room": "garage",
        "room_name": "Garage",
        "room_title_zh": "車庫",
        "title": "Heavy Iron C-Clamp",
        "title_zh": "重型鑄鐵C型夾",
        "year": "1955",
        "catalog": "The Garage Room &bull; Catalog No. G-07",
        "label": "<strong>Heavy Iron C-Clamp</strong>. Acquired 1955. Cast in ductile iron with an Acme threaded screw, it holds glued timber with unswerving vigilance. Its swivel pad distributes tons of pressure without marring wood.",
        "fun_fact": "The Acme thread profile was formulated in 1894 for heavy load clamping.",
        "card_preview": "Cast in ductile iron with an Acme threaded screw, holding glued timber with unswerving mechanical vigilance.",
        "word_count": "34 字"
    },
    {
        "filename": "desk-rotary-pencil-sharpener.html",
        "room": "desk",
        "room_name": "Desk",
        "room_title_zh": "書桌",
        "title": "Mechanical Rotary Pencil Sharpener",
        "title_zh": "旋轉手搖削鉛筆機",
        "year": "1976",
        "catalog": "Desk Collection &bull; Room 02",
        "label": "<strong>Mechanical Rotary Pencil Sharpener</strong>. Acquired 1976. Twin cylindrical milling cutters shave cedar spirals into a clear receptacle with rhythmic grind. It restores precision points with disciplined mechanical efficiency.",
        "fun_fact": "The planetary gear rotary sharpener was patented in 1896 by A.B. Dick.",
        "card_preview": "Twin cylindrical milling cutters shave cedar spirals with rhythmic grind, restoring precision points with disciplined efficiency.",
        "word_count": "34 字"
    }
]

def generate_exhibit_image(title, prompt_desc, filename, room=""):
    """Call OpenAI API using gpt-image-2.6-flare to generate high-end domestic setting artwork."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not configured. Skipping automated image generation.")
        return None

    os.makedirs("images", exist_ok=True)
    img_filename = f"images/{filename.replace('.html', '.jpg')}"
    
    endpoint = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Designated model: gpt-image-2.6-flare
    model_name = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.6-flare")
    
    furniture_context = {
        "kitchen": "a warm solid butcher block kitchen island or honed soapstone counter",
        "desk": "a handsome dark oiled walnut study desk with book spines and quiet stationery",
        "garage": "a scarred but cherished solid maple carpenter workbench in a sunlit home workshop"
    }.get(room.lower(), "sophisticated, textured solid hardwood home furniture")

    prompt = (
        f"An editorial still-life photograph of {title}, an everyday household object celebrated for its sculptural quality and honest utility. "
        f"{prompt_desc}. "
        f"Setting: Intimate, high-end residential home environment—naturally placed on {furniture_context}. "
        f"Strictly not an art gallery, no museum plinths, no sterile pedestals. "
        f"Atmosphere: Rich, tasteful home interior with tactile domestic textures, warm natural daylight streaming through a nearby residential window, "
        f"subtle soft morning illumination highlighting the patina of daily life. Architectural Digest domestic aesthetic."
    )
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }

    try:
        import urllib.request
        import json
        
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            img_url = data["data"][0]["url"]
            
            with urllib.request.urlopen(img_url, timeout=30) as img_resp:
                with open(img_filename, "wb") as f_img:
                    f_img.write(img_resp.read())
            print(f"Successfully generated exhibit image via {model_name}: {img_filename}")
            return img_filename
    except Exception as e:
        print(f"Notice: Image generation with {model_name} encountered: {e}")
        return None

def run():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 1. Pick first object not yet in repo
    selected = None
    for item in POOL:
        if not os.path.exists(item["filename"]):
            selected = item
            break
            
    if not selected:
        print("All pool exhibits have already been added.")
        return False

    print(f"Adding new exhibit: {selected['title']}")

    # 2. Generate Image with GPT Image 2.6 (if API key is present)
    image_path = generate_exhibit_image(selected['title'], selected['card_preview'], selected['filename'])
    image_tag = f"""\n        <div class="exhibit-image">\n          <img src="{image_path}" alt="{selected['title']}">\n        </div>""" if image_path else ""

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
      </article>"""

        index_content = re.sub(
            r'<article class="museum-plaque" style="margin-bottom: 1rem;">.*?</article>',
            new_plaque,
            index_content,
            flags=re.DOTALL
        )
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(index_content)

    # 6. Append to HISTORY.md (newest at top)
    if os.path.exists("HISTORY.md"):
        with open("HISTORY.md", "r", encoding="utf-8") as f:
            hist_content = f.read()

        new_row = f"| **{now_str}** | **{selected['title']}（{selected['title_zh']}）** | {selected['room_name']}（{selected['room_title_zh']}） | {selected['year']} | {selected['word_count']} | 雲端定時自動新增 ⭐ | [查看展品]({selected['filename']}) |\n"
        
        parts = hist_content.split("| :--- | :--- | :--- | :---: | :---: | :---: | :--- |\n")
        if len(parts) == 2:
            hist_content = parts[0] + "| :--- | :--- | :--- | :---: | :---: | :---: | :--- |\n" + new_row + parts[1]
            with open("HISTORY.md", "w", encoding="utf-8") as f:
                f.write(hist_content)

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
        if marker in dash_content:
            dash_content = dash_content.replace(marker, marker + new_row, 1)

        dash_content = re.sub(
            r'<span class="plaque-year">最新自動入庫項目</span>\s*<h3.*?>.*?</h3>\s*<p.*?>.*?</p>\s*<a href=".*?" class="card-action">.*?</a>',
            f'<span class="plaque-year">最新自動入庫項目</span>\n      <h3 style="font-family: var(--font-serif); font-size: 1.4rem; margin: 0.35rem 0;">{selected["title"]}（{selected["title_zh"]}）</h3>\n      <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.75rem;">展廳：{selected["room_title_zh"]} ({selected["room_name"]}) &bull; 收購年份：{selected["year"]} &bull; 字數：{selected["word_count"]}</p>\n      <a href="{selected["filename"]}" class="card-action">點此直接查看展品頁面 &rarr;</a>',
            dash_content,
            flags=re.DOTALL
        )

        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(dash_content)

    print(f"Successfully added {selected['title']} and updated all pages.")
    return True

if __name__ == "__main__":
    run()
