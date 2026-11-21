#!/usr/bin/env python3
"""Mirror already-public Yaptake bytes, then append immutable content identities."""
from __future__ import annotations

import argparse
import base64
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import build_opener, HTTPRedirectHandler, Request

REPO = 'hraness/homebrew-tap'
PREFIX = '/repos/' + REPO
BRANCH = 'yaptake-downloads'
CATALOG = 'yaptake-downloads.json'
ORIGIN = 'https://yaptake.com/'
META_LIMIT = 128 * 1024
INVENTORY_LIMIT = 2 * 1024 * 1024
API_LIMIT = 4 * 1024 * 1024
ASSET_LIMIT = 2 * 1024 * 1024 * 1024 - 1
MAX_FILES = 768
# Archives finalized from 2026-11-16 are Yaptake-VERSION.*; earlier ones keep
# their published Yaptake/Yapwing-VERSION-private.* names.
PATH = re.compile(r'downloads/([a-f0-9]{64})/((?:Yaptake|Yapwing)-([0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+?)??)(?:-private)?)\.(zip|sha256|manifest\.json)')
MARKER = 'Exact-byte mirror of an already-public Yaptake package. Native activation is managed by yaptake.com.'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def parse(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: need(False, 'Invalid JSON number'))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise ValueError('Source bytes and API requests must not redirect')


def source_open(path, method='GET'):
    need(isinstance(path, str) and (PATH.fullmatch(path) or path in ('release.json', 'appcast.xml', 'downloads.json')), 'Source is outside the exact public package allowlist')
    response = build_opener(NoRedirect()).open(Request(ORIGIN + path, method=method, headers={
        'User-Agent': 'Yaptake-immutable-mirror/1', 'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'}), timeout=60)
    need(response.status == 200 and response.geturl() == ORIGIN + path and response.headers.get('Content-Encoding', 'identity') == 'identity', 'Unexpected source response')
    return response


def declared_length(response, limit):
    value = response.headers.get('Content-Length')
    need(value is not None and value.isdigit() and 0 < int(value) <= limit, 'Source must declare a bounded positive Content-Length')
    return int(value)


def small_source(path):
    limit = INVENTORY_LIMIT if path == 'downloads.json' else META_LIMIT
    with source_open(path) as response:
        size = declared_length(response, limit)
        raw = response.read(limit + 1)
    need(len(raw) == size, 'Public metadata was truncated or oversized')
    return raw


def validate_rows(rows, sha1_required=True):
    need(isinstance(rows, list) and 3 <= len(rows) <= MAX_FILES, 'Expected bounded complete public triples')
    groups, seen = {}, set()
    for row in rows:
        need(isinstance(row, dict) and set(row) == {'path', 'sha256', 'sha1', 'length'}, 'Invalid source content record')
        match = PATH.fullmatch(row['path']) if isinstance(row['path'], str) else None
        need(match and row['path'] not in seen and isinstance(row['sha256'], str) and re.fullmatch('[a-f0-9]{64}', row['sha256']), 'Unsafe or duplicate public package path')
        need((not sha1_required and row['sha1'] is None) or (isinstance(row['sha1'], str) and re.fullmatch('[a-f0-9]{40}', row['sha1'])), 'Invalid source SHA-1 content hash')
        need(type(row['length']) is int and 0 < row['length'] <= (ASSET_LIMIT if match[4] == 'zip' else META_LIMIT), 'Invalid bounded source length')
        need(match[4] != 'zip' or row['sha256'] == match[1], 'ZIP path does not contain its exact content hash')
        seen.add(row['path']); groups.setdefault((match[1], match[2]), []).append(row)
    need(all({PATH.fullmatch(row['path'])[4] for row in group} == {'zip', 'sha256', 'manifest.json'} and len(group) == 3 for group in groups.values()), 'Every archive needs its exact checksum and manifest')
    return groups


