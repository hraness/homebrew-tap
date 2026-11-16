import base64
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('yaptake_mirrors', Path(__file__).parents[1] / 'tools/yaptake-mirrors.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


def fixture(payload=b'Synthetic archive', build='225', name='Yaptake-0.1.0-private'):
    archive_hash = hashlib.sha256(payload).hexdigest()
    package = {'version': '0.1.0', 'buildNumber': build, 'sha256': archive_hash, 'archive': name + '.zip', 'channel': 'private', 'sourceDirty': False, 'bundleIdentifier': 'com.yapwing.app', 'architecture': 'arm64', 'minimumMacOS': '26.0', 'teamID': '8AAP53VTW3', 'notarization': {'status': 'Accepted', 'stapleValidated': True, 'gatekeeperAccepted': True}, **{key: 'a' * length for key, length in [('sourceSHA', 40), ('sourceTreeSHA', 40), ('sourceSnapshotSHA256', 64), ('symbolsSHA256', 64), ('appTreeSHA256', 64)]}}
    data = {f'downloads/{archive_hash}/{name}.zip': payload, f'downloads/{archive_hash}/{name}.sha256': f'{archive_hash}  {name}.zip\n'.encode(), f'downloads/{archive_hash}/{name}.manifest.json': m.encode(package)}
    rows = [{'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'sha1': hashlib.sha1(raw).hexdigest(), 'length': len(raw)} for path, raw in sorted(data.items())]
    tag = f'yaptake-0.1.0-{build}-{archive_hash}'
    record = {'version': '0.1.0', 'build': build, 'sha256': archive_hash, 'tag': tag, 'releaseID': int(build), 'files': [{**row, 'assetID': int(build) * 10 + index, 'url': m.asset_url(tag, Path(row['path']).name)} for index, row in enumerate(rows, 1)]}
    return rows, data, package, record


def response(data):
    stream = io.BytesIO(data); stream.status = 200; stream.headers = {'Content-Length': str(len(data))}; return stream


class MirrorsTests(unittest.TestCase):
    def test_exact_triples_and_native_public_receipts(self):
        rows, data, package, _ = fixture()
        self.assertEqual(m.validate_package(rows, lambda path: data[path]), package)
        for change in ('missing', 'unsafe', 'hash', 'dirty', 'team'):
            changed = copy.deepcopy(rows); files = dict(data)
            if change == 'missing': changed.pop()
            elif change == 'unsafe': changed[0]['path'] = '../private.txt'
            elif change == 'hash': changed[-1]['sha256'] = 'b' * 64
            else:
                value = copy.deepcopy(package); value['sourceDirty' if change == 'dirty' else 'teamID'] = True if change == 'dirty' else 'OTHERTEAM1'
                row = next(row for row in changed if row['path'].endswith('.manifest.json')); raw = m.encode(value); files[row['path']] = raw; row.update(sha256=hashlib.sha256(raw).hexdigest(), sha1=hashlib.sha1(raw).hexdigest(), length=len(raw))
            with self.subTest(change=change), self.assertRaises(ValueError): m.validate_package(changed, lambda path: files[path])

    def test_archives_named_without_the_signing_channel_are_admitted(self):
        rows, data, package, record = fixture(build='240', name='Yaptake-0.1.0')
        self.assertEqual(m.validate_package(rows, lambda path: data[path]), package)
        self.assertEqual(m.PATH.fullmatch(rows[0]['path'])[3], '0.1.0')
        self.assertEqual(m.PATH.fullmatch('downloads/' + 'a' * 64 + '/Yaptake-0.1.0-private.zip')[3], '0.1.0')

    def test_append_is_stable_and_cannot_replace_or_roll_back_prior_entries(self):
        _, _, _, first = fixture(); _, _, _, second = fixture(b'Second synthetic archive', '226')
        catalog, changed = m.merge_catalog(m.empty_catalog(), first); self.assertTrue(changed)
        same, changed = m.merge_catalog(catalog, copy.deepcopy(first)); self.assertFalse(changed); self.assertEqual(same, catalog)
        next_catalog, changed = m.merge_catalog(catalog, second); self.assertTrue(changed); self.assertIn(first, next_catalog['archives'])
        replaced = copy.deepcopy(first); replaced['files'][0]['length'] += 1
        with self.assertRaisesRegex(ValueError, 'cannot be replaced'): m.merge_catalog(catalog, replaced)
        alternate = copy.deepcopy(first); alternate.update(build='227', tag=first['tag'].replace('-225-', '-227-'), releaseID=227)
        for row in alternate['files']: row['url'] = m.asset_url(alternate['tag'], Path(row['path']).name)
        with self.assertRaisesRegex(ValueError, 'different runtime'): m.merge_catalog(catalog, alternate)

    def test_conditional_append_reconciles_another_writer_without_losing_history(self):
        _, _, _, first = fixture(); _, _, _, second = fixture(b'Concurrent archive', '226')
        class Concurrent(m.GitHub):
            def __init__(self): self.catalog = m.empty_catalog(); self.calls = 0; self.puts = []
            def read_catalog(self): return self.catalog, 'a' * 40 if self.calls == 0 else 'b' * 40
            def api(self, method, path, value=None):
                self.assertion = (method, path)
                if method == 'PUT':
                    self.puts.append(value); self.calls += 1
                    if self.calls == 1:
                        self.catalog, _ = m.merge_catalog(self.catalog, first); raise m.APIError(409)
                    if value['sha'] != 'b' * 40: raise ValueError('Stale conditional SHA')
                    self.catalog = m.parse(base64.b64decode(value['content']))
        client = Concurrent(); self.assertTrue(client.append(second)); self.assertEqual(len(client.catalog['archives']), 2)
        self.assertFalse(client.append(second)); self.assertEqual(len(client.puts), 2)

    def test_upload_stream_is_bounded_hashed_length_checked_and_connection_closed(self):
        rows, data, _, _ = fixture(b'x' * 200001); row = next(row for row in rows if row['path'].endswith('.zip'))
        connections = []
        class Connection:
            def __init__(self, *args, **kwargs): self.parts = []; self.closed = False; connections.append(self)
            def putrequest(self, *args): pass
            def putheader(self, *args): pass
            def endheaders(self): pass
            def send(self, block): self.parts.append(block)
            def getresponse(self):
                raw = m.encode({'id': 1, 'name': Path(row['path']).name, 'state': 'uploaded', 'size': row['length'], 'digest': 'sha256:' + row['sha256']})
                result = response(raw); result.status = 201; return result
            def close(self): self.closed = True
        client = m.GitHub('synthetic-token')
        with mock.patch.object(client, 'api') as api:
            result = client.upload(1, row, lambda path: response(data[path]), Connection)
        self.assertEqual(result, row); self.assertEqual(b''.join(connections[0].parts), data[row['path']]); self.assertTrue(connections[0].closed)
        self.assertLessEqual(max(map(len, connections[0].parts)), 65536); api.assert_called_once()
        def corrupt(path): return response(b'y' * row['length'])
        with self.assertRaisesRegex(ValueError, 'changed during streaming'):
            client.upload(1, row, corrupt, Connection)
        self.assertTrue(connections[-1].closed)
        with self.assertRaisesRegex(ValueError, 'length changed'):
            client.upload(1, row, lambda path: response(b'truncated'), Connection)
        self.assertTrue(connections[-1].closed)

    def test_lost_label_recovery_streams_and_rechecks_source_without_replacing_asset(self):
        rows, data, _, _ = fixture(b'x' * 200001)
        row = next(row for row in rows if row['path'].endswith('.zip'))
        self.assertEqual(m.source_hashes({**row, 'sha1': None}, lambda path: response(data[path])), row)
        with self.assertRaisesRegex(ValueError, 'changed during draft recovery'):
            m.source_hashes(row, lambda path: response(b'y' * row['length']))

    def test_upload_refuses_remote_digest_mismatch_before_admission(self):
        rows, _, _, _ = fixture(); row = rows[0]
        for field, value in [('digest', 'sha256:' + '0' * 64), ('state', 'starter'), ('size', row['length'] + 1), ('name', 'private-source.zip')]:
            asset = {'id': 1, 'name': Path(row['path']).name, 'size': row['length'], 'state': 'uploaded', 'digest': 'sha256:' + row['sha256']}; asset[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Remote asset'): m.verify_asset(asset, row)

    def test_scope_preflight_requires_one_exact_public_tap_without_admin_scope(self):
        client = m.GitHub('synthetic-token')
        good = {'total_count': 1, 'repositories': [{'id': 1382935233, 'full_name': m.REPO, 'private': False, 'owner': {'id': 307125679, 'login': 'hraness'}}]}
        with mock.patch.object(client, 'api', return_value=good) as api: client.preflight()
        api.assert_called_once_with('GET', '/installation/repositories')
        for access in ({**good, 'total_count': 2}, {**good, 'repositories': [{**good['repositories'][0], 'private': True}]}, {**good, 'repositories': [{**good['repositories'][0], 'id': 1}]}):
            with mock.patch.object(client, 'api', return_value=access), self.assertRaisesRegex(ValueError, 'select only'): client.preflight()

    def test_draft_recovery_uses_exact_tag_listing_and_id_not_latest_or_tag_lookup(self):
        _, _, _, record = fixture()
        draft = {'id': 225, 'tag_name': record['tag'], 'body': m.MARKER, 'draft': True}
        client = mock.Mock()
        unrelated = {'id': 999, 'tag_name': 'newest-unrelated', 'draft': False}
        client.api.side_effect = [[unrelated, draft], draft]
        self.assertEqual(m.exact_release(client, record['tag']), draft)
        self.assertEqual(client.api.call_args_list, [mock.call('GET', m.PREFIX + '/releases?per_page=100&page=1'), mock.call('GET', m.PREFIX + '/releases/225')])
        client.api.side_effect = [[draft, draft]]
        with self.assertRaisesRegex(ValueError, 'Multiple'): m.exact_release(client, record['tag'])
        client.api.side_effect = [[{**draft, 'body': 'Unexpected owner'}]]
        with self.assertRaisesRegex(ValueError, 'unexpected'): m.exact_release(client, record['tag'])
        client.api.side_effect = [[unrelated] * 100] * 3
        with self.assertRaisesRegex(ValueError, 'exceeds'): m.exact_release(client, record['tag'])

    def test_mirror_cannot_append_until_all_assets_are_immutable_and_read_back(self):
        rows, data, package, record = fixture()
        class Fake:
            def __init__(self, immutable, canonical_published_url=True, change_draft_tag=False):
                self.immutable = immutable; self.appended = False; self.published = False
                self.canonical_published_url = canonical_published_url; self.change_draft_tag = change_draft_tag
                self.release = {'id': 225, 'tag_name': record['tag'], 'body': m.MARKER, 'draft': True, 'immutable': False, 'assets': []}
            def api(self, method, path, value=None):
                if '?per_page=100&page=' in path: return [self.release]
                if method == 'GET' and len(self.release['assets']) == 3 and self.release['draft'] and self.change_draft_tag:
                    self.release['tag_name'] = 'changed-before-publication'
                if method == 'PATCH':
                    self.published = True; self.release.update(draft=False, immutable=self.immutable)
                    if self.canonical_published_url:
                        for asset in self.release['assets']: asset['browser_download_url'] = m.asset_url(record['tag'], asset['name'])
                return self.release
            def upload(self, release_id, row):
                file = next(item for item in record['files'] if item['path'] == row['path'])
                self.release['assets'].append({'id': file['assetID'], 'name': Path(row['path']).name, 'state': 'uploaded', 'size': row['length'], 'digest': 'sha256:' + row['sha256'], 'label': 'sha1:' + row['sha1'], 'browser_download_url': m.asset_url('untagged-832de19bcd9fee2eb4d8', Path(row['path']).name)})
                return row
            def append(self, value): self.appended = True; self.record = value
        with mock.patch.object(m, 'validate_package', return_value=package):
            bad = Fake(False)
            with self.assertRaisesRegex(ValueError, 'not immutable'): m.mirror(bad, rows)
            self.assertFalse(bad.appended)
            good = Fake(True); result = m.mirror(good, rows); self.assertTrue(good.appended); self.assertEqual(result, record)
            wrong_url = Fake(True, canonical_published_url=False)
            with self.assertRaisesRegex(ValueError, 'Published asset URL differs'): m.mirror(wrong_url, rows)
            self.assertTrue(wrong_url.published); self.assertFalse(wrong_url.appended)
            changed = Fake(True, change_draft_tag=True)
            with self.assertRaisesRegex(ValueError, 'Owned mirror identity'): m.mirror(changed, rows)
            self.assertFalse(changed.published); self.assertFalse(changed.appended)
