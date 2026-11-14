"""Durable reservations prevent ambiguous paid requests from being retried.
Only deployment byte verification advances the three-day publication date.
"""
import base64
import datetime as dt
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from PIL import Image

STATE = Path('automation/state.json')
ROOMS = {'kitchen': '廚房', 'desk': '書桌', 'garage': '車庫'}
QUERIES = {'kitchen': ['spoon', 'ladle', 'kettle', 'strainer', 'bowl'],
           'desk': ['inkstand', 'paperweight', 'ruler', 'pen', 'scissors'],
           'garage': ['hammer', 'saw', 'pliers', 'chisel']}

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)

def now():
    return dt.datetime.now(dt.timezone.utc)

def due(state, clock=None):
    last = state.get('last_published_at')
    taipei = dt.timezone(dt.timedelta(hours=8))
    return not last or ((clock or now()).astimezone(taipei).date() -
                       dt.datetime.fromisoformat(last).astimezone(taipei).date()).days >= 3

def words(item):
    return len(html.unescape(re.sub('<[^>]+>', '', item['label']+' '+item['fun_fact'])).split())

def validate(item):
    if item['room'] not in ROOMS or not re.fullmatch(r'(kitchen|desk|garage)-[a-z0-9-]+\.html', item['filename']):
        raise ValueError('Invalid exhibit identity')
    if words(item) > 40 or '!' in item['label']+item['fun_fact']:
        raise ValueError('Label violates museum voice')