def validate_package(rows, fetch=small_source):
    """Check already-public native receipts; this does not admit or activate new native bytes."""
    validate_rows(rows, False)
    manifest = next(row for row in rows if row['path'].endswith('.manifest.json'))
    checksum = next(row for row in rows if row['path'].endswith('.sha256'))
    archive = next(row for row in rows if row['path'].endswith('.zip'))
    for row in (manifest, checksum):
        raw = fetch(row['path'])
        need(len(raw) == row['length'] and hashlib.sha256(raw).hexdigest() == row['sha256'] and (row['sha1'] is None or hashlib.sha1(raw).hexdigest() == row['sha1']), 'Public metadata changed from its admitted content record')
        if row is manifest:
            package = parse(raw)
        else:
            need(raw == f"{archive['sha256']}  {Path(archive['path']).name}\n".encode(), 'Checksum does not match the public archive')
    need(isinstance(package, dict) and package.get('sourceDirty') is False and package.get('channel') == 'private' and package.get('bundleIdentifier') == 'com.yapwing.app', 'Expected an already-finalized native package')
    need(package.get('architecture') == 'arm64' and package.get('minimumMacOS') == '26.0' and package.get('teamID') == '8AAP53VTW3', 'Unexpected native platform or signing team')
    notary = package.get('notarization', {})
    need(isinstance(notary, dict) and notary.get('status') == 'Accepted' and notary.get('stapleValidated') is True and notary.get('gatekeeperAccepted') is True, 'Native package receipt lacks accepted notarization')
    match = PATH.fullmatch(archive['path'])
    need(package.get('archive') == Path(archive['path']).name and package.get('sha256') == archive['sha256'] and package.get('version') == match[3] and isinstance(package.get('buildNumber'), str) and re.fullmatch('[1-9][0-9]{0,8}', package['buildNumber']), 'Package version, build or archive identity differs')
    for key, length in [('sourceSHA', 40), ('sourceTreeSHA', 40), ('sourceSnapshotSHA256', 64), ('symbolsSHA256', 64), ('appTreeSHA256', 64)]:
        need(isinstance(package.get(key), str) and re.fullmatch('[a-f0-9]{' + str(length) + '}', package[key]), 'Package is missing its finalized content provenance')
    return package


def archive_digest(value):
    need(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value), 'Expected an exact lowercase archive SHA-256')
    return value


def staged_plan(sha256, fetch=small_source):
    """Select only the named public triple, including when its URLs redirect to a registered mirror."""
    archive_digest(sha256)
    inventory = parse(fetch('downloads.json'))
    need(isinstance(inventory, dict) and set(inventory) == {'schemaVersion', 'files'} and type(inventory['schemaVersion']) is int and inventory['schemaVersion'] == 1, 'Invalid public download inventory')
    files = inventory['files']
    need(isinstance(files, list) and 3 <= len(files) <= MAX_FILES, 'Expected a bounded inventory of public archive triples')
    need(all(isinstance(row, dict) and set(row) == {'path', 'sha256', 'length'} for row in files), 'Expected canonical public download identities')
    groups = validate_rows([{**row, 'sha1': None} for row in files], sha1_required=False)
    matches = [rows for (archive, _), rows in groups.items() if archive == sha256]
    need(len(matches) == 1, 'Expected exactly one complete public package for the staged SHA-256')
    return matches[0]


def current_plan(fetch=small_source, catalog=None):
    release_raw, feed_raw = fetch('release.json'), fetch('appcast.xml')
    manifest = parse(release_raw); release = manifest.get('release')
    need(manifest.get('schemaVersion') == 1 and isinstance(release, dict), 'No active native release')
    path = release.get('url', '').removeprefix(ORIGIN)
    match = PATH.fullmatch(path)
    need(match and match[4] == 'zip' and release['url'] == ORIGIN + path and release.get('sha256') == match[1], 'Active release is not the exact canonical native archive')
    length = release.get('sparkle', {}).get('length')
    need(type(length) is int and 0 < length <= ASSET_LIMIT, 'Invalid active archive length')
    known = next((record for record in (catalog or empty_catalog())['archives'] if record['sha256'] == match[1]), None)
    rows = [] if known is None else [{key: row[key] for key in ('path', 'sha256', 'sha1', 'length')} for row in known['files']]
    for suffix in (() if known is not None else ('manifest.json', 'sha256', 'zip')):
        source = path.removesuffix('zip') + suffix
        if suffix == 'zip':
            rows.append({'path': source, 'sha256': match[1], 'sha1': None, 'length': length})
        else:
            raw = fetch(source)
            rows.append({'path': source, 'sha256': hashlib.sha256(raw).hexdigest(), 'sha1': hashlib.sha1(raw).hexdigest(), 'length': len(raw)})
    package = validate_package(rows, fetch) if known is None else {'version': known['version'], 'buildNumber': known['build']}
    need(release.get('version') == package['version'] and (known is not None or release.get('sourceCommit') == package['sourceSHA']), 'Active release and package source differ')
    need(any(row['path'] == path and row['length'] == length for row in rows), 'Active release length differs from its admitted mirror')
    # The source-owned appcast is selection, never GitHub's latest-release flag.
    import xml.etree.ElementTree as ET
    need(b'<!DOCTYPE' not in feed_raw.upper() and b'<!ENTITY' not in feed_raw.upper(), 'Unsupported appcast XML')
    items = ET.fromstring(feed_raw).findall('./channel/item'); need(len(items) == 1, 'Expected one active native appcast item')
    item = items[0]; namespace = '{http://www.andymatuschak.org/xml-namespaces/sparkle}'
    enclosure = item.findall('enclosure'); need(len(enclosure) == 1, 'Expected one active archive enclosure')
    need(item.findtext(namespace + 'version') == package['buildNumber'] and item.findtext(namespace + 'shortVersionString') == package['version'] and enclosure[0].get('url') == release['url'] and enclosure[0].get('length') == str(length) and enclosure[0].get(namespace + 'edSignature') == release['sparkle'].get('edSignature'), 'Active feed and archive identity differ')
    need(fetch('release.json') == release_raw and fetch('appcast.xml') == feed_raw, 'Native activation changed during mirror planning')
    return rows


