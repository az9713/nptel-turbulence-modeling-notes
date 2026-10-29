"""Headless offline reader checks; all browser state and artifacts are local."""
import json
import argparse
import hashlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.update(TEMP=str(ROOT / 'work/tmp'), TMP=str(ROOT / 'work/tmp'),
                  PLAYWRIGHT_BROWSERS_PATH=str(ROOT / 'work/browser-binaries'))
from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('chapters',nargs='*')
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--output',default=None)
    args=parser.parse_args()
    if args.full and args.chapters:
        parser.error('--full cannot be combined with selected chapters')
    (ROOT / 'work/author/render').mkdir(parents=True, exist_ok=True)
    issues, pages, errors = [], [], []
    drive = Path(os.environ.get('SystemDrive', 'C:') + '/')
    program_files = Path(os.environ.get('ProgramFiles', str(drive / 'Program Files')))
    program_files_x86 = Path(os.environ.get('ProgramFiles(x86)', str(drive / 'Program Files (x86)')))
    executable = Path(os.environ.get('BOOK_BROWSER', str(program_files / 'Google/Chrome/Application/chrome.exe')))
    if not executable.is_file():
        executable = program_files_x86 / 'Microsoft/Edge/Application/msedge.exe'
    from build_book import read
    manifest=json.loads(read(ROOT/'source-manifest.json'))
    declared=[c['file'] for c in manifest['chapters']]
    selected = args.chapters or declared
    if any(Path(name).name != name or not name.startswith('chapter-') or
           not name.endswith('.html') for name in selected):
        raise ValueError('Pass contained root chapter filenames')
    if any(name not in declared for name in selected):
        raise ValueError('Selected chapter missing from manifest')
    full=not args.chapters
    if full:
        from audit_public import public_files
        names=sorted(p.name for p in public_files() if p.suffix=='.html')
        if not set(declared).issubset(set(names)):
            raise ValueError('Full public inventory omits declared chapters')
    else:
        names = ['index.html'] + selected
        names += ['book-overview.html', 'source-map.html', 'references.html', 'numerical-lab.html']
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(ROOT / 'work/author/browser-profile'), headless=True,
            executable_path=str(executable), offline=True, reduced_motion='reduce',
            viewport={'width': 1440, 'height': 1000},
            args=['--disable-breakpad', '--disable-crash-reporter',
                  '--disable-background-networking', '--disable-gpu', '--no-first-run',
                  '--no-default-browser-check'])
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        for name in names:
            print('CHECK', name, flush=True)
            page.goto((ROOT / name).as_uri(), wait_until='load')
            page.wait_for_function(
                "document.documentElement.dataset.mathReady === 'true'")
            math_errors = page.locator('[data-mml-node="merror"], mjx-merror').count()
            count = page.locator('mjx-container').count()
            if math_errors:
                issues.append(name + ': math rendering errors')
            for width in [1440, 390]:
                page.set_viewport_size({'width': width, 'height': 1000})
                if page.evaluate('document.documentElement.scrollWidth > innerWidth+2'):
                    issues.append(name + ': page overflow at ' + str(width))
            from build_book import body_of, read
            body_sha = hashlib.sha256(body_of(read(ROOT / name)).encode('utf-8')).hexdigest()
            pages.append({'page': name, 'body_sha256': body_sha, 'rendered_math': count,
                          'math_errors': math_errors})
            if name == 'numerical-lab.html':
                page.wait_for_function('window.LAB_READY === true')
                uv = float(page.locator('#covariance-results').get_attribute('data-r12'))
                if abs(uv + 1) > 1e-12:
                    issues.append('Covariance lab initial value')
                r12 = float(page.locator('#channel-results').get_attribute('data-r12'))
                if abs(r12 + .08183333333333333) > 1e-12:
                    issues.append('Channel lab initial value')
                for c in [-1, 0, 1]:
                    page.locator('#correlation').evaluate(
                        '(e,v)=>{e.value=v;e.dispatchEvent(new Event("input"))}', c)
                    actual = float(page.locator('#covariance-results').get_attribute('data-r12'))
                    if abs(actual - 2*c) > 1e-12:
                        issues.append('Covariance lab endpoint')
                page.locator('#mean-gradient').evaluate(
                    'e=>{e.value=6000;e.dispatchEvent(new Event("input"))}')
                residual = float(page.locator('#channel-results').get_attribute('data-residual'))
                if abs(residual) > 1e-12:
                    issues.append('Channel lab balance')
                page.set_viewport_size({'width': 390, 'height': 844})
                page.screenshot(path=str(ROOT / 'work/author/render/lab-mobile.png'))
            if name.startswith('chapter-'):
                prefix = Path(name).stem
                if count == 0:
                    issues.append(name + ': missing mathematics')
                page.set_viewport_size({'width': 1440, 'height': 1000})
                page.screenshot(path=str(ROOT / f'work/author/render/{prefix}-desktop.png'))
                page.set_viewport_size({'width': 390, 'height': 844})
                page.screenshot(path=str(ROOT / f'work/author/render/{prefix}-mobile.png'))
                page.locator('#solutions-toggle').click()
                if page.locator('article details:not([open])').count():
                    issues.append('Solution expansion failed')
                page.locator('#solutions-toggle').click()
                if page.locator('article details[open]').count():
                    issues.append('Solution collapse failed')
                page.locator('#theme-toggle').click()
                if not page.locator('body').evaluate("e=>e.classList.contains('light')"):
                    issues.append('Theme switch failed')
                page.locator('#theme-toggle').click()
                page.locator('#text-toggle').click()
                if not page.locator('body').evaluate("e=>e.classList.contains('large-text')"):
                    issues.append('Text switch failed')
                page.locator('#text-toggle').click()
                page.locator('.copy-code').first.click()
                page.wait_for_function(
                    "document.querySelector('.copy-code').textContent === 'Copied'")
                page.evaluate("dispatchEvent(new Event('beforeprint'))")
                if page.locator('article details:not([open])').count():
                    issues.append('Print expansion failed')
                page.evaluate("dispatchEvent(new Event('afterprint'))")
                if page.locator('article details[open]').count():
                    issues.append('Print restoration failed')
                page.locator('pre[data-run]').first.scroll_into_view_if_needed()
                page.screenshot(path=str(ROOT / f'work/author/render/{prefix}-code-mobile.png'))
        page.goto((ROOT / 'index.html').as_uri(), wait_until='load')
        page.locator('#lecture-search').fill('momentum')
        if page.locator('[data-lecture]:visible').count() == 0:
            issues.append('Chapter search failed')
        page.locator('#lecture-search').fill('zzzz-no-match')
        if page.locator('[data-lecture]:visible').count():
            issues.append('Search filtering failed')
        context.close()
    issues.extend(errors)
    report = {'scope': 'Offline headless Chromium DOM, rendering and controls; '
                       'no human visual or scientific certification',
              'coverage':'full-manifest' if full else 'selected-chapters',
              'passed': not issues, 'issues': issues, 'pages': pages,
              'pages_checked':[p['page'] for p in pages],'widths':[1440,390],
              'chapter_hashes':{p['page']:p['body_sha256'] for p in pages if p['page'] in declared}}
    from audit_public import public_files,sha,write_report
    report['web_input_sha256']={p.relative_to(ROOT).as_posix():sha(p)
        for p in public_files() if p.suffix in {'.html','.js','.css','.svg','.png','.jpg','.jpeg','.webp'}}
    if args.output or full:
        write_report(ROOT,args.output or 'reader-validation.json',report)
    (ROOT / 'validation').mkdir(exist_ok=True)
    if full:
        (ROOT / 'validation/reader-checks.json').write_text(
            json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for name in selected:
        specific = ROOT / 'validation' / ('reader-' + Path(name).stem + '.json')
        specific.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'coverage':report['coverage'],
        'pages':len(pages),'widths':report['widths'],'issues':issues,
        'math_expressions':sum(p['rendered_math'] for p in pages)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
