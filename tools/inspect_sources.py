"""Optional private-source integrity audit; never required for reader rebuilds."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def seconds(value):
    hours, minutes, sec = value.split(':')
    return 3600 * int(hours) + 60 * int(minutes) + float(sec)


def main():
    directory = ROOT / 'work/sources'
    playlist = json.loads((directory / 'playlist.json').read_text(encoding='utf-8'))
    outline = json.loads((directory / 'official-course.json').read_text(encoding='utf-8'))['courseOutline']
    acquired = json.loads((directory / 'caption-acquisition.json').read_text(encoding='utf-8'))
    official = {lesson['id']: lesson for unit in outline['units'] for lesson in unit['lessons']}
    integrity = {a['lesson']: a for a in acquired}
    rows, issues, numbered = [], [], []
    for position, entry in enumerate(playlist['entries'], 1):
        match = re.match(r'(\d+)\.', entry['title'])
        if not match:
            rows.append({'playlist_position': position, 'video_id': entry['id'],
                         'status': 'Extra item; acquired/read status recorded separately'})
            continue
        lesson = int(match[1])
        numbered.append(lesson)
        source = integrity[lesson]
        raw_path = directory / f'lecture-{lesson:02d}.vtt'
        raw = raw_path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        endpoints = re.findall(
            r'(\d{2}:\d{2}:\d{2}\.\d+)\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d+)',
            raw.decode('utf-8-sig'))
        last = seconds(endpoints[-1][1])
        ratio = last / entry['duration']
        identity = entry['id'] == official[lesson]['youtube_id'] == source['video_id']
        hash_match = sha == source['sha256']
        endpoint_match = abs(last - source['last_cue_seconds']) < .01
        if not identity or not hash_match or not endpoint_match:
            issues.append({'lesson': lesson, 'identity': identity,
                           'hash': hash_match, 'endpoint': endpoint_match})
        text = (directory / f'lecture-{lesson:02d}.transcript.txt').read_bytes()
        rows.append({'playlist_position': position, 'video_id': entry['id'],
                     'lesson': lesson, 'official_identity_matches': identity,
                     'caption_sha256': sha, 'acquisition_hash_matches': hash_match,
                     'normalized_transcript_sha256': hashlib.sha256(text).hexdigest(),
                     'first_cue_start': seconds(endpoints[0][0]),
                     'last_cue_end': last, 'duration_seconds': entry['duration'],
                     'endpoint_ratio': ratio, 'cue_count': len(endpoints)})
    if sorted(numbered) != list(range(1, 75)):
        issues.append('Numbered lessons are not exactly 1–74')
    report = {'course': outline['title'], 'instructor': outline['professor'],
              'institution': outline['instituteName'],
              'playlist_items': len(rows), 'numbered_lessons': len(numbered),
              'official_outline_lessons': len(official),
              'passed': not issues, 'issues': issues, 'recordings': rows,
              'scope': 'Identity, stored-source integrity and caption endpoints; '
                       'not transcript reading, equation fidelity or scientific review'}
    (ROOT / 'work/author/source-integrity-audit.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    ratios = [r['endpoint_ratio'] for r in rows if 'endpoint_ratio' in r]
    print(json.dumps({k: v for k, v in report.items() if k != 'recordings'}, indent=2))
    print('caption endpoint ratios:', min(ratios), max(ratios))


if __name__ == '__main__':
    main()
