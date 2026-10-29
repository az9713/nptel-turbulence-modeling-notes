"""Rebuild/test an exact public-only copy or committed git archive.

Exact displayed output uses the reference Python 3.13 interpreter.
Draft defaults do not certify course completion. --release requires complete
public content/review/coverage evidence, --git, --install and --browser.
All exports, environments, caches, browser profiles and logs stay under work/.
"""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import quote
from audit_public import ROOT, RECORDS, contained, inspect, load, public_files, sha, write_report

PLAYWRIGHT_REQUIREMENT='playwright==1.57.0'


def environment(folder):
    temporary=folder/'work/tmp'; temporary.mkdir(parents=True,exist_ok=True)
    return dict(os.environ,TEMP=str(temporary),TMP=str(temporary),
                PIP_CACHE_DIR=str(folder/'work/pip-cache'),
                PYTHONUSERBASE=str(folder/'work/python-user'),
                PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='',PYTHONNOUSERSITE='1',PIP_DISABLE_PIP_VERSION_CHECK='1',
                GCM_INTERACTIVE='Never',GIT_TERMINAL_PROMPT='0',
                PLAYWRIGHT_BROWSERS_PATH=str(folder/'work/browser-binaries'),
                OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')


def run_command(python,args,root,env,timeout=240):
    print('RUN',args[0] if args else 'python',flush=True)
    result=subprocess.run([str(python),'-B','-X','utf8',*args],cwd=root,env=env,
                          capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    return {'command':['python',*args],'returncode':result.returncode,
            'stdout':result.stdout,'stderr':result.stderr}


class Listings(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.items=[];self.current=None;self.kind=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='pre':
            if 'data-run' in attrs:
                self.current={'program':attrs['data-run'],'source':'','output':None};self.items.append(self.current);self.kind='source'
            elif 'output' in attrs.get('class','').split() and self.items:
                self.current=self.items[-1];self.current['output']='';self.kind='output'
    def handle_endtag(self,tag):
        if tag=='pre':self.kind=None
    def handle_data(self,text):
        if self.kind:self.current[self.kind]+=text


def exact_code_checks(root,python,env):
    records=[];issues=[]
    for meta_path in sorted(root.glob('chapter-*.meta.json')):
        meta=load(meta_path);page=contained(root,meta.get('file',meta_path.name.replace('.meta.json','.html')))
        parser=Listings();parser.feed(page.read_bytes().decode('utf-8'))
        if len(parser.items)!=meta.get('executable_listings'):
            issues.append('Listing coverage differs: '+page.name)
        for item in parser.items:
            name=item['program']
            if not re.fullmatch(r'code/ch\d{2}_[a-z0-9_]+\.py',name):
                raise ValueError('Unsafe code download')
            path=contained(root,name)
            same=path.read_bytes()==item['source'].encode('utf-8')
            result=run_command(python,[name],root,env,timeout=240)
            expected=item['output']
            output_matches=expected is not None and result['stdout'].strip('\n')==expected.replace('\r\n','\n').strip('\n')
            passed=same and output_matches and result['returncode']==0
            records.append(dict(result,program=name,chapter=page.name,
                                exact_source_bytes=same,displayed_output_matches=output_matches,passed=passed))
            if not passed:issues.append('Code/output mismatch: '+name)
    return {'passed':bool(records) and not issues,'issues':issues,'records':records}


def browser_checks(root,base=None,executable=None):
    """Actual headless two-width DOM/math/image/reader checks, local or live."""
    from playwright.sync_api import sync_playwright
    root=Path(root).resolve();state=root/'work/browser-checks';state.mkdir(parents=True,exist_ok=True)
    os.environ.update(environment(root))
    names=sorted(p.name for p in public_files(root) if p.suffix=='.html')
    from validate_book import math_inventory
    from build_book import body_of, read
    expected_math = {}
    for name in names:
        if not name.startswith('chapter-'):
            continue
        inventory = math_inventory(body_of(read(root / name)))
        if (not inventory['payload_sequence_matches']
                or inventory['unmatched_delimiters']):
            raise ValueError('Invalid raw/parsed source mathematics: ' + name)
        expected_math[name] = inventory['raw_count']
    issues=[];records=[]
    with sync_playwright() as p:
        launch={'headless':True,'args':['--disable-background-networking','--disable-breakpad','--disable-crash-reporter','--no-first-run']}
        if executable:launch['executable_path']=str(Path(executable).resolve())
        browser=p.chromium.launch(**launch)
        browser_version=browser.version
        try:
            for width in (1440,390):
                context=browser.new_context(viewport={'width':width,'height':1000},reduced_motion='reduce',offline=not bool(base))
                page=context.new_page();errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                for name in names:
                    print('BROWSER',width,name,flush=True)
                    url=base.rstrip('/')+'/'+quote(name) if base else (root/name).as_uri()
                    response=page.goto(url,wait_until='load',timeout=45000)
                    if base and (response is None or response.status!=200):issues.append(name+': HTTP not 200')
                    page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise',timeout=45000)
                    page.evaluate('async()=>{await MathJax.startup.promise;return true}')
                    math_errors=page.locator('[data-mml-node="merror"],mjx-merror').count()
                    count=page.locator('mjx-container').count()
                    authored_count=page.locator('#chapter-content mjx-container').count()
                    broken=page.locator('img').evaluate_all('(images)=>images.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute("src"))')
                    overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
                    if math_errors:issues.append(name+': MathJax errors')
                    if broken:issues.append(name+': broken images '+str(broken))
                    if overflow:issues.append(name+': page overflow '+str(width))
                    if name.startswith('chapter-'):
                        if authored_count==0:issues.append(name+': no rendered authored mathematics')
                        if authored_count!=expected_math[name]:issues.append(name+': authored math count differs from source')
                        page.locator('#solutions-toggle').click()
                        if page.locator('article details:not([open])').count():issues.append(name+': solution expansion')
                        page.locator('#solutions-toggle').click()
                        if page.locator('article details[open]').count():issues.append(name+': solution collapse')
                        for element,cls in [('#theme-toggle','light'),('#text-toggle','large-text')]:
                            before=page.locator('body').evaluate('(e,c)=>e.classList.contains(c)',cls)
                            page.locator(element).click()
                            after=page.locator('body').evaluate('(e,c)=>e.classList.contains(c)',cls)
                            if before==after:issues.append(name+': reader control '+element)
                            page.locator(element).click()
                        for button in page.locator('.copy-code').all():
                            button.click()
                            if button.inner_text() not in {'Copied','Select code to copy'}:
                                page.wait_for_timeout(100)
                            if button.inner_text() not in {'Copied','Select code to copy'}:issues.append(name+': copy-code control')
                        prior=page.locator('article details').evaluate_all('(d)=>d.map(e=>e.open)')
                        page.evaluate('dispatchEvent(new Event("beforeprint"))')
                        if page.locator('article details:not([open])').count():issues.append(name+': print expansion')
                        page.evaluate('dispatchEvent(new Event("afterprint"))')
                        if page.locator('article details').evaluate_all('(d)=>d.map(e=>e.open)')!=prior:issues.append(name+': print state restoration')
                    records.append({'page':name,'width':width,'rendered_math':count,'authored_math':authored_count,'expected_authored_math':expected_math.get(name),'math_errors':math_errors,'broken_images':broken,'overflow':overflow})
                issues.extend(errors);context.close()
        finally:browser.close()
    return {'passed':not issues,'issues':issues,'pages_checked':names,'widths':[390,1440],
            'records':records,'browser_executable':Path(executable).name if executable else 'Playwright managed Chromium',
            'browser_version':browser_version,'chapter_hashes':inspect(root)['chapter_hashes'],
            'web_input_sha256':{p.relative_to(root).as_posix():sha(p) for p in public_files(root) if p.suffix in {'.html','.js','.css','.svg','.png','.jpg','.jpeg','.webp'}},
            'scope':'Actual headless reader checks; no scientific or human visual certification'}


def documented_commands(root):
    """Only execute documented contained Python scripts, never shell commands."""
    result=[['tools/build_book.py'],['tools/validate_book.py'],['tools/check_code.py'],['tools/check_package.py']]
    for text_path in ('README.md','WORKFLOW.md'):
        text=(root/text_path).read_bytes().decode('utf-8')
        for line in text.splitlines():
            line=line.strip()
            if not line.startswith('python '):continue
            tokens=shlex.split(line)
            if len(tokens)!=2 or not tokens[1].endswith('.py'):continue
            script=contained(root,tokens[1])
            if script.name in {'audit_public.py','verify_source_free.py','verify_publication.py'}:continue
            if not script.is_file():raise ValueError('Documented command missing: '+line)
            if [tokens[1]] not in result:result.append([tokens[1]])
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',action='store_true')
    parser.add_argument('--git',action='store_true')
    parser.add_argument('--install',action='store_true',help='Install public requirements in a new local export venv')
    parser.add_argument('--browser',action='store_true')
    parser.add_argument('--browser-executable',default=os.environ.get('BOOK_BROWSER'))
    parser.add_argument('--output',default='work/release-tooling-implementation/source-free-validation.json')
    args=parser.parse_args()
    if sys.version_info[:2]!=(3,13):
        parser.error('Exact displayed-output reproduction requires Python 3.13; other versions may change compensated-sum residuals')
    if args.release and not (args.git and args.install and args.browser):parser.error('--release requires --git --install --browser')
    parent=ROOT/'work/release-tooling-implementation/exports';parent.mkdir(parents=True,exist_ok=True)
    export=Path(tempfile.mkdtemp(prefix='public-',dir=parent))
    report={'passed':False,'mode':'release-content' if args.release else 'draft',
            'scope':'Public-only reproduction; final publication/completion is a separate gate',
            'export':export.relative_to(ROOT).as_posix(),'checks':[],'issues':[],
            'git_archive_commit':None,'browser_checks_requested':args.browser,
            'dependency_installation':'Existing interpreter packages; not an installation proof'}
    try:
        start=inspect(mode='content' if args.release else 'draft')
        if not start['passed']:raise ValueError('Input audit failed: '+str(start['issues']))
        files=public_files(release=args.release);allowed={p.relative_to(ROOT).as_posix() for p in files}
        if args.git:
            env=environment(export)
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,env=env,text=True).strip()
            tracked=subprocess.check_output(['git','ls-tree','-r','--name-only','-z','HEAD'],cwd=ROOT,env=env).decode('utf-8').strip('\0').split('\0')
            if set(tracked)!=allowed:raise ValueError('Committed git inventory differs from exact public inventory')
            archive=subprocess.check_output(['git','archive','--format=tar','HEAD'],cwd=ROOT,env=env)
            with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
                members=bundle.getmembers()
                for member in members:
                    if not (member.isfile() or member.isdir()) or member.name.startswith('/') or '..' in Path(member.name).parts:
                        raise ValueError('Unsafe archive member')
                    if member.isfile() and member.name not in allowed:raise ValueError('Unexpected archive payload')
                for member in members:
                    if member.isfile():
                        target=contained(export,member.name);target.parent.mkdir(parents=True,exist_ok=True)
                        with bundle.extractfile(member) as source, target.open('wb') as output:
                            shutil.copyfileobj(source,output)
            report['git_archive_commit']=commit
        else:
            for source in files:
                target=export/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        reproduction_files=public_files(export,release=args.release)
        reproduction_input={p.relative_to(export).as_posix():sha(p) for p in reproduction_files if p.relative_to(export).as_posix() not in RECORDS}
        before={p.name:sha(p) for p in reproduction_files if p.suffix=='.html'}
        env=environment(export);python=Path(sys.executable)
        if args.browser_executable: env['BOOK_BROWSER']=str(Path(args.browser_executable).resolve())
        if args.install:
            install=run_command(python,['-m','venv',str(export/'work/venv')],export,env,timeout=120)
            report['checks'].append(install)
            if install['returncode']:raise ValueError('Could not create isolated venv')
            python=export/('work/venv/Scripts/python.exe' if os.name=='nt' else 'work/venv/bin/python')
            dependencies=['-m','pip','install','--disable-pip-version-check','-r','requirements.txt']
            if args.browser:dependencies.append(PLAYWRIGHT_REQUIREMENT)
            install=run_command(python,dependencies,export,env,timeout=1200)
            report['checks'].append(install)
            if install['returncode']:raise ValueError('Public dependency installation failed')
            report['dependency_installation']='isolated project-local venv from public requirements'
            report['checks'].append(run_command(python,['-m','pip','check'],export,env))
            report['checks'].append(run_command(python,['-m','pip','freeze'],export,env))
        for command in documented_commands(export):
            print('CHECK',' '.join(command),flush=True)
            report['checks'].append(run_command(python,command,export,env))
        code=exact_code_checks(export,python,env);report['code_checks']=code
        # Run browser checks in the chosen interpreter, not shared/private author modules.
        if args.browser:
            command=['tools/verify_source_free.py','--browser-worker']
            if args.browser_executable:command+=['--browser-executable',args.browser_executable]
            check=run_command(python,command,export,env,timeout=900);report['checks'].append(check)
            browser=load(export/'work/release-tooling-implementation/browser-worker.json')
            report['browser_checks']=browser
        audit=inspect(export,mode='content' if args.release else 'draft')
        changed=[name for name,digest in before.items() if sha(export/name)!=digest]
        report.update(public_file_count=len(files),html_count=len(before),changed_html=changed,
                      byte_identical_html_rebuild=not changed,html_sha256=before,
                      chapter_hashes=audit['chapter_hashes'],raw_source_files_available=False,
                      reproduction_input_sha256=reproduction_input)
        report['issues'].extend(audit['issues'])
        if changed:report['issues'].append('Source-free builder changed HTML bytes')
        if not code['passed']:report['issues'].extend(code['issues'])
        if args.browser and not report['browser_checks']['passed']:report['issues'].extend(report['browser_checks']['issues'])
        if any(r['returncode'] for r in report['checks']):report['issues'].append('A public command failed')
        report['passed']=not report['issues']
    except Exception as exc:report['issues'].append(type(exc).__name__+': '+str(exc))
    write_report(ROOT,args.output,report)
    print(json.dumps({k:v for k,v in report.items() if k not in {'checks','code_checks','browser_checks'}},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    if '--browser-worker' in sys.argv:
        parser=argparse.ArgumentParser();parser.add_argument('--browser-worker',action='store_true');parser.add_argument('--browser-executable')
        args=parser.parse_args();result=browser_checks(ROOT,executable=args.browser_executable)
        write_report(ROOT,'work/release-tooling-implementation/browser-worker.json',result)
        raise SystemExit(0 if result['passed'] else 1)
    raise SystemExit(main())
