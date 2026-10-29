"""Explicit public inventory shared by package and export tools.

No recursive directory export: strict promotion requires content-inventory.json.
"""
from audit_public import ROOT, BASE_FILES, RECORDS, contained, draft_names
from audit_public import public_files as _public_files


def public_files(root=ROOT, release=False):
    return _public_files(root, release=release)
