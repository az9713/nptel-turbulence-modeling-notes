"""Audit an exact public package; draft inspection is not release acceptance.

--prepublication requires content/review/coverage plus all local checks, while
--release additionally requires final live publication and completion evidence.
No private acquisition or editorial report is read by this public tool.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
BASE_FILES = {
    '.gitattributes', '.gitignore', '.nojekyll', 'README.md', 'WORKFLOW.md',
    'LICENSE', 'THIRD-PARTY.md', 'requirements.txt', 'source-manifest.json',
    'index.html', 'book-overview.html', 'book-overview.meta.json',
    'source-map.html', 'source-map.json', 'references.html', 'numerical-lab.html',
    'tools/build_book.py', 'tools/validate_book.py', 'tools/check_code.py',
    'tools/browser_check.py', 'tools/check_package.py', 'tools/public_files.py',
    'tools/audit_public.py', 'tools/verify_source_free.py', 'tools/verify_publication.py',
    'tools/inspect_sources.py', 'assets/book.css', 'assets/book.js', 'assets/lab.js',
    'assets/mathjax-tex-svg.js', 'assets/mathjax-LICENSE',
    'assets/input/tex/extensions/boldsymbol.js',
    'assets/input/tex/extensions/cancel.js',
    'assets/input/tex/extensions/mathtools.js',
}
RECORDS = {
    'content-inventory.json', 'editorial-review-summary.json',
    'source-validation-summary.json', 'course-review.json', 'completion.json',
    'chapter-code-validation.json', 'reader-validation.json',
    'package-validation.json', 'public-package-validation.json',
    'source-free-validation.json', 'publication-validation.json',
}
# These are individually named files, never recursively exported directories.
PLOT_NAMES = ()
PRIVATE = {'work', '.git', '__pycache__', 'auth', 'credentials', 'sessions'}
TEXT_SUFFIXES = {'.html', '.json', '.md', '.py', '.js', '.css', '.tdb', '.txt'}
SECRET = re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b|\bAKIA[A-Z0-9]{16}\b|[-]{5}BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY[-]{5}')
BODY_START = '<!-- BOOK-CONTENT-START -->'
BODY_END = '<!-- BOOK-CONTENT-END -->'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes().decode('utf-8-sig'))


def contained(root, name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Expected a contained public POSIX filename')
    part = PurePosixPath(name)
    if name != part.as_posix() or part.is_absolute() or any(p in ('..', '.') or p.lower() in PRIVATE for p in part.parts):
        raise ValueError('Private or traversing public filename: '+name)
    if any(p.lower().startswith('.env') for p in part.parts) or part.name.lower() in {'readme.txt','initial_prompt.txt','agents.md'}:
        raise ValueError('Private source/prompt filename: '+name)
    root = root.resolve()
    cursor = root
    for segment in part.parts:
        cursor = cursor / segment
        if cursor.is_symlink():
            raise ValueError('Symbolic public path: '+name)
    resolved = cursor.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('Public path escapes project')
    return resolved


def body_sha(path):
    text = path.read_bytes().decode('utf-8')
    if text.count(BODY_START) != 1 or text.count(BODY_END) != 1:
        raise ValueError('Expected exactly one authored-body marker pair: '+path.name)
    body = text.split(BODY_START)[1].split(BODY_END)[0]
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.local=[]; self.programs=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='pre' and 'data-run' in attrs: self.programs.append(attrs['data-run'])
        if tag in {'a','img','script','link'}:
            value=attrs.get('href') or attrs.get('src')
            if value: self.local.append(value)


def draft_names(root):
    """Derive declared chapter artifacts and linked assets, not arbitrary files."""
    names=set(BASE_FILES)
    names.update('tools/plot_'+n+'.py' for n in PLOT_NAMES if (root/('tools/plot_'+n+'.py')).is_file())
    names.update(n for n in RECORDS if (root/n).is_file())
    names.add('assets/ternary-lab.js') if (root/'assets/ternary-lab.js').is_file() else None
    for sidecar in sorted(root.glob('chapter-*.meta.json')):
        meta=load(sidecar)
        page=meta.get('file',sidecar.name.replace('.meta.json','.html')); contained(root,page)
        if not re.fullmatch(r'chapter-\d{2}-[a-z0-9-]+\.html',page):
            raise ValueError('Invalid declared chapter name')
        names.update({page, sidecar.name})
        engine=meta.get('actual_engine',{})
        if engine.get('database'): names.add(engine['database'])
    from urllib.parse import unquote,urlsplit
    # Only existing declared root HTML is inspected. Linked resources are explicit.
    for name in sorted(n for n in names if n.endswith('.html')):
        path=contained(root,name)
        if not path.is_file(): continue
        parser=Links(); parser.feed(path.read_bytes().decode('utf-8'))
        for value in parser.local+parser.programs:
            parts=urlsplit(value)
            if parts.scheme or parts.netloc or not parts.path: continue
            target=unquote(parts.path)
            contained(root,target)
            if target.startswith(('assets/','code/','data/')):
                names.add(target)
    for document in ('README.md','WORKFLOW.md'):
        if not (root/document).is_file(): continue
        text=(root/document).read_bytes().decode('utf-8')
        for value in re.findall(r'!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)',text):
            value=value.strip('<>');parts=urlsplit(value)
            if parts.scheme or parts.netloc or not parts.path: continue
            target=unquote(parts.path);contained(root,target)
            if target.startswith(('assets/','code/','data/')): names.add(target)
    return names


def public_files(root=ROOT, release=False):
    """Return only the exact inventory; strict mode never ignores missing files."""
    root=Path(root).resolve()
    inventory=root/'content-inventory.json'
    if inventory.is_file():
        names=load(inventory).get('public_files')
        if not isinstance(names,list) or not names or len(names)!=len(set(names)):
            raise ValueError('content-inventory.json requires unique public_files')
        names=set(names)
    elif release:
        raise ValueError('Missing content-inventory.json')
    else:
        names=draft_names(root)
    if release:
        missing_names=(BASE_FILES|RECORDS)-names
        if missing_names: raise ValueError('Required files omitted from exact inventory: '+', '.join(sorted(missing_names)))
    paths=[contained(root,name) for name in sorted(names)]
    missing=[p.relative_to(root).as_posix() for p in paths if not p.is_file()]
    if missing: raise ValueError('Missing declared public files: '+', '.join(missing))
    return paths


def inspect(root=ROOT, mode='draft'):
    root=Path(root).resolve(); issues=[]; warnings=[]; files=[]; chapters=[]
    strict=mode!='draft'
    try: files=public_files(root,release=strict)
    except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        issues.append(str(exc))
        if strict:
            try: files=public_files(root,release=False)
            except (ValueError,KeyError,TypeError,json.JSONDecodeError): pass
    names={p.relative_to(root).as_posix() for p in files}
    # Fixed roots are required even for a draft. Final records are not invented.
    for name in sorted(BASE_FILES-names): issues.append('Missing required public artifact: '+name)
    for path in files:
        relative=path.relative_to(root).as_posix()
        if path.suffix.lower() in {'.vtt','.wav','.mp3','.mp4','.m4a','.pdf','.jsonl','.log','.db','.sqlite'}:
            issues.append('Source/private format in public package: '+relative)
        if path.suffix in TEXT_SUFFIXES:
            try: text=path.read_bytes().decode('utf-8-sig')
            except UnicodeDecodeError: issues.append('Non-UTF8 public text: '+relative); continue
            private_pattern=r'[A-Za-z]:[/\\]'+'Users'+r'[/\\]|/'+'Users'+r'/|/'+'home'+r'/[^/]+/'
            if re.search(private_pattern,text):
                issues.append('Absolute private user path: '+relative)
            if SECRET.search(text): issues.append('Credential-like payload: '+relative)
        if re.fullmatch(r'chapter-\d{2}-[a-z0-9-]+\.meta\.json',relative):
            try:
                meta=load(path); page=meta.get('file',path.name.replace('.meta.json','.html')); digest=body_sha(contained(root,page))
                engine=meta.get('actual_engine',{})
                if engine.get('database_sha256') and sha(contained(root,engine['database']))!=engine['database_sha256']:
                    issues.append('Declared public database digest mismatch: '+page)
                if meta['authored_body_sha256']!=digest: issues.append('Raw authored-body mismatch: '+page)
                if page not in names: issues.append('Chapter missing from inventory: '+page)
                parser=Links();parser.feed(contained(root,page).read_bytes().decode('utf-8'))
                if len(parser.programs)!=meta.get('executable_listings'):
                    issues.append('Declared executable-listing count mismatch: '+page)
                for program in parser.programs:
                    if not re.fullmatch(r'code/ch\d{2}_[a-z0-9_]+\.py',program) or program not in names:
                        issues.append('Missing/unsafe declared code download: '+str(program))
                chapters.append({'file':page,'body_sha256':digest,'chapter':meta['chapter'],
                                 'programs':parser.programs,'worked_solutions':meta.get('worked_solutions'),
                                 'recording_ids':[r['video_id'] for r in meta.get('recordings',[])]})
            except (ValueError,KeyError,TypeError,OSError) as exc: issues.append(str(exc))
    # HTML resources must belong to the same explicit public inventory.
    from urllib.parse import unquote,urlsplit
    for path in files:
        if path.suffix!='.html': continue
        parser=Links();parser.feed(path.read_bytes().decode('utf-8'))
        for value in parser.local:
            parts=urlsplit(value)
            if parts.scheme or parts.netloc or not parts.path: continue
            name=unquote(parts.path)
            try:
                target=contained(root,name)
                if target.relative_to(root).as_posix() not in names: issues.append('Linked file outside exact inventory: '+name)
            except ValueError as exc: issues.append(str(exc))
    if strict:
        try:
            for record_name in sorted(RECORDS):
                record=load(root/record_name)
                if not isinstance(record,dict):
                    raise ValueError('Required record must be a JSON object: '+record_name)
                if record_name not in {'content-inventory.json','editorial-review-summary.json','completion.json'} and not isinstance(record.get('passed'),bool):
                    raise ValueError('Required validation record needs boolean passed: '+record_name)
            manifest=load(root/'source-manifest.json'); inv=load(root/'content-inventory.json')
            recorded=inv.get('chapters',[])
            declared=[c['file'] for c in manifest['chapters']]
            if len(declared)!=len(set(declared)) or set(declared)!={c['file'] for c in chapters}:
                issues.append('Manifest and exact chapter inventory differ')
            overview=load(root/'book-overview.meta.json')
            if overview.get('body_sha256')!=body_sha(root/'book-overview.html'):
                issues.append('Orientation body digest mismatch')
            expected={c['file']:c['body_sha256'] for c in chapters}
            if len(recorded)!=len(expected) or {c['file']:c['body_sha256'] for c in recorded}!=expected:
                issues.append('Content inventory chapter hashes/set differ')
            coverage=load(root/'source-validation-summary.json')
            actual=coverage.get('recordings',[]); original=manifest['recordings']
            if len(original)!=77 or len({r['video_id'] for r in original})!=77 or {r.get('lesson') for r in original if isinstance(r.get('lesson'),int)}!=set(range(1,75)):
                issues.append('Full 77-item/74-numbered-lesson manifest required')
            if coverage.get('passed') is not True or coverage.get('complete') is not True:
                issues.append('Source coverage not complete/passed')
            if len(actual)!=len(original) or {r['video_id'] for r in actual}!={r['video_id'] for r in original}:
                issues.append('Coverage must retain every playlist identity exactly once')
            mapped={r['video_id']:r for r in actual}
            for r in original:
                row=mapped.get(r['video_id'],{})
                if not row.get('disposition') or row.get('reading_complete') is not True:
                    issues.append('Incomplete recording reading/disposition: '+r['video_id'])
                if r['video_id']!=load(root/'book-overview.meta.json').get('recording_id') and (row.get('included') is not True or not row.get('chapters')):
                    issues.append('Substantive recording not included: '+r['video_id'])
                for cfile in row.get('chapters',[]):
                    if cfile=='book-overview.html' and r['video_id']==load(root/'book-overview.meta.json').get('recording_id'): continue
                    entry=next((c for c in chapters if c['file']==cfile),{})
                    if r['video_id'] not in entry.get('recording_ids',[]): issues.append('Coverage/chapter recording mismatch: '+r['video_id'])
                if any(c not in expected and c!='book-overview.html' for c in row.get('chapters',[])):
                    issues.append('Coverage refers to unknown chapter: '+r['video_id'])
            editorial=load(root/'editorial-review-summary.json')
            reviews=editorial.get('chapters',[])
            if len(reviews)!=len(expected) or {c['file'] for c in reviews}!=set(expected):
                issues.append('Editorial accepted chapter set differs')
            for c in reviews:
                digest=expected.get(c['file']); rounds=c.get('rounds',[])
                accepted=[r for r in rounds if r.get('body_sha256')==digest and r.get('accepted') is True
                          and r.get('independent_of_author') is True
                          and all(r.get(k)==0 for k in ('blocking','major','minor'))]
                if c.get('accepted') is not True or c.get('body_sha256')!=digest or {r.get('round') for r in accepted}!={1,2}:
                    issues.append('Two current-digest accepted independent rounds required: '+c['file'])
                if len({r.get('reviewer_id') for r in accepted})<2 or any(not r.get('reviewer_id') for r in accepted):
                    issues.append('Two distinct reviewers required: '+c['file'])
            if load(root/'course-review.json').get('passed') is not True: issues.append('Course review not passed')
            # content mode is used inside source-free checking, before its own report exists.
            if mode in {'prepublication','release'}:
                for name in ('chapter-code-validation.json','reader-validation.json','package-validation.json','public-package-validation.json','source-free-validation.json'):
                    result=load(root/name)
                    if result.get('passed') is not True: issues.append('Local check not passed: '+name)
                    if result.get('chapter_hashes')!=expected: issues.append('Stale/missing chapter binding: '+name)
                reader=load(root/'reader-validation.json')
                required={p.name for p in files if p.suffix=='.html'}
                if not required.issubset(set(reader.get('pages_checked',[]))) or set(reader.get('widths',[]))!={390,1440}:
                    issues.append('Full two-width reader coverage required')
                export=load(root/'source-free-validation.json')
                if not export.get('git_archive_commit') or export.get('dependency_installation')!='isolated project-local venv from public requirements':
                    issues.append('Committed source-free export/dependency-install proof required')
                current_web={p.relative_to(root).as_posix():sha(p) for p in files if p.suffix in {'.html','.js','.css','.svg','.png','.jpg','.jpeg','.webp'}}
                if reader.get('web_input_sha256')!=current_web: issues.append('Reader input bytes are stale')
                current_input={p.relative_to(root).as_posix():sha(p) for p in files if p.relative_to(root).as_posix() not in RECORDS}
                if export.get('reproduction_input_sha256')!=current_input: issues.append('Source-free reproduction input bytes are stale')
                current_html={p.name:sha(p) for p in files if p.suffix=='.html'}
                if export.get('html_sha256')!=current_html: issues.append('Source-free HTML byte evidence is stale')
                if export.get('browser_checks_requested') is not True or export.get('byte_identical_html_rebuild') is not True:
                    issues.append('Source-free browser/HTML byte-identity proof required')
                completion=load(root/'completion.json')
                if completion.get('local_release_checks') is not True: issues.append('Local release completion flag not true')
                if mode=='release':
                    publication=load(root/'publication-validation.json')
                    if completion.get('complete') is not True or completion.get('publication') is not True: issues.append('Final completion/publication not true')
                    if publication.get('passed') is not True or publication.get('final') is not True: issues.append('Final live publication not passed')
                    current_payload={p.relative_to(root).as_posix():sha(p) for p in files if p.relative_to(root).as_posix()!='publication-validation.json'}
                    if publication.get('payload_sha256')!=current_payload: issues.append('Publication report payload set/hashes are stale')
                    if publication.get('readme_preview',{}).get('passed') is not True or publication.get('readme_preview',{}).get('preview_checked') is not True:
                        issues.append('Actual README preview verification required')
                    if publication.get('payload_sha256',{}).get('completion.json')!=sha(root/'completion.json'):
                        issues.append('Publication report does not bind final completion bytes')
        except (OSError,ValueError,KeyError,TypeError) as exc: issues.append('Required release evidence invalid: '+str(exc))
    else:
        warnings.append('Draft inspection only; final records, complete course coverage and publication not certified')
    return {'passed':not issues,'mode':mode,'scope':'Public payload and declared evidence audit, not new scientific review',
            'issues':issues,'warnings':warnings,'public_file_count':len(files),
            'chapter_hashes':{c['file']:c['body_sha256'] for c in chapters},
            'inventory':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in files
                         if p.relative_to(root).as_posix()!='public-package-validation.json'],
            'self_hash_exclusion':'Only this audit report is excluded from its own inventory hashes'}


def write_report(root,name,report):
    # Reports may be public named outputs or contained ignored-work outputs.
    relative=PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
        raise ValueError('Unsafe report output')
    if not (name in RECORDS or relative.parts[:1]==('work',)):
        raise ValueError('Report output must be a known record or inside work/')
    path=(root/name).resolve()
    if not path.is_relative_to(root.resolve()): raise ValueError('Report escapes project')
    cursor=root.resolve()
    for part in relative.parts:
        cursor=cursor/part
        if cursor.is_symlink(): raise ValueError('Symbolic report output')
    path.parent.mkdir(parents=True,exist_ok=True)
    if relative.parts[:1]!=('work',):
        def scrub(value):
            if isinstance(value,dict):return {k:scrub(v) for k,v in value.items()}
            if isinstance(value,list):return [scrub(v) for v in value]
            if isinstance(value,str):
                value=value.replace(str(root.resolve()),'.').replace(root.resolve().as_posix(),'.')
                return re.sub(r'\b[A-Za-z]:[\\/][^\n\r"<>]*', '<local-path>',value)
            return value
        report=scrub(report)
    path.write_bytes((json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--release',action='store_true')
    mode.add_argument('--prepublication',action='store_true')
    parser.add_argument('--output',default='work/release-tooling-implementation/public-audit.json')
    args=parser.parse_args()
    report=inspect(mode='release' if args.release else 'prepublication' if args.prepublication else 'draft')
    write_report(ROOT,args.output,report)
    print(json.dumps({k:v for k,v in report.items() if k!='inventory'},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
