"""Static public source, body-integrity, navigation and timestamp checks."""
import json
import hashlib
from html import unescape
import argparse
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, unquote, urlsplit

from bs4 import BeautifulSoup
from build_book import ROOT, body_of, digest, public_path, read


_MATH = re.compile(
    r'(?<!\\)\\\[(?P<bracket_display>[\s\S]*?)(?<!\\)\\\]'
    r'|(?<!\\)\\\((?P<bracket_inline>[\s\S]*?)(?<!\\)\\\)'
    r'|(?<![\\$])\$\$(?P<dollar_display>[\s\S]*?)(?<!\\)\$\$'
    r'|(?<![\\$])\$(?!\$)(?P<dollar_inline>[\s\S]*?)'
    r'(?<![\\$])\$(?!\$)'
)


def math_spans(text):
    """Recognize whole outer math spans without editing their TeX payload."""
    return [
        {'start': m.start(), 'end': m.end(), 'kind': m.lastgroup,
         'payload': m.group(m.lastgroup)}
        for m in _MATH.finditer(text)
    ]


def math_inventory(body):
    """Compare raw and parsed visible math; code and SVG labels are excluded."""
    excluded = ('pre', 'code', 'script', 'style', 'noscript', 'textarea', 'svg')
    protected = body
    for tag in excluded:
        protected = re.sub(
            r'<' + tag + r'\b[^>]*>[\s\S]*?</' + tag + r'\s*>',
            '', protected, flags=re.I,
        )
    protected = re.sub(r'<!--[\s\S]*?-->', '', protected)
    raw = math_spans(protected)
    soup = BeautifulSoup(body, 'html.parser')
    for element in soup.select(','.join(excluded)):
        element.decompose()
    visible = math_spans(soup.get_text())
    residual = protected
    for span in reversed(raw):
        residual = (
            residual[:span['start']] + ' ' * (span['end'] - span['start'])
            + residual[span['end']:]
        )
    unmatched = [
        {'offset': m.start(), 'token': m.group()}
        for m in re.finditer(r'(?<!\\)\\[()\[\]]|(?<![\\$])\$', residual)
    ]
    raw_payload = [unescape(r['payload']) for r in raw]
    visible_payload = [r['payload'] for r in visible]

    def encode(values):
        return json.dumps(values, ensure_ascii=False).encode()

    return {
        'raw_count': len(raw), 'visible_count': len(visible),
        'raw_payload_sha256': hashlib.sha256(encode(raw_payload)).hexdigest(),
        'visible_payload_sha256': hashlib.sha256(
            encode(visible_payload)
        ).hexdigest(),
        'payload_sequence_matches': raw_payload == visible_payload,
        'unmatched_delimiters': unmatched,
        'raw_literal_comparison_spans': [
            r['payload'] for r in raw if '<' in r['payload'] or '>' in r['payload']
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',action='store_true')
    parser.add_argument('--output',default='package-validation.json')
    args=parser.parse_args()
    manifest = json.loads(read(ROOT / 'source-manifest.json'))
    durations = {r['video_id']: r['duration_seconds'] for r in manifest['recordings']}
    issues, records = [], []
    positions = [r['playlist_position'] for r in manifest['recordings']]
    if positions != list(range(1, len(positions) + 1)):
        issues.append('Playlist positions incomplete or reordered')
    if len(durations) != len(positions):
        issues.append('Duplicate recording identity')
    for path in sorted(ROOT.glob('*.html')):
        document = read(path)
        if "\r" in document:
            issues.append(path.name + ": HTML must use canonical LF newlines")
        body = body_of(document)
        soup = BeautifulSoup(document, 'html.parser')
        ids = [tag['id'] for tag in soup.select('[id]')]
        if len(ids) != len(set(ids)):
            issues.append(path.name + ': duplicate IDs')
        for anchor in soup.select('a[href],script[src],link[href],img[src]'):
            link = anchor.get('href') or anchor.get('src')
            parts = urlsplit(link)
            if parts.scheme:
                if parts.scheme != 'https':
                    issues.append(path.name + ': unexpected URL scheme')
                if parts.netloc == 'www.youtube.com':
                    query = parse_qs(parts.query)
                    video = query.get('v', [''])[0]
                    seconds = int(query.get('t', ['0'])[0])
                    if video not in durations or not 0 <= seconds <= durations[video]:
                        issues.append(path.name + ': invalid recording timestamp')
                continue
            try:
                target = public_path(unquote(parts.path)) if parts.path else path
                if not target.is_file():
                    issues.append(path.name + ': missing local file ' + link)
                elif parts.fragment and target.suffix == '.html':
                    linked = BeautifulSoup(read(target), 'html.parser')
                    if linked.find(id=parts.fragment) is None:
                        issues.append(path.name + ': missing target anchor ' + link)
            except ValueError:
                issues.append(path.name + ': unsafe local path')
        if re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|file://|Users[/\\]', body):
            issues.append(path.name + ': private absolute path in authored body')
        all_math = math_inventory(body)
        if all_math['unmatched_delimiters']:
            issues.append(path.name + ': unmatched mixed math delimiters')
        if path.name.startswith('chapter-'):
            meta = json.loads(read(path.with_suffix('.meta.json')))
            if digest(body) != meta['authored_body_sha256']:
                issues.append(path.name + ': sidecar digest mismatch')
            for s in meta['sections']:
                source = next(r for r in meta['recordings']
                              if (r['video_id'] == s['video_id'] if s.get('video_id')
                                  else r['lesson'] == s['lesson']))
                if not 0 <= s['start'] < s['end'] <= source['duration_seconds']:
                    issues.append(path.name + ': source span out of bounds')
                heading = soup.find(id=s['anchor'])
                if (heading is None or heading.get('data-video') != source['video_id']
                    or heading.get('data-start') != str(s['start'])
                    or heading.get('data-end') != str(s['end'])):
                    issues.append(path.name + ': heading/sidecar source mismatch: ' + s['anchor'])
            for note in meta.get('cross_recording_notes', []):
                source = next((r for r in manifest['recordings']
                               if r['video_id'] == note['video_id']), None)
                if (source is None or source['lesson'] != note['lesson']
                    or not 0 <= note['start'] < note['end'] <= source['duration_seconds']):
                    issues.append(path.name + ': cross-recording note out of bounds')
            article = BeautifulSoup(body, 'html.parser')
            inventory = math_inventory(body)
            if not inventory['payload_sequence_matches']:
                issues.append(path.name + ': raw/parsed math payload mismatch')
            if inventory['raw_literal_comparison_spans']:
                issues.append(path.name + ': escape raw math comparison signs')
            records.append({'file': path.name, 'body_sha256': digest(body),
                            'article_words_including_math_code': len(article.get_text(' ', strip=True).split()),
                            'worked_solutions': len(article.select('details')),
                            'display_equations': body.count(r'\['),
                            'math_inventory': inventory,
                            'source_spans': len(meta['sections'])})
    if args.release:
        from audit_public import inspect
        audit=inspect(mode='content')
        issues.extend(audit['issues'])
        if {c['order'] for c in manifest['chapters']}!=set(range(1,26)):
            issues.append('Final edition requires25 coherent chapters')
    report = {'scope': 'Static structure, links, source bounds and digest integrity; '
                       'not scientific or independent source-fidelity review',
              'passed': not issues, 'issues': issues, 'chapters': records,
              'chapter_hashes':{r['file']:r['body_sha256'] for r in records},
              'release_content_gate_requested':args.release}
    from audit_public import write_report
    write_report(ROOT,args.output,report)
    (ROOT / 'validation').mkdir(exist_ok=True)
    (ROOT / 'validation/static-checks.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'chapters':len(records),
        'release_content_gate_requested':args.release,'issues':issues}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