def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'TinyMuseum/2.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def replenish(state):
    """Free, source-backed metadata; fail explicitly on outage or exhaustion."""
    used = set(state.get('source_ids', []))
    rooms = list(ROOMS)
    start = len(state.get('published', [])) % len(rooms)
    for room in rooms[start:]+rooms[:start]:
        for query in QUERIES[room]:
            for offset in range(0, 2000, 100):
                params = urllib.parse.urlencode({'q': query, 'title': 'true', 'offset': offset, 'limit': 100})
                data = get_json('https://collectionapi.metmuseum.org/public/collection/v1.1/search?'+params)
                ids = data.get('objectIDs') or []
                if not ids:
                    break
                for ident in ids:
                    if ident in used or Path(f'{room}-met-{ident}.html').exists():
                        continue
                    obj = get_json(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{ident}')
                    title, medium, date = (obj.get(k, '') for k in ('title', 'medium', 'objectDate'))
                    if not title or query not in title.lower() or len(title.split()) > 7:
                        continue
                    if not medium or len(medium.split()) > 6 or not date or len(date.split()) > 6:
                        continue
                    if any(c in title+medium+date for c in '<>!'):
                        continue
                    year = str(now().year)
                    item = dict(filename=f'{room}-met-{ident}.html', room=room,
                        room_name=room.title(), room_title_zh=ROOMS[room], title=title,
                        title_zh='日常器物研究', year=year, catalog=f'{room.title()} Collection',
                        label=f'<strong>{html.escape(title)}</strong>. Acquired {year}. {html.escape(medium)} gives this form its substance. Its silhouette invites quiet attention.',
                        fun_fact=f'The Met dates it to {html.escape(date)}.',
                        card_preview=f'{title}. Material: {medium}. A digital study of an everyday object.',
                        source=obj['objectURL'], source_id=ident,
                        source_metadata={'title': title, 'medium': medium, 'objectDate': date})
                    if words(item) <= 40:
                        item['word_count'] = str(words(item))+' words'
                        return item
    raise RuntimeError('No eligible source objects remain. Expand reviewed queries; not a successful empty run.')

def preflight(item):
    validate(item)
    markers = [(item['room']+'.html', '<div class="gallery-grid">\n'), ('dashboard.html', '<tbody>\n')]
    for file, marker in markers:
        if Path(file).read_text(encoding='utf-8').count(marker) != 1:
            raise ValueError('Missing/duplicate marker: '+file)
    text = Path('index.html').read_text(encoding='utf-8')
    if len(re.findall(r'<article id="featured-exhibit" class="museum-plaque" style="margin-bottom: 1rem;">.*?</article>', text, re.S)) != 1:
        raise ValueError('Homepage marker missing/duplicate')

def prepare():
    state = read(STATE)
    pending = state.get('pending')
    if pending:
        if pending['phase'] == 'reserved':
            raise RuntimeError('Unresolved paid reservation. Recover artifact or reconcile billing; automatic retry blocked.')
        return
    if not due(state):
        print('Not due: fewer than three Taipei calendar days since verified publication.')
        return
    if os.getenv('MUSEUM_PAID_ENABLED') != 'true':
        print('Paid generation paused pending budget approval; existing site can deploy.')
        return
    config = read('automation/budget.json')
    if not config['approved']:
        raise RuntimeError('Repository budget not approved.')
    attempts = [a for a in state['attempts'] if a['at'].startswith(now().strftime('%Y-%m'))]
    if len(attempts) >= config['max_requests_per_month'] or sum(a['reserved_usd'] for a in attempts)+config['reserve_per_request_usd'] > config['monthly_budget_usd']:
        raise RuntimeError('Monthly conservative request allowance reached.')
    item = next((i for i in read('automation/catalog.json') if not Path(i['filename']).exists()), None)
    item = item or replenish(state)
    item['word_count'] = str(words(item))+' words'
    preflight(item)
    stamp = now().isoformat()
    state['attempts'].append({'at': stamp, 'reserved_usd': config['reserve_per_request_usd'], 'filename': item['filename']})
    state['pending'] = {'item': item, 'phase': 'reserved', 'at': stamp, 'run_id': os.environ['GITHUB_RUN_ID']}
    write(STATE, state)

def decode_image(data):
    entry = data['data'][0]
    if entry.get('b64_json'):
        raw = base64.b64decode(entry['b64_json'], validate=True)
    elif entry.get('url'):
        if not entry['url'].startswith('https://'):
            raise ValueError('Image URL must use HTTPS')
        with urllib.request.urlopen(entry['url'], timeout=60) as response:
            raw = response.read(30_000_001)
    else:
        raise ValueError('Missing image data')
    if len(raw) > 30_000_000:
        raise ValueError('Image too large')
    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        if min(img.size) < 256:
            raise ValueError('Image too small')
        output = io.BytesIO()
        img.convert('RGB').save(output, 'JPEG', quality=92)
    return output.getvalue()

def generate():
    state = read(STATE)
    pending = state.get('pending')
    if not pending or pending['phase'] != 'reserved':
        return
    if os.getenv('MUSEUM_PAID_ENABLED') != 'true' or not read('automation/budget.json')['approved']:
        raise RuntimeError('Paid gate closed')
    if pending['run_id'] != os.getenv('GITHUB_RUN_ID') or os.getenv('GITHUB_RUN_ATTEMPT', '1') != '1':
        raise RuntimeError('Cannot retry a previous paid reservation')
    item = pending['item']
    furniture = {'kitchen': 'warm butcher block kitchen island', 'desk': 'oiled walnut study desk', 'garage': 'worn maple home workshop bench'}[item['room']]
    prompt = (f"Editorial still-life photograph of {item['title']}. {item['card_preview']} "
              f'Naturally placed on a {furniture}. Warm residential window light, tactile surfaces, '
              'quiet domestic atmosphere, believable proportions, no museum plinth, no lettering. '
              'Illustrative interpretation, not documentary reproduction.')
    payload = {'model': 'gpt-image-2.6-flare', 'prompt': prompt, 'n': 1, 'size': '1024x1024', 'quality': 'low', 'output_format': 'jpeg'}
    req = urllib.request.Request('https://api.openai.com/v1/images/generations', data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer '+os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
    # One paid call, no retry on timeout/429/5xx: billing may already have happened.
    with urllib.request.urlopen(req, timeout=240) as response:
        data = json.load(response)
    raw = decode_image(data)
    Path('images', item['filename'].replace('.html', '.jpg')).write_bytes(raw)
    pending['phase'] = 'image_ready'
    pending['usage'] = data.get('usage', {})
    write(STATE, state)

def render():
    state = read(STATE)
    pending = state.get('pending')
    if not pending or pending['phase'] == 'rendered':
        return
    if pending['phase'] != 'image_ready':
        raise RuntimeError('Cannot publish without a validated image')
    item = pending['item']
    preflight(item)
    root = Path.cwd()
    if Path(item['filename']).exists():
        raise RuntimeError('Refusing to overwrite an existing exhibit')
    import curate_daily
    # Render in an isolated staging directory; failed checks never touch public pages.
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        for file in root.glob('*.html'):
            shutil.copy2(file, stage/file.name)
        shutil.copytree(root/'images', stage/'images')
        try:
            os.chdir(stage)
            curate_daily.POOL = [item]
            curate_daily.run(item['room'])
        finally:
            os.chdir(root)
        for file in stage.glob('*.html'):
            if not (root/file.name).exists() or file.read_bytes() != (root/file.name).read_bytes():
                shutil.copy2(file, root/file.name)
    pending['phase'] = 'rendered'
    write(STATE, state)

def build():
    output = Path('_site')
    output.mkdir()  # must be fresh to avoid accidentally deploying stale files
    for pattern in ('*.html', '*.css'):
        for file in Path('.').glob(pattern):
            shutil.copy2(file, output/file.name)
    shutil.copytree('images', output/'images')
    files = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file()}
    write(output/'deployment.json', {'files': files})
    print(f'Built {len(files)} public files; automation state and secrets excluded.')

def verify(base):
    for name, expected in read('_site/deployment.json')['files'].items():
        for attempt in range(6):
            try:
                with urllib.request.urlopen(base.rstrip('/')+'/'+name+'?verify='+expected[:12], timeout=30) as response:
                    actual = hashlib.sha256(response.read()).hexdigest()
                if actual == expected:
                    break
            except Exception:
                pass
            if attempt == 5:
                raise RuntimeError('Deployed bytes do not match: '+name)
            time.sleep(10)
    Path('automation/verified.tmp').write_text(hashlib.sha256(Path('_site/deployment.json').read_bytes()).hexdigest())
    print('All deployed pages, stylesheet and images match local bytes.')

def format_delivery_summary(item, base_url=None):
    base = (base_url or os.getenv('PAGE_URL') or 'https://600725abc.github.io/tiny-museum/').rstrip('/') + '/'
    room = item['room']
    room_url = f"{base}{room}.html"
    exhibit_url = f"{base}{item['filename']}"
    home_url = base
    dashboard_url = f"{base}dashboard.html"

    clean_label = re.sub(r'<[^>]+>', '', item['label']).strip()
    clean_fact = re.sub(r'<[^>]+>', '', item['fun_fact']).strip()

    title_display = item['title'] + (f"（{item['title_zh']}）" if item.get('title_zh') else '')
    room_display = f"{item['room_name']}（{ROOMS.get(room, room)}）"

    lines = [
        "## 🏛️ Tiny Museum 展品發布交付報告 (Delivery Summary)",
        "",
        "### 交付方式與公開線上連結 (Public URLs)",
        f"- **館藏首頁 (Home)**: [{home_url}]({home_url})",
        f"- **本次新增展品 (New Exhibit)**: [{item['title']}]({exhibit_url})",
        f"- **所屬展廳 (Room Gallery)**: [{room_display}]({room_url})",
        f"- **展館儀表板 (Dashboard)**: [{dashboard_url}]({dashboard_url})",
        "",
        "### 交付展品詳細元數據 (Exhibit Metadata)",
        f"- **展件名稱**: {title_display}",
        f"- **所屬展廳**: {room_display}",
        f"- **典藏年份**: Acquired {item['year']}",
        f"- **展籤字數**: {words(item)} words (嚴格上限 40 字)",
        f"- **展籤內文**: {clean_label}",
        f"- **館長趣聞**: {clean_fact}",
        "",
        "### 驗收狀態 (Verification)",
        "- **逐檔校驗**: 線上所有公開檔案（HTML、CSS、圖片）SHA-256 核對一致",
        "- **發布狀態**: 已完成部署並通過線上逐檔驗證"
    ]
    return "\n".join(lines)

def emit_delivery_summary(item, base_url=None):
    summary = format_delivery_summary(item, base_url)
    print(summary)

    step_summary_path = os.getenv('GITHUB_STEP_SUMMARY')
    if step_summary_path:
        try:
            with open(step_summary_path, 'a', encoding='utf-8') as f:
                f.write(summary + '\n')
        except Exception as e:
            print(f"Warning: Failed to write GITHUB_STEP_SUMMARY: {e}", file=sys.stderr)
    return summary

def finalize(base_url=None):
    expected = hashlib.sha256(Path('_site/deployment.json').read_bytes()).hexdigest()
    if Path('automation/verified.tmp').read_text() != expected:
        raise RuntimeError('Online verification missing')
    state = read(STATE)
    pending = state.get('pending')
    if not pending:
        return
    if pending['phase'] != 'rendered':
        raise RuntimeError('Exhibit not rendered')
    stamp, item = now().isoformat(), pending['item']
    state['last_published_at'] = stamp
    state['published'].append({'filename': item['filename'], 'at': stamp, 'title': item['title'], 'room': item['room']})
    if item.get('source_id'):
        state['source_ids'].append(item['source_id'])
    state['pending'] = None
    path = Path('HISTORY.md')
    path.write_text(path.read_text(encoding='utf-8')+f'\n| {stamp} | {item["title"]} | {item["room_name"]} | {item["year"]} | {words(item)} words | 部署後逐檔驗證通過 | [查看展品]({item["filename"]}) |\n', encoding='utf-8')
    write(STATE, state)
    emit_delivery_summary(item, base_url)

def summary_cmd(base_url=None):
    state = read(STATE)
    published = state.get('published') or []
    if not published:
        print("No published exhibits found in state.")
        return
    latest_filename = published[-1]['filename']
    catalog = read('automation/catalog.json')
    item = next((i for i in catalog if i['filename'] == latest_filename), None)
    if not item:
        # Fallback to reconstructing basic item
        item = {
            'filename': latest_filename,
            'room': latest_filename.split('-')[0],
            'room_name': latest_filename.split('-')[0].title(),
            'title': published[-1].get('title', latest_filename),
            'year': 'N/A',
            'label': published[-1].get('title', latest_filename),
            'fun_fact': 'Recorded in museum history.',
        }
    emit_delivery_summary(item, base_url)

if __name__ == '__main__':
    if sys.argv[1] == 'verify':
        verify(sys.argv[2])
    elif sys.argv[1] == 'finalize':
        finalize(sys.argv[2] if len(sys.argv) > 2 else None)
    elif sys.argv[1] == 'summary':
        summary_cmd(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {'prepare': prepare, 'generate': generate, 'render': render, 'build': build}[sys.argv[1]]()
