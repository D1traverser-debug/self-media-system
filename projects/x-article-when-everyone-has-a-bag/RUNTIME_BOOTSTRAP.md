# Video Studio Runtime Bootstrap

This project uses the standalone Video Studio runtime declared by `video_studio/data/studio_manifest.json`. CAOS session-level decision governance may guide the agent's decisions, but this child runtime does not depend on or modify the CAOS runtime.

From a repository checkout:

```bash
python -m pip install -e .
python projects/x-article-when-everyone-has-a-bag/bootstrap.py --root ./studio-work --branch work/meme-x-article-bigfoot-2026-11-v3-3-editorial --commit-sha <40-character-commit-sha>
vga-studio --root ./studio-work status x-article-when-everyone-has-a-bag
vga-studio --root ./studio-work tasks x-article-when-everyone-has-a-bag
vga-studio --root ./studio-work audit x-article-when-everyone-has-a-bag
```

The bootstrap imports immutable v3 source assets, the v3.2 candidate and v3.3 deliverables; records the editorial decision; completes evidence review, root-cause diagnosis, manuscript revision, dependent-asset refresh and delivery readback; and completes repository sync only when a real branch and 40-character commit SHA are supplied.

Independent editor review, target-reader review, X-native preview, rights review, owner publication authorization and final release acceptance remain open. Word/PDF inspection is not a substitute for the native X preview.

The runtime root is project/workspace state, not a replacement for GitHub source assets. Do not commit local SQLite state unless the project owner explicitly chooses that storage policy.
