"""Inspect an explicit public package without copying private source material.

Defaults inspect the available draft only. --release requires all final content,
review, coverage, source-free and deployed evidence. Reproduction is performed
separately by tools/verify_source_free.py, avoiding recursive package checks.
"""
import argparse
import json
from audit_public import ROOT, contained, inspect, write_report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',action='store_true')
    parser.add_argument('--prepublication',action='store_true')
    parser.add_argument('--output',default='work/release-tooling-implementation/package-checks.json')
    args=parser.parse_args()
    if args.release and args.prepublication:parser.error('Choose one promotion gate')
    report=inspect(mode='release' if args.release else 'prepublication' if args.prepublication else 'draft')
    cases=['../escape.html','work/private.html','/outside.html','C:/outside.html',
           r'..\escape.html','assets/../../escape.py','WORK/private.html',
           './index.html','assets//book.css','README.txt','INITIAL_PROMPT.txt','AGENTS.md']
    rejected=0
    for name in cases:
        try:
            contained(ROOT,name)
            report['issues'].append('Unsafe public alias accepted: '+name)
        except ValueError:rejected+=1
    report['path_traversal_cases_rejected']=rejected
    report['passed']=not report['issues']
    write_report(ROOT,args.output,report)
    print(json.dumps({k:v for k,v in report.items() if k!='inventory'},indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
