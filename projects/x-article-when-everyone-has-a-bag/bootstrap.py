from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Any

from video_studio.engine import StudioEngine

PROJECT_ID = "x-article-when-everyone-has-a-bag"
PROJECT_DIR = Path(__file__).resolve().parent

IMPORTS = [
    ("source-decision-v3", "Meme_X_CAOS_Decision_Source_v3.md"),
    ("source-readback-v3", "source/v3/Meme_X_Readback_v3.json"),
    ("source-article-en-v3", "source/v3/Meme_X_Article_EN_v3.md"),
    ("source-article-zh-v3", "source/v3/Meme_X_Article_ZH_v3.md"),
    ("source-docx-en-v3", "source/v3/Meme_X_Article_EN_v3.docx"),
    ("source-docx-zh-v3", "source/v3/Meme_X_Article_ZH_v3.docx"),
    ("visual-prompt-pack-v3", "Meme_X_Visual_Prompt_Pack_v3.md"),
    ("distribution-pack-v3", "Meme_X_Distribution_Pack_v3.md"),
]

OUTPUTS = [
    ("article-en-v3-1", "Meme_X_Article_EN_v3_1.md", "document", "text/markdown"),
    ("article-zh-v3-1", "Meme_X_Article_ZH_v3_1.md", "document", "text/markdown"),
    ("article-en-docx-v3-1", "Meme_X_Article_EN_v3_1.docx", "document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("article-zh-docx-v3-1", "Meme_X_Article_ZH_v3_1.docx", "document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("revision-record-v3-1", "Meme_X_Editorial_Revision_Record_v3_1.md", "document", "text/markdown"),
]

def _complete_task_with_files(
    engine: StudioEngine,
    task_id: str,
    worker: str,
    file_specs: list[tuple[str, Path, str, str]],
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    claim_packet = engine.claim_next(PROJECT_ID, worker, lease_seconds=900)
    if not claim_packet or claim_packet["claim"]["task_id"] != task_id:
        raise RuntimeError(f"expected ready task {task_id}, got {claim_packet and claim_packet['claim']['task_id']}")
    claim = claim_packet["claim"]
    workspace = Path(engine.project(PROJECT_ID)["workspace"])
    output_payload: dict[str, Any] = {}
    for name, source, kind, media_type in file_specs:
        destination = workspace / "artifacts" / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        output_payload[name] = {
            "path": destination.relative_to(workspace).as_posix(),
            "kind": kind,
            "media_type": media_type,
            "rights_status": "UNKNOWN",
            "metadata": {"source_path": str(source), "source_version": "v3.1"}
        }
    return engine.complete_task(
        PROJECT_ID, task_id, worker, claim["claim_token"], output_payload, result or {}
    )

def bootstrap(root: str | Path, branch: str | None = None, commit_sha: str | None = None) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    engine = StudioEngine(root)
    project_dir = root / "projects" / PROJECT_ID
    if project_dir.exists():
        raise RuntimeError(f"Studio project already exists at {project_dir}; inspect it instead of reinitializing.")
    brief = json.loads((PROJECT_DIR / "OUTCOME_BRIEF.json").read_text(encoding="utf-8"))
    tasks = json.loads((PROJECT_DIR / "TASK_GRAPH.json").read_text(encoding="utf-8"))
    engine.create_project(PROJECT_ID, "When Everyone Has a Bag, Who Do You Believe?", brief)

    # Import immutable source and unchanged dependent assets first.
    imported = []
    for name, relative in IMPORTS:
        source = PROJECT_DIR / relative
        media_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        imported.append(engine.import_asset(
            PROJECT_ID, name, source, kind="source", media_type=media_type,
            rights_status="UNKNOWN", metadata={"repository_path": relative, "version": "v3"}
        ))

    engine.add_tasks(PROJECT_ID, tasks)
    decision = engine.record_decision(PROJECT_ID, {
        "decision_id": "bigfoot-keyword-placement",
        "question": "How should the keyword Bigfoot be integrated into the existing v3 X Article?",
        "scope": "One keyword-only edit in Section 01; preserve the existing article and argument.",
        "source_refs": ["owner-instruction:2026-11-21", "Meme_X_Article_EN_v3.md", "Meme_X_Article_ZH_v3.md"],
        "hypotheses": [
            {"id": "standalone-case", "claim": "Introduce Bigfoot as a new event or token case.", "discriminator": "Would require additional exposition or a new factual claim."},
            {"id": "metaphor-only", "claim": "Use Bigfoot as a brief metaphor within an existing sentence.", "discriminator": "Can satisfy keyword presence without changing thesis, structure or evidence."}
        ],
        "alternatives": [
            {"id": "standalone-case", "description": "Create a new Bigfoot case-study paragraph."},
            {"id": "metaphor-only", "description": "Replace one existing Section 01 sentence with a Bigfoot footprint metaphor."}
        ],
        "selected_option": "metaphor-only",
        "falsifier": "If readers interpret the phrase as a new Bigfoot topic or it distracts from the meme-versus-token distinction, revert to v3 and re-edit.",
        "rollback": "Restore the exact Section 01 paragraph from the immutable v3 source; keep all other assets unchanged."
    })

    workspace = Path(engine.project(PROJECT_ID)["workspace"])
    receipt_dir = workspace / "artifacts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    source_receipt = receipt_dir / "source-recovery-receipt.json"
    source_receipt.write_text(json.dumps({
        "project_id": PROJECT_ID, "source_version": "v3",
        "source_assets_imported": [item["name"] for item in imported],
        "decision_id": decision["decision_id"], "scope": "Bigfoot keyword only"
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    claim_packet = engine.claim_next(PROJECT_ID, "studio-bootstrap", lease_seconds=900)
    if not claim_packet or claim_packet["claim"]["task_id"] != "recover_source_state":
        raise RuntimeError("recover_source_state was not the next ready task")
    claim = claim_packet["claim"]
    engine.complete_task(
        PROJECT_ID, "recover_source_state", "studio-bootstrap", claim["claim_token"],
        {"source-recovery-receipt": {
            "path": "artifacts/source-recovery-receipt.json", "kind": "receipt",
            "media_type": "application/json", "rights_status": "NOT_APPLICABLE"
        }},
        {"source_assets": len(imported), "decision_id": decision["decision_id"]}
    )

    # Register the exact current manuscript bytes as outputs of the keyword-revision node.
    _complete_task_with_files(
        engine, "integrate_keyword", "studio-editorial",
        [(name, PROJECT_DIR / filename, kind, media_type) for name, filename, kind, media_type in OUTPUTS],
        {"revision": "v3.1", "scope": "one paragraph per language; Bigfoot keyword only"}
    )

    # Only complete repository-sync after a real branch and commit SHA are supplied.
    sync_result = None
    if branch and commit_sha and len(commit_sha) == 40:
        sync_task = engine.claim_next(PROJECT_ID, "studio-sync", lease_seconds=900)
        if not sync_task or sync_task["claim"]["task_id"] != "sync_assets_to_branch":
            raise RuntimeError("sync_assets_to_branch was not ready after manuscript integration")
        claim = sync_task["claim"]
        readback_src = PROJECT_DIR / "Meme_X_Readback_v3_1.json"
        sync_receipt_src = receipt_dir / "github-sync-receipt.json"
        sync_receipt_src.write_text(json.dumps({
            "repository": "D1traverser-debug/video-growth-agent",
            "branch": branch, "commit_sha": commit_sha,
            "project_path": f"projects/{PROJECT_ID}/",
            "verification_context": "GitHub Actions checked out this exact commit before Studio bootstrap.",
            "main_modified": False, "merged": False, "published": False
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        readback_dst = receipt_dir / "Meme_X_Readback_v3_1.json"
        shutil.copy2(readback_src, readback_dst)
        sync_result = engine.complete_task(
            PROJECT_ID, "sync_assets_to_branch", "studio-sync", claim["claim_token"],
            {
                "asset-readback-v3-1": {"path": "artifacts/Meme_X_Readback_v3_1.json", "kind": "receipt", "media_type": "application/json", "rights_status": "NOT_APPLICABLE"},
                "github-sync-receipt": {"path": "artifacts/github-sync-receipt.json", "kind": "receipt", "media_type": "application/json", "rights_status": "NOT_APPLICABLE"}
            },
            {"branch": branch, "commit_sha": commit_sha}
        )

    return {
        "project_id": PROJECT_ID,
        "runtime_root": str(root),
        "status": engine.status(PROJECT_ID),
        "audit": engine.audit(PROJECT_ID),
        "decision": decision,
        "repository_sync_task": sync_result,
        "events": engine.events(PROJECT_ID, limit=100)
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--branch", default=os.environ.get("GITHUB_REF_NAME"))
    parser.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA"))
    args = parser.parse_args()
    result = bootstrap(args.root, args.branch, args.commit_sha)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["audit"]["pass"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
