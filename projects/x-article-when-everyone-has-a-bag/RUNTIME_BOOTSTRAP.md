# Video Studio Runtime Bootstrap — Meme X Article v3.6

This is a standalone Video Studio project. CAOS session-level governance may inform decisions but is not an imported runtime dependency.

From a checkout of `work/meme-x-article-bigfoot-2026-11-v3-6-full-audit`:

```bash
python -m pip install -e .
python projects/x-article-when-everyone-has-a-bag/bootstrap.py --root ./studio-work --branch work/meme-x-article-bigfoot-2026-11-v3-6-full-audit --commit-sha <40-character-commit-sha>
vga-studio --root ./studio-work status x-article-when-everyone-has-a-bag
vga-studio --root ./studio-work tasks x-article-when-everyone-has-a-bag
vga-studio --root ./studio-work audit x-article-when-everyone-has-a-bag
```

The bootstrap should import immutable v3, v3.2 and v3.5 evidence assets, v3.6 text/review/readback assets, register the v3.6 decision and task graph, and keep external human/platform/rights/owner gates pending. It must not mark unavailable human reviews as complete.

**Execution status in this conversation:** source was modified but live `StudioEngine` startup was not performed. A CI/pass claim requires actual checkout, installed runtime and test output. Do not equate the GitHub source synchronization or DOCX/PDF checks with a verified runtime execution.

Binary Word/PDF/ZIP handoff copies are delivered as chat attachments; source Markdown, audit, prompts, distribution, readback and hashes are in `v3.6/` on this isolated branch.
