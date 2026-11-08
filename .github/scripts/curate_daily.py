import os
import re
import datetime

POOL = [
    {
        "filename": "desk-wooden-ruler.html",
        "room": "desk",
        "room_name": "Desk",
        "room_title_zh": "書桌",
        "title": "Wooden Folding Ruler",
        "title_zh": "木製摺疊尺",
        "year": "1970",
        "catalog": "Desk Collection &bull; Room 02",
        "label": "<strong>Wooden Folding Ruler</strong>. Acquired 1970. Bound by brass hinges and seasoned boxwood, it unfolds six feet of tactile measurement. Its incised increments keep steady geometric faith against shifting human ambition.",
        "fun_fact": "Anton Ullrich patented the spring-joint folding ruler in 1886.",
        "card_preview": "Bound by brass hinges and seasoned boxwood, it unfolds six feet of tactile measurement with steady geometric faith.",
        "word_count": "34 字"
    },
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

    # 2. Create the exhibit HTML file
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
      <a href="kitchen.html"{" class=\"active\"" if selected['room'] == 'kitchen' else ""}>Kitchen</a>
      <a href="desk.html"{" class=\"active\"" if selected['room'] == 'desk' else ""}>Desk</a>
      <a href="garage.html"{" class=\"active\"" if selected['room'] == 'garage' else ""}>Garage</a>
    </nav>
  </header>

  <main>
    <div class="exhibit-container">
      <article class="museum-plaque">
        <header class="plaque-header">
          <span class="plaque-year">Acquired {selected['year']}</span>
          <h1 class="plaque-title">{selected['title']}</h1>
          <p class="plaque-room">{selected['catalog']}</p>
        </header>

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

    # 3. Update room gallery HTML
    room_file = f"{selected['room']}.html"
    if os.path.exists(room_file):
        with open(room_file, "r", encoding="utf-8") as f:
            room_content = f.read()

        card_snippet = f"""
      <a href="{selected['filename']}" class="object-card">
        <span class="card-year">Acquired {selected['year']}</span>
        <h3 class="card-title">{selected['title']}</h3>
        <p class="card-preview">{selected['card_preview']}</p>
        <span class="card-action">View Exhibit &rarr;</span>
      </a>
    </div>"""

        room_content = room_content.replace("    </div>\n  </main>", f"{card_snippet}\n  </main>")
        with open(room_file, "w", encoding="utf-8") as f:
            f.write(room_content)

    # 4. Update index.html Object of the Day
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            index_content = f.read()

        new_plaque = f"""      <article class="museum-plaque" style="margin-bottom: 1rem;">
        <header class="plaque-header">
          <span class="plaque-year">Acquired {selected['year']}</span>
          <h3 class="plaque-title" style="font-size: 1.8rem;"><a href="{selected['filename']}" style="color: inherit; text-decoration: none;">{selected['title']}</a></h3>
          <p class="plaque-room">{selected['catalog']}</p>
        </header>
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

    # 5. Append to HISTORY.md
    if os.path.exists("HISTORY.md"):
        with open("HISTORY.md", "r", encoding="utf-8") as f:
            hist_content = f.read()

        new_row = f"| **{now_str}** | **{selected['title']}（{selected['title_zh']}）** | {selected['room_name']}（{selected['room_title_zh']}） | {selected['year']} | {selected['word_count']} | 雲端定時自動新增 ⭐ | [查看展品]({selected['filename']}) |\n"
        
        # Insert right after table header
        parts = hist_content.split("| :--- | :--- | :--- | :---: | :---: | :---: | :--- |\n")
        if len(parts) == 2:
            hist_content = parts[0] + "| :--- | :--- | :--- | :---: | :---: | :---: | :--- |\n" + new_row + parts[1]
            with open("HISTORY.md", "w", encoding="utf-8") as f:
                f.write(hist_content)

    print(f"Successfully added {selected['title']} and updated all pages.")
    return True

if __name__ == "__main__":
    run()
