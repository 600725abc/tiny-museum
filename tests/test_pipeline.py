import base64
import copy
import datetime as dt
import importlib.util
import io
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.github/scripts'))
import pipeline as p

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cwd = Path.cwd()
        self.root = Path(self.temp.name)
        for pattern in ('*.html', '*.css', 'HISTORY.md'):
            for file in ROOT.glob(pattern):
                shutil.copy2(file, self.root/file.name)
        shutil.copytree(ROOT/'images', self.root/'images')
        shutil.copytree(ROOT/'automation', self.root/'automation')
        os.chdir(self.root)
        p.write(p.STATE, {'last_published_at': None, 'pending': None, 'attempts': [], 'published': [], 'source_ids': []})
        self.item = p.read('automation/catalog.json')[0]
        self.item['word_count'] = str(p.words(self.item))+' words'

    def tearDown(self):
        os.chdir(self.cwd)
        self.temp.cleanup()

    def pending(self, phase):
        state = p.read(p.STATE)
        state['pending'] = {'item': self.item, 'phase': phase, 'run_id': '123'}
        p.write(p.STATE, state)

    def image(self):
        out = io.BytesIO()
        Image.new('RGB', (256, 256), 'tan').save(out, 'PNG')
        return out.getvalue()

    def test_cross_month_and_leap_day(self):
        for stamp in ['2026-01-31T01:17:00+00:00', '2028-02-28T01:17:00+00:00']:
            start = dt.datetime.fromisoformat(stamp)
            state = {'last_published_at': stamp}
            self.assertFalse(p.due(state, start+dt.timedelta(days=2)))
            self.assertTrue(p.due(state, start+dt.timedelta(hours=72)))
            self.assertTrue(p.due(state, start+dt.timedelta(hours=71, minutes=59)))

    def test_closed_gate_never_calls_network(self):
        with patch.dict(os.environ, {'MUSEUM_PAID_ENABLED': 'false'}), patch.object(p.urllib.request, 'urlopen', side_effect=AssertionError('network')):
            p.prepare()
            p.generate()
        self.assertIsNone(p.read(p.STATE)['pending'])

    def test_unapproved_budget_blocks(self):
        with patch.dict(os.environ, {'MUSEUM_PAID_ENABLED': 'true'}):
            with self.assertRaisesRegex(RuntimeError, 'not approved'):
                p.prepare()

    def test_monthly_allowance_blocks_before_network(self):
        budget = p.read('automation/budget.json')
        budget.update(approved=True, max_requests_per_month=1)
        p.write('automation/budget.json', budget)
        state = p.read(p.STATE)
        state['attempts'] = [{'at': p.now().isoformat(), 'reserved_usd': 0.25}]
        p.write(p.STATE, state)
        with patch.dict(os.environ, {'MUSEUM_PAID_ENABLED': 'true'}), patch.object(p.urllib.request, 'urlopen', side_effect=AssertionError('network')):
            with self.assertRaisesRegex(RuntimeError, 'allowance'):
                p.prepare()

    def test_paid_timeout_is_not_retried_and_reservation_survives(self):
        self.pending('reserved')
        budget = p.read('automation/budget.json')
        budget['approved'] = True
        p.write('automation/budget.json', budget)
        with patch.dict(os.environ, {'MUSEUM_PAID_ENABLED': 'true', 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1', 'OPENAI_API_KEY': 'mock-not-a-key'}):
            with patch.object(p.urllib.request, 'urlopen', side_effect=TimeoutError('mock')) as call:
                with self.assertRaises(TimeoutError):
                    p.generate()
                self.assertEqual(call.call_count, 1)
        self.assertEqual(p.read(p.STATE)['pending']['phase'], 'reserved')
        self.assertFalse(Path(self.item['filename']).exists())

    def test_rerun_cannot_repeat_paid_request(self):
        self.pending('reserved')
        budget = p.read('automation/budget.json')
        budget['approved'] = True
        p.write('automation/budget.json', budget)
        with patch.dict(os.environ, {'MUSEUM_PAID_ENABLED': 'true', 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '2'}):
            with self.assertRaisesRegex(RuntimeError, 'retry'):
                p.generate()

    def test_reservation_blocks_ambiguous_retry(self):
        self.pending('reserved')
        with self.assertRaisesRegex(RuntimeError, 'reservation'):
            p.prepare()

    def test_base64_and_url_images(self):
        raw = self.image()
        for response in [{'data': [{'b64_json': base64.b64encode(raw).decode()}]}, {'data': [{'url': 'https://example.org/image'}]}]:
            with patch.object(p.urllib.request, 'urlopen', return_value=io.BytesIO(raw)):
                output = p.decode_image(response)
            with Image.open(io.BytesIO(output)) as image:
                self.assertEqual(image.format, 'JPEG')

    def test_corrupt_response_rejected(self):
        for data in [{'data': [{}]}, {'data': [{'b64_json': 'broken'}]}, {'data': [{'url': 'http://example.org'}]}]:
            with self.assertRaises(Exception):
                p.decode_image(data)

    def test_image_failure_cannot_create_page(self):
        self.pending('reserved')
        before = Path('index.html').read_bytes()
        with self.assertRaises(RuntimeError):
            p.render()
        self.assertFalse(Path(self.item['filename']).exists())
        self.assertEqual(before, Path('index.html').read_bytes())

    def test_missing_marker_is_atomic(self):
        self.pending('image_ready')
        Path('index.html').write_text('no marker')
        before = Path('garage.html').read_bytes()
        with self.assertRaises(ValueError):
            p.render()
        self.assertEqual(before, Path('garage.html').read_bytes())
        self.assertFalse(Path(self.item['filename']).exists())

    def test_render_and_retry_do_not_duplicate(self):
        self.pending('image_ready')
        Path('images', self.item['filename'].replace('.html', '.jpg')).write_bytes(self.image())
        p.render()
        before = Path('garage.html').read_bytes()
        p.render()
        self.assertEqual(before, Path('garage.html').read_bytes())
        self.assertTrue(Path(self.item['filename']).exists())
        self.assertIsNone(p.read(p.STATE)['last_published_at'])

    def test_catalog_voice(self):
        for item in p.read('automation/catalog.json'):
            p.validate(item)

    def test_source_refill_and_dedup(self):
        def fake(url):
            if 'search?' in url:
                return {'objectIDs': [1, 2]}
            return {'title': 'Spoon', 'medium': 'Silver', 'objectDate': '1890', 'objectURL': 'https://www.metmuseum.org/art/collection/search/2'}
        with patch.object(p, 'get_json', side_effect=fake):
            item = p.replenish({'source_ids': [1], 'published': []})
        self.assertEqual(item['source_id'], 2)
        p.validate(item)

    def test_finalization_requires_verification(self):
        self.pending('rendered')
        p.build()
        with self.assertRaises(FileNotFoundError):
            p.finalize()
        self.assertIsNone(p.read(p.STATE)['last_published_at'])

    def test_success_finalization_idempotent(self):
        self.pending('rendered')
        p.build()
        Path('automation/verified.tmp').write_text(p.hashlib.sha256(Path('_site/deployment.json').read_bytes()).hexdigest())
        p.finalize()
        before = p.read(p.STATE)
        p.finalize()
        self.assertEqual(before, p.read(p.STATE))
        self.assertIsNotNone(before['last_published_at'])

    def test_build_excludes_internal_files(self):
        p.build()
        self.assertFalse(Path('_site/automation').exists())
        self.assertFalse(Path('_site/.github').exists())

    def test_complete_pipeline_with_mock_api_and_mock_deployment(self):
        budget = p.read('automation/budget.json')
        budget['approved'] = True
        p.write('automation/budget.json', budget)
        payload = p.json.dumps({'data': [{'b64_json': base64.b64encode(self.image()).decode()}], 'usage': {'output_tokens': 1}}).encode()
        with patch.dict(os.environ, {'MUSEUM_PAID_ENABLED': 'true', 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1', 'OPENAI_API_KEY': 'mock-not-a-key'}):
            p.prepare()
            with patch.object(p.urllib.request, 'urlopen', return_value=io.BytesIO(payload)) as call:
                p.generate()
                self.assertEqual(call.call_count, 1)
        p.render()
        p.build()
        def deployed(url, **kwargs):
            name = p.urllib.parse.urlparse(url).path.removeprefix('/museum/')
            return io.BytesIO(Path('_site', name).read_bytes())
        with patch.object(p.urllib.request, 'urlopen', side_effect=deployed):
            p.verify('https://example.org/museum/')
        p.finalize()
        state = p.read(p.STATE)
        self.assertIsNone(state['pending'])
        self.assertEqual(len(state['published']), 1)
        self.assertEqual(len(state['attempts']), 1)

    def test_failed_online_verification_cannot_finalize(self):
        self.pending('rendered')
        p.build()
        with patch.object(p.urllib.request, 'urlopen', side_effect=lambda *args, **kw: io.BytesIO(b'stale page')), patch.object(p.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'do not match'):
                p.verify('https://example.org/')
        self.assertIsNone(p.read(p.STATE)['last_published_at'])
        self.assertFalse(Path('automation/verified.tmp').exists())

    def test_source_exhaustion_fails_explicitly(self):
        with patch.object(p, 'get_json', return_value={'objectIDs': []}):
            with self.assertRaisesRegex(RuntimeError, 'No eligible'):
                p.replenish({'published': [], 'source_ids': []})

if __name__ == '__main__':
    unittest.main()
