# Textbook production workflow

This independent edition follows the complete Turbulence Modeling playlist by
Vagesh D. Narasimhamurthy, IIT Madras (NPTEL 112106453). All 77 positions are
retained. The 74 numbered lessons agree with the official outline by video
identity; the playlist itself is scrambled. Teaching order follows lesson
numbers while the source manifest preserves original positions.

Production applies transcript-grounded-textbook, rigorous-explainer, and
science-editor. Representative finished chapters from the owner's NPTEL
Continuum Mechanics and Algebra 1 editions were read end to end. Their
workflows and the Actuarial Probability and High Performance Scientific
Computing editions were inspected for pedagogy, provenance, reader behavior,
and validation methods.

1. Preserve official metadata, playlist identities, captions, media, and
   acquisition evidence privately in ignored work/. Match each numbered video
   to the official outline, hash stored captions, and compare caption endpoints
   with recording durations. These checks do not establish equation fidelity.
2. Read complete source text sequentially. Map major topic spans and distinguish
   source content, research extensions, and original teaching constructions.
   Hosted English captions are fallible; their hosting does not prove human
   authorship. Board equations require independent derivation or visual checking.
3. Develop a representative pilot before scaling. Write full prose, mathematical
   definitions and derivations, integrated primary references, original numerical
   examples, runnable code, and developed exercises with complete solutions.
   Use article depth diagnostics to locate omissions, never to pad text.
4. Self-edit and execute the pilot's code. Validate actual mathematical rendering,
   source spans, links, and offline desktop/mobile reader controls. The author
   cannot independently accept the resulting scientific manuscript.
5. The lead performs independent scientific review. Record at least two
   review/repair rounds and a final zero-blocking verdict tied to the exact
   UTF-8 authored body digest. A scientific rewriter is an author, not an
   independent reviewer of the rewritten text. Drafts remain fixed during review.
6. After pilot acceptance, author the remaining coherent chapters to the same
   calibrated standard. Retain chapter-specific provenance, limitations, code
   evidence, and exact digest-bound review status.
7. Build root-level HTML and sidecars with local CSS, JavaScript, and MathJax.
   Check local links, timestamps, notation, displayed output, browser behavior,
   public inventory, and source-free rebuild. Generated metadata and validation
   reports are not hashed into themselves or into the scientific body.
8. Publish only after the lead accepts all chapters and the package checks pass.
   Commit public files to the separate repository, enable GitHub Pages, and
   independently verify the live files. A successful push is not a live check.

The pilot passed two independent scientific reviews before full authoring.
All 74 numbered caption transcripts and all three supplementary machine
transcripts were read in full. The 25 chapters retain source spans and explicit
live-session administrative dispositions. Exact scientific acceptance is
recorded in each sidecar and the editorial summary. The public completion and
publication records determine the current release stage; their presence alone
does not establish a passed gate.
No comprehensive audiovisual review, formal proof verification, human expert
certification, or empirical validation of a turbulence model is implied.

Run public checks from the repository root:

    python tools/build_book.py
    python tools/validate_book.py
    python tools/check_code.py
    python tools/browser_check.py
    python tools/check_package.py

The code check requires every manifest chapter's declared listing and exact
download bytes. The default browser check covers the complete declared public
HTML inventory at 1440 and 390 pixels; a selected chapter run is explicitly a
subset and cannot satisfy the final gate. Reports bind exact chapter bodies and
current reader input bytes.

Final promotion additionally requires the strict public audit, a source-free
committed Git archive, a fresh project-local dependency installation and all
checks inside that export. Run the archive tool with --git --install --browser
and the contained installed browser executable; --release requires all three.
Its result records the commit and exact reproduced HTML. The public inventory
must match tracked files exactly. Internal inputs and credentials are excluded.

The live verifier fetches the declared payload and compares served bytes,
opens the deployed reader, checks the actual README preview, and probes the
publication report separately from its self-hash exclusion. Bootstrap with
truthful pending records, perform real checks, then promote completion and
repeat deployment and all final byte probes. After any record changes, the
final served completion and publication states and local/remote HEAD must agree.
No report hashes itself.

The reader rebuild uses only public files. Code examples use standard-library
Python 3.13. Exact floating-point output is bound to that reference minor version;
older interpreters can print slightly different roundoff despite equivalent
formulas. Static/code validation additionally requires Beautiful Soup. Headless
browser verification requires Playwright and installed Chrome or Edge; browser
profiles, temporary files and screenshots stay under this project. Optional
source inspection uses private sources and is not required to read or rebuild.