def empty_catalog():
    return {'schemaVersion': 1, 'product': 'yaptake', 'repository': REPO, 'archives': []}


def validate_catalog(value):
    need(isinstance(value, dict) and set(value) == {'schemaVersion', 'product', 'repository', 'archives'} and type(value['schemaVersion']) is int and value['schemaVersion'] == 1 and value['product'] == 'yaptake' and value['repository'] == REPO and isinstance(value['archives'], list) and len(value['archives']) <= MAX_FILES // 3, 'Invalid public mirror catalog')
    paths, ids, tags = set(), set(), set()
    for archive in value['archives']:
        need(isinstance(archive, dict) and set(archive) == {'version', 'build', 'sha256', 'tag', 'releaseID', 'files'}, 'Invalid mirrored archive record')
        need(isinstance(archive['version'], str) and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', archive['version']) and isinstance(archive['build'], str) and re.fullmatch('[1-9][0-9]{0,8}', archive['build']) and isinstance(archive['sha256'], str) and re.fullmatch('[a-f0-9]{64}', archive['sha256']), 'Invalid mirrored runtime identity')
        need(archive['tag'] == f"yaptake-{archive['version']}-{archive['build']}-{archive['sha256']}" and archive['tag'] not in tags and type(archive['releaseID']) is int and archive['releaseID'] > 0 and archive['releaseID'] not in ids and isinstance(archive['files'], list) and len(archive['files']) == 3, 'Invalid exact release identity')
        rows = []
        for row in archive['files']:
            need(isinstance(row, dict) and set(row) == {'path', 'sha256', 'sha1', 'length', 'assetID', 'url'}, 'Invalid mirrored file')
            need(isinstance(row['path'], str) and row['path'] not in paths and type(row['assetID']) is int and row['assetID'] > 0 and row['url'] == asset_url(archive['tag'], Path(row['path']).name), 'Duplicate file or unexpected asset URL')
            match = PATH.fullmatch(row['path']); need(match and match[1] == archive['sha256'] and match[3] == archive['version'], 'Asset filename disagrees with its archive identity')
            paths.add(row['path']); rows.append({key: row[key] for key in ('path', 'sha256', 'sha1', 'length')})
        validate_rows(rows); ids.add(archive['releaseID']); tags.add(archive['tag'])
    need(value['archives'] == sorted(value['archives'], key=lambda row: row['tag']), 'Catalog must have canonical tag order')
    return value


def asset_url(tag, name):
    return f'https://github.com/{REPO}/releases/download/{tag}/{name}'


def merge_catalog(previous, record):
    validate_catalog(previous)
    old = next((item for item in previous['archives'] if item['tag'] == record['tag']), None)
    if old is not None:
        need(old == record, 'An admitted immutable identity cannot be replaced')
        return previous, False
    need(not any(item['sha256'] == record['sha256'] for item in previous['archives']), 'Archive hash cannot acquire a different runtime identity')
    result = {**previous, 'archives': sorted(previous['archives'] + [record], key=lambda item: item['tag'])}
    return validate_catalog(result), True


class APIError(ValueError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'GitHub API returned HTTP {status}; no activation was changed')


class GitHub:
    def __init__(self, token):
        need(token and '\n' not in token and '\r' not in token, 'A scoped GitHub App installation token is required')
        self.token = token

    def api(self, method, path, value=None):
        need(path == '/installation/repositories' or path.startswith(PREFIX + '/'), 'GitHub API path is outside the selected tap')
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2026-03-10', 'User-Agent': 'Yaptake-immutable-mirror/1'}
        raw = None if value is None else encode(value)
        if raw is not None:
            headers['Content-Type'] = 'application/json'
        try:
            with build_opener(NoRedirect()).open(Request('https://api.github.com' + path, data=raw, method=method, headers=headers), timeout=60) as response:
                body = response.read(API_LIMIT + 1)
                need(len(body) <= API_LIMIT, 'GitHub response exceeds the metadata limit')
                return parse(body) if body else None
        except HTTPError as error:
            raise APIError(error.code) from None

    def preflight(self):
        access = self.api('GET', '/installation/repositories')
        need(access.get('total_count') == 1 and len(access.get('repositories', [])) == 1 and access['repositories'][0].get('id') == 1382935233 and access['repositories'][0].get('full_name') == REPO and access['repositories'][0].get('private') is False and access['repositories'][0].get('owner', {}).get('id') == 307125679 and access['repositories'][0].get('owner', {}).get('login') == 'hraness', 'App installation token must select only the existing public tap')

    def read_catalog(self):
        try:
            result = self.api('GET', PREFIX + '/contents/' + CATALOG + '?ref=' + BRANCH)
        except APIError as error:
            if error.status == 404:
                return empty_catalog(), None
            raise
        need(result.get('type') == 'file' and result.get('encoding') == 'base64' and isinstance(result.get('sha'), str) and re.fullmatch('[a-f0-9]{40}', result['sha']), 'Invalid data-branch catalog object')
        raw = base64.b64decode(result['content'], validate=False)
        need(len(raw) <= 2 * 1024 * 1024, 'Catalog exceeds its metadata bound')
        return validate_catalog(parse(raw)), result['sha']

    def append(self, record):
        for _ in range(4):
            previous, sha = self.read_catalog()
            result, changed = merge_catalog(previous, record)
            if not changed:
                return False
            if sha is None:
                try:
                    self.api('GET', PREFIX + '/git/ref/heads/' + BRANCH)
                except APIError as error:
                    if error.status != 404:
                        raise
                    main = self.api('GET', PREFIX + '/git/ref/heads/main')['object']['sha']
                    try:
                        self.api('POST', PREFIX + '/git/refs', {'ref': 'refs/heads/' + BRANCH, 'sha': main})
                    except APIError as create:
                        if create.status != 422:
                            raise
            body = {'message': 'Record immutable Yaptake archive ' + record['sha256'], 'content': base64.b64encode(encode(result)).decode(), 'branch': BRANCH}
            if sha is not None:
                body['sha'] = sha
            try:
                self.api('PUT', PREFIX + '/contents/' + CATALOG, body)
                readback, _ = self.read_catalog()
                need(any(item == record for item in readback['archives']), 'Conditional catalog update did not persist its exact record')
                return True
            except APIError as error:
                if error.status not in (409, 422):
                    raise
        raise ValueError('Concurrent catalog updates did not converge; retry is safe')

    def upload(self, release_id, row, open_source=source_open, connect=http.client.HTTPSConnection):
        """One bounded stream; no historical ZIP is staged on disk or held in memory."""
        connection = connect('uploads.github.com', timeout=120)
        count, sha256, sha1 = 0, hashlib.sha256(), hashlib.sha1()
        try:
            with open_source(row['path']) as response:
                need(declared_length(response, ASSET_LIMIT if row['path'].endswith('.zip') else META_LIMIT) == row['length'], 'Source length changed before upload')
                path = PREFIX + f'/releases/{release_id}/assets?' + urlencode({'name': Path(row['path']).name})
                connection.putrequest('POST', path)
                for name, value in {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2026-03-10', 'User-Agent': 'Yaptake-immutable-mirror/1', 'Content-Type': 'application/octet-stream', 'Content-Length': str(row['length'])}.items():
                    connection.putheader(name, value)
                connection.endheaders()
                while block := response.read(64 * 1024):
                    count += len(block)
                    need(count <= row['length'], 'Source exceeded its admitted length')
                    sha256.update(block); sha1.update(block); connection.send(block)
                need(count == row['length'] and sha256.hexdigest() == row['sha256'] and (row['sha1'] is None or sha1.hexdigest() == row['sha1']), 'Source bytes changed during streaming; draft cannot be published')
                result = connection.getresponse(); raw = result.read(API_LIMIT + 1)
                need(result.status == 201 and len(raw) <= API_LIMIT, 'Draft asset upload did not succeed')
                asset = parse(raw)
            verify_asset(asset, row)
            row = {**row, 'sha1': sha1.hexdigest()}
            self.api('PATCH', PREFIX + '/releases/assets/' + str(asset['id']), {'label': 'sha1:' + row['sha1']})
            return row
        finally:
            connection.close()


def source_hashes(row, open_source=source_open):
    """Recover a lost draft-label acknowledgement without staging or replacing bytes."""
    count, sha256, sha1 = 0, hashlib.sha256(), hashlib.sha1()
    with open_source(row['path']) as response:
        need(declared_length(response, ASSET_LIMIT if row['path'].endswith('.zip') else META_LIMIT) == row['length'], 'Source length changed during draft recovery')
        while block := response.read(64 * 1024):
            count += len(block); need(count <= row['length'], 'Source exceeded its admitted length')
            sha256.update(block); sha1.update(block)
    need(count == row['length'] and sha256.hexdigest() == row['sha256'] and (row['sha1'] is None or sha1.hexdigest() == row['sha1']), 'Source bytes changed during draft recovery')
    return {**row, 'sha1': sha1.hexdigest()}


def verify_asset(asset, row):
    need(isinstance(asset, dict) and type(asset.get('id')) is int and asset['id'] > 0 and asset.get('name') == Path(row['path']).name and asset.get('state') == 'uploaded' and asset.get('size') == row['length'] and asset.get('digest') == 'sha256:' + row['sha256'], 'Remote asset digest or length differs from the exact source bytes')


def exact_release(github, tag):
    # GET releases/tags hides drafts. Authenticated bounded listing recovers the
    # exact owned draft by ID; order and latest flags never select an artifact.
    matches = []
    for page in range(1, 4):
        releases = github.api('GET', PREFIX + f'/releases?per_page=100&page={page}')
        need(isinstance(releases, list) and len(releases) <= 100, 'Invalid bounded release listing')
        matches.extend(release for release in releases if isinstance(release, dict) and release.get('tag_name') == tag)
        if len(releases) < 100:
            break
    else:
        raise ValueError('Release listing exceeds its bound; exact draft discovery is incomplete')
    need(len(matches) <= 1, 'Multiple releases claim the same exact archive tag')
    if not matches:
        return None
    release = matches[0]
    need(type(release.get('id')) is int and release['id'] > 0 and release.get('body') == MARKER, 'Exact tag belongs to an unexpected release')
    readback = github.api('GET', PREFIX + '/releases/' + str(release['id']))
    need(readback.get('id') == release['id'] and readback.get('tag_name') == tag and readback.get('body') == MARKER, 'Exact draft changed during ID readback')
    return readback


def mirror(github, rows):
    package = validate_package(rows)
    tag = f"yaptake-{package['version']}-{package['buildNumber']}-{package['sha256']}"
    release = exact_release(github, tag)
    if release is None:
        main = github.api('GET', PREFIX + '/git/ref/heads/main')['object']['sha']
        need(isinstance(main, str) and re.fullmatch('[a-f0-9]{40}', main), 'Exact public tap source commit is required')
        release = github.api('POST', PREFIX + '/releases', {'tag_name': tag, 'target_commitish': main, 'name': f"Yaptake {package['version']} ({package['buildNumber']}): {package['sha256'][:12]}", 'body': MARKER, 'draft': True, 'prerelease': True, 'make_latest': 'false'})
    need(release.get('tag_name') == tag and type(release.get('id')) is int and release.get('body') == MARKER and isinstance(release.get('assets'), list) and len(release['assets']) <= 3, 'Existing tag is not an owned exact-byte mirror draft')
    release_id = release['id']
    names = [asset.get('name') for asset in release['assets']]
    need(len(set(names)) == len(names) and set(names) <= {Path(row['path']).name for row in rows}, 'Mirror release has unexpected assets')
    completed = []
    for row in sorted(rows, key=lambda item: item['path']):
        asset = next((asset for asset in release['assets'] if asset.get('name') == Path(row['path']).name), None)
        if asset is not None and asset.get('state') == 'starter' and asset.get('size') == 0:
            need(release.get('draft') is True and type(asset.get('id')) is int and asset['id'] > 0, 'Only an exact empty asset in an owned draft may be retried')
            github.api('DELETE', PREFIX + '/releases/assets/' + str(asset['id']))
            asset = None
        if asset is None:
            need(release.get('draft') is True, 'A published mirror cannot be changed')
            row = github.upload(release_id, row)
        else:
            verify_asset(asset, row)
            label = asset.get('label', '')
            if not label and release.get('draft') is True:
                row = source_hashes(row)
                github.api('PATCH', PREFIX + '/releases/assets/' + str(asset['id']), {'label': 'sha1:' + row['sha1']})
            else:
                need(isinstance(label, str) and re.fullmatch('sha1:[a-f0-9]{40}', label) and (row['sha1'] is None or label == 'sha1:' + row['sha1']), 'Existing asset label conflicts with its exact source identity')
                row = {**row, 'sha1': label.removeprefix('sha1:')}
        completed.append(row)
    release = github.api('GET', PREFIX + '/releases/' + str(release_id))
    need(release.get('id') == release_id and release.get('tag_name') == tag and release.get('body') == MARKER and len(release.get('assets', [])) == 3, 'Owned mirror identity and all three exact assets are required before publication')
    for row in completed:
        asset = next((item for item in release['assets'] if item.get('name') == Path(row['path']).name), {})
        verify_asset(asset, row)
        need(asset.get('label') == 'sha1:' + row['sha1'], 'Asset readback lost its exact source identity')
    # Draft assets use temporary untagged URLs. Admit canonical download URLs
    # only from the immutable published readback below; never fetch draft URLs.
    if release.get('draft') is True:
        github.api('PATCH', PREFIX + '/releases/' + str(release_id), {'draft': False, 'prerelease': True, 'make_latest': 'false'})
    release = github.api('GET', PREFIX + '/releases/' + str(release_id))
    need(release.get('id') == release_id and release.get('body') == MARKER and release.get('draft') is False and release.get('immutable') is True and release.get('tag_name') == tag and len(release.get('assets', [])) == 3, 'Published release is not immutable; catalog admission refused')
    files = []
    for row in completed:
        asset = next((item for item in release['assets'] if item.get('name') == Path(row['path']).name), {})
        verify_asset(asset, row)
        need(asset.get('browser_download_url') == asset_url(tag, Path(row['path']).name), 'Published asset URL differs')
        files.append({**row, 'assetID': asset['id'], 'url': asset['browser_download_url']})
    record = {'version': package['version'], 'build': package['buildNumber'], 'sha256': package['sha256'], 'tag': tag, 'releaseID': release['id'], 'files': files}
    validate_catalog({**empty_catalog(), 'archives': [record]})
    github.append(record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--staged-sha256', type=archive_digest, help='Mirror just the exact archive SHA-256 already listed in yaptake.com/downloads.json')
    selection.add_argument('--include-history', action='store_true', help='Admit the reviewed exact public history seed before the current release')
    args = parser.parse_args()
    github = GitHub(os.environ.get('YAPTAKE_RELEASE_TOKEN'))
    github.preflight()
    if args.preflight:
        print('GitHub App token selects only the exact public tap; no publication attempted')
        return
    previous, _ = github.read_catalog()
    plans = []
    if args.include_history:
        seed = parse(Path('catalog/yaptake-history.json').read_bytes())
        need(isinstance(seed, dict) and set(seed) == {'schemaVersion', 'files'} and type(seed['schemaVersion']) is int and seed['schemaVersion'] == 1, 'Invalid reviewed history seed')
        plans.extend(validate_rows(seed['files']).values())
    if args.staged_sha256:
        plans.append(staged_plan(args.staged_sha256))
    else:
        plans.extend(validate_rows(current_plan(catalog=previous), False).values())
    for rows in plans:
        known = next((record for record in previous['archives'] if record['sha256'] == PATH.fullmatch(rows[0]['path'])[1]), None)
        if known is not None:
            by_path = {row['path']: row for row in known['files']}
            need(all(row['path'] in by_path and all(row[key] is None or row[key] == by_path[row['path']][key] for key in ('sha256', 'sha1', 'length')) for row in rows), 'Existing immutable catalog conflicts with public source identity')
            continue
        record = mirror(github, rows)
        previous, _ = merge_catalog(previous, record)
        print(json.dumps({'status': 'immutable', 'tag': record['tag'], 'files': len(record['files'])}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(f'Yaptake mirror refused: {error}') from None
