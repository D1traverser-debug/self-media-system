# Video Studio Runtime Bootstrap

This project uses the standalone Video Studio runtime declared by `video_studio/data/studio_manifest.json`. It does not require or modify the CAOS runtime.

From a repository checkout:

```bash
python -m pip install -e .
python projects/x-article-when-everyone-has-a-bag/bootstrap.py --root ./studio-work --branch work/meme-x-article-bigfoot-2026-11 --commit-sha <40-character-commit-sha>
vga-studio --root ./studio-work status x-article-when-everyone-has-a-bag
vga-studio --root ./studio-work tasks x-article-when-everyone-has-a-bag
vga-studio --root ./studio-work audit x-article-when-everyone-has-a-bag
```

The bootstrap imports the v3 source assets, records the keyword-placement decision, completes source recovery and manuscript integration against the exact v3.1 bytes, and completes repository sync only when a branch and real commit SHA are supplied. Independent editor review, target-reader review, X-native preview and release acceptance remain open.

The runtime root is project/workspace state, not a replacement for the GitHub source assets. Do not commit local SQLite state unless the project owner explicitly chooses that storage policy.
