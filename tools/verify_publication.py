"""Verify deployed payload bytes and reader behavior; never publish or push.

Always pass --base and --repo. --init-pending creates truthful bootstrap evidence.
After updating final completion: run --final, deploy the updated report, then
repeat --final --no-write to verify the exact final records without changing them.
Only publication-validation.json is excluded from its own payload hashes; its
HTTP presence, JSON validity and final state are checked separately.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote,urljoin,urlsplit
from urllib.request import Request,urlopen
from audit_public import ROOT,inspect,load,public_files,sha,write_report,contained
from verify_source_free import browser_checks,environment


def fetch(url,accept=None):
    headers={'User-Agent':'Turbulence-notes-publication-check/1.0','Cache-Control':'no-cache'}
    if accept:headers['Accept']=accept
    with urlopen(Request(url,headers=headers),timeout=40) as response:
        status=response.status;data=response.read()
    if status!=200:raise ValueError('HTTP '+str(status)+' at '+url)
    return data


def verify_payload(files,base):
    def one(path):
        name=path.relative_to(ROOT).as_posix()
        try:
            remote=fetch(base.rstrip('/')+'/'+quote(name,safe='/')+'?book_probe='+str(time.time_ns()))
            return {'path':name,'http_status':200,'bytes':len(remote),'matches':remote==path.read_bytes()}
        except Exception as exc:return {'path':name,'matches':False,'error':str(exc)}
    with ThreadPoolExecutor(max_workers=4) as pool:return list(pool.map(one,files))


class Images(HTMLParser):
    def __init__(self):super().__init__();self.sources=[]
    def handle_starttag(self,tag,attrs):
        if tag=='img':self.sources.append(dict(attrs))


def readme_check(repo,base,preview,final):
    report={'passed':False};issues=[]
    try:
        local=(ROOT/'README.md').read_bytes()
        report['raw_readme_matches']=fetch('https://raw.githubusercontent.com/'+repo+'/HEAD/README.md')==local
        if not report['raw_readme_matches']:issues.append('Repository README bytes differ')
        text=local.decode('utf-8')
        images=re.findall(r'!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)',text)
        if preview is None and images:
            candidate=images[0].strip('<>')
            if not urlsplit(candidate).scheme:preview=candidate
        if not preview:
            if final:issues.append('Final README preview is missing')
            report.update(passed=not issues,issues=issues,preview_checked=False)
            return report
        path=contained(ROOT,preview)
        if not path.is_file():raise ValueError('Missing local README preview')
        if preview not in {p.relative_to(ROOT).as_posix() for p in public_files()}:
            raise ValueError('README preview outside public inventory')
        page=fetch('https://api.github.com/repos/'+repo+'/readme',accept='application/vnd.github.html').decode('utf-8')
        parser=Images();parser.feed(page)
        report['rendered_preview_present']=any(Path(preview).name in (im.get('src','')+' '+im.get('data-canonical-src','')) for im in parser.sources)
        report['pages_preview_bytes_match']=fetch(base.rstrip('/')+'/'+quote(preview,safe='/'))==path.read_bytes()
        report['repository_preview_bytes_match']=fetch('https://raw.githubusercontent.com/'+repo+'/HEAD/'+quote(preview,safe='/'))==path.read_bytes()
        report['preview']=preview;report['preview_checked']=True
        if not all(report[k] for k in ('rendered_preview_present','pages_preview_bytes_match','repository_preview_bytes_match')):
            issues.append('README rendered preview or actual preview bytes failed')
    except Exception as exc:issues.append(type(exc).__name__+': '+str(exc))
    report.update(passed=not issues,issues=issues)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True)
    parser.add_argument('--repo',required=True,help='Public GitHub owner/repository')
    parser.add_argument('--final',action='store_true')
    parser.add_argument('--release',action='store_true',help='Alias for --final')
    parser.add_argument('--init-pending',action='store_true')
    parser.add_argument('--no-write',action='store_true',help='Verify final evidence without rewriting it')
    parser.add_argument('--skip-browser',action='store_true',help='Diagnostic only; final mode forbids this')
    parser.add_argument('--browser-executable',default=os.environ.get('BOOK_BROWSER'))
    parser.add_argument('--preview')
    parser.add_argument('--allow-local-http',action='store_true',help='Diagnostic fixture use only')
    parser.add_argument('--output',default='work/release-tooling-implementation/publication-validation.json')
    args=parser.parse_args();args.final=args.final or args.release
    parts=urlsplit(args.base)
    if parts.username or parts.password or parts.query or parts.fragment or not parts.netloc:
        parser.error('Base must be a credential-free site URL without query/fragment')
    local=parts.scheme=='http' and parts.hostname in {'localhost','127.0.0.1','::1'} and args.allow_local_http
    if parts.scheme!='https' and not local:parser.error('HTTPS required except explicit local diagnostic fixtures')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.repo):parser.error('Expected owner/repository')
    if args.final and (args.skip_browser or local):parser.error('Final verification requires live HTTPS browser checks')
    if args.init_pending and (args.final or args.no_write):parser.error('Pending initialization is separate from final probes')
    if args.init_pending:
        report={'passed':False,'final':False,'status':'pending','base_url':args.base,'repository':args.repo,
                'scope':'Bootstrap placeholder; no deployed files or reader behavior verified',
                'payload_sha256':{},'self_hash_exclusion':'publication-validation.json only; served presence still required'}
        write_report(ROOT,args.output,report);print(json.dumps(report,indent=2));return 0
    report={'passed':False,'final':args.final,'status':'verification failed',
            'checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'base_url':args.base,'repository':args.repo,'issues':[],
            'self_hash_exclusion':'publication-validation.json only',
            'scope':'All other payload bytes are compared exactly; own report HTTP/JSON is checked separately. A written report must be deployed and verified again.'}
    try:
        # Content gate avoids a circular dependency on the live report being generated.
        audit=inspect(mode='prepublication' if args.final else 'draft')
        if not audit['passed']:raise ValueError('Local payload/content audit failed: '+str(audit['issues']))
        files=public_files(release=args.final)
        payload=[p for p in files if p.relative_to(ROOT).as_posix()!='publication-validation.json']
        report['payload_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in payload}
        report['chapter_hashes']=audit['chapter_hashes']
        report['payload_checks']=verify_payload(payload,args.base)
        for result in report['payload_checks']:
            if not result['matches']:report['issues'].append('Served bytes failed: '+result['path'])
        self_bytes=fetch(args.base.rstrip('/')+'/publication-validation.json?book_probe='+str(time.time_ns()))
        served_self=json.loads(self_bytes.decode('utf-8'))
        if not isinstance(served_self,dict) or not isinstance(served_self.get('passed'),bool):
            raise ValueError('Served publication report must be a JSON object with boolean passed')
        report['served_selfreport']={'http_status':200,'valid_json':True,'passed':served_self['passed'],
                                    'final':served_self.get('final')}
        if args.final and served_self.get('passed') is not True:report['issues'].append('Served publication report is not passed:true')
        completion=load(ROOT/'completion.json')
        served_completion=json.loads(fetch(args.base.rstrip('/')+'/completion.json?book_probe='+str(time.time_ns())).decode('utf-8'))
        report['served_completion']={'complete':served_completion.get('complete'),'publication':served_completion.get('publication')}
        if args.final and (completion.get('complete') is not True or completion.get('publication') is not True
                           or served_completion.get('complete') is not True or served_completion.get('publication') is not True):
            report['issues'].append('Final local/served completion is not complete/publication:true')
        if args.no_write:
            local_self=(ROOT/'publication-validation.json').read_bytes()
            report['served_selfreport']['exact_local_bytes']=self_bytes==local_self
            if self_bytes!=local_self:report['issues'].append('Served final publication report bytes differ')
            if args.final and (served_self.get('final') is not True or served_self.get('payload_sha256')!=report['payload_sha256']):
                report['issues'].append('Served final report does not bind the exact final payload/completion hashes')
        if not args.skip_browser:
            report['browser_checks']=browser_checks(ROOT,base=args.base,executable=args.browser_executable)
            if not report['browser_checks']['passed']:report['issues'].extend(report['browser_checks']['issues'])
        else:report['diagnostic_browser_omission']=True
        report['readme_preview']=readme_check(args.repo,args.base,args.preview,args.final)
        if not report['readme_preview']['passed']:report['issues'].extend(report['readme_preview']['issues'])
        env=environment(ROOT)
        local_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,env=env,text=True).strip()
        remote_head=subprocess.check_output(['git','ls-remote','origin','HEAD'],cwd=ROOT,env=env,text=True,timeout=40).split()[0]
        report.update(local_commit=local_head,remote_commit=remote_head)
        if local_head!=remote_head:report['issues'].append('Local and origin HEAD differ')
        if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,env=env,text=True).strip():
            report['issues'].append('Tracked working files differ from committed payload')
        report['passed']=not report['issues'];report['status']='passed' if report['passed'] else 'verification failed'
    except Exception as exc:report['issues'].append(type(exc).__name__+': '+str(exc))
    if not args.no_write:write_report(ROOT,args.output,report)
    else:print('Read-only final probe; publication evidence was not rewritten.')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
