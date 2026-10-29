"""Execute every declared chapter listing and compare source bytes and output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import sys

from bs4 import BeautifulSoup
import pycodestyle
from build_book import ROOT, body_of, digest, public_path, read


class StyleReport(pycodestyle.BaseReport):
    """Collect source-relative diagnostics without exposing local paths."""

    def __init__(self, options):
        super().__init__(options)
        self.issues = []

    def error(self, line_number, offset, text, check):
        code = super().error(line_number, offset, text, check)
        if code:
            self.issues.append({
                'line': line_number, 'column': offset + 1,
                'code': code, 'message': text[5:],
            })
        return code


def source_style(source_bytes):
    """Full default PEP8 checks, including the 79-character line limit."""
    options = pycodestyle.StyleGuide(quiet=True, max_line_length=79).options
    report = StyleReport(options)
    source = source_bytes.decode('utf-8')
    pycodestyle.Checker(
        lines=source.splitlines(True), options=options, report=report,
    ).check_all()
    return report.issues


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='chapter-code-validation.json')
    parser.add_argument('--release',action='store_true')
    args=parser.parse_args()
    if sys.version_info[:2]!=(3,13):
        parser.error('Exact displayed-output validation requires reference Python3.13')
    from audit_public import write_report
    manifest=json.loads(read(ROOT/'source-manifest.json'))
    declared=[c['file'] for c in manifest['chapters']]
    reports,issues,expected_programs=[],[],[]
    hashes={}
    if len(declared)!=len(set(declared)):
        issues.append('Duplicate declared chapter')
    if {p.name for p in ROOT.glob('chapter-*.html')}!=set(declared):
        issues.append('Chapter files differ from manifest')
    for name in declared:
        chapter=public_path(name,'.html')
        hashes[name]=digest(body_of(read(chapter)))
        meta=json.loads(read(chapter.with_suffix('.meta.json')))
        soup = BeautifulSoup(body_of(read(chapter)), 'html.parser')
        outputs = soup.select('pre.output')
        listings=soup.select('pre[data-run]')
        count=meta.get('executable_listings')
        if not isinstance(count,int) or count<1 or len(listings)!=count:
            issues.append(name+': executable count missing/mismatched')
        if len(outputs)!=len(listings):
            issues.append(name+': every listing requires exactly one observed output')
        for i, listing in enumerate(listings):
            program = public_path(listing['data-run'], '.py')
            if not program.is_relative_to(ROOT / 'code'):
                raise ValueError('Listing must be in code/')
            source_bytes=program.read_bytes()
            style_issues=source_style(source_bytes)
            same_source=bool(listing.code) and listing.code.get_text().encode('utf-8')==source_bytes
            relative=program.relative_to(ROOT).as_posix()
            expected_programs.append(relative)
            (ROOT/'work/tmp').mkdir(parents=True,exist_ok=True)
            env = dict(os.environ, TEMP=str(ROOT / 'work/tmp'),
                       TMP=str(ROOT / 'work/tmp'), PYTHONDONTWRITEBYTECODE='1',
                       MPLCONFIGDIR=str(ROOT/'work/matplotlib'))
            process = subprocess.run(
                [sys.executable, '-B', '-X', 'utf8', str(program)],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
            expected = outputs[i].get_text() if i < len(outputs) else None
            same_output = expected == process.stdout
            reports.append({
                'chapter': chapter.name, 'body_sha256': hashes[name], 'listing_index':i,
                'program': relative,
                'source_sha256': hashlib.sha256(source_bytes).hexdigest(), 'embedded_source_matches': same_source,
                'pep8_issues': style_issues, 'style_passed': not style_issues,
                'displayed_output_matches': same_output, 'exit_code': process.returncode,
                'stdout': process.stdout, 'stderr': process.stderr,
                'passed': same_source and same_output and process.returncode == 0 and not style_issues})
    if len(expected_programs)!=len(set(expected_programs)):
        issues.append('Each code download requires one declared listing owner')
    inventory=ROOT/'content-inventory.json'
    auxiliary=[]
    if args.release and not inventory.is_file():
        issues.append('Release requires explicit content inventory')
    if inventory.is_file():
        inv=json.loads(read(inventory))
        inv_programs={n for n in inv['public_files'] if n.startswith('code/')}
        auxiliary=inv.get('auxiliary_programs',[])
        if len(auxiliary)!=len(set(auxiliary)) or any(not n.startswith('code/plot_') or not n.endswith('.py') for n in auxiliary):
            issues.append('Invalid explicit auxiliary generator set')
        if inv_programs!=set(expected_programs)|set(auxiliary):
            issues.append('Public code inventory differs from executed listing set')
        for row in inv.get('chapters',[]):
            entry=[r for r in reports if r['chapter']==row['file']]
            if 'programs' in row and set(row['programs'])!={r['program'] for r in entry}:
                issues.append('Inventory listing paths differ: '+row['file'])
    auxiliary_results=[]
    for name in auxiliary:
        source=public_path(name,'.py')
        parent=ROOT/'work/code-generator-checks'
        parent.mkdir(parents=True,exist_ok=True)
        sandbox=Path(tempfile.mkdtemp(prefix=source.stem+'-',dir=parent))
        (sandbox/'code').mkdir(parents=True,exist_ok=True)
        (sandbox/'assets').mkdir(exist_ok=True)
        (sandbox/'work/tmp').mkdir(parents=True,exist_ok=True)
        destination=sandbox/name
        shutil.copyfile(source,destination)
        env=dict(os.environ,TEMP=str(sandbox/'work/tmp'),TMP=str(sandbox/'work/tmp'),
            MPLCONFIGDIR=str(sandbox/'work/matplotlib'),PYTHONDONTWRITEBYTECODE='1')
        process=subprocess.run([sys.executable,'-B','-X','utf8',str(destination)],
            cwd=sandbox,env=env,capture_output=True,text=True,timeout=120)
        generated={p.relative_to(sandbox).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (sandbox/'assets').iterdir() if p.is_file()}
        style_issues=source_style(source.read_bytes())
        passed=process.returncode==0 and bool(generated) and not style_issues
        auxiliary_results.append({'program':name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'exit_code':process.returncode,'stdout':process.stdout,'stderr':process.stderr,
            'pep8_issues':style_issues,'style_passed':not style_issues,
            'generated_artifact_sha256':generated,'passed':passed,
            'scope':'Executed figure generator in isolated public-code copy; no claim byte-identical images across Matplotlib versions'})
        if not passed:issues.append('Auxiliary figure execution failed: '+name)
    issues.extend('Code/source/output failure: '+r['chapter'] for r in reports if not r['passed'])
    report = {'scope': 'Every manifest chapter/listing: exact UTF-8 source bytes and actual execution; not scientific review',
              'coverage':'full-manifest','issues':issues,'chapter_hashes':hashes,
              'chapters_checked':declared,'expected_programs':expected_programs,
              'auxiliary_programs':auxiliary_results,
              'passed': bool(reports) and not issues,'records': reports}
    write_report(ROOT,args.output,report)
    (ROOT / 'validation').mkdir(exist_ok=True)
    (ROOT / 'validation/code-checks.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'chapters':len(hashes),'listings':len(reports),
        'auxiliary_generators':len(auxiliary_results),'issues':issues}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
