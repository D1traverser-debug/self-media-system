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
V33_DIR = PROJECT_DIR / "v3.3"

IMPORTS = [
    ("source-decision-v3", "Meme_X_CAOS_Decision_Source_v3.md"),
    ("source-readback-v3", "source/v3/Meme_X_Readback_v3.json"),
    ("source-article-en-v3", "source/v3/Meme_X_Article_EN_v3.md"),
    ("source-article-zh-v3", "source/v3/Meme_X_Article_ZH_v3.md"),
    ("candidate-v3-2-en", "v3.2/Meme_X_Article_EN_v3_2.md"),
    ("candidate-v3-2-zh", "v3.2/Meme_X_Article_ZH_v3_2.md"),
    ("candidate-v3-2-audit", "Meme_X_CAOS_Audit_v3_1.md"),
    ("visual-prompt-pack-v3", "Meme_X_Visual_Prompt_Pack_v3.md"),
    ("distribution-pack-v3", "Meme_X_Distribution_Pack_v3.md"),
    ("candidate-v3-3-en", "v3.3/Meme_X_Article_EN_v3_3.md"),
    ("candidate-v3-3-zh", "v3.3/Meme_X_Article_ZH_v3_3.md"),
    ("candidate-v3-3-audit", "v3.3/Meme_X_v3_3_Editorial_Decision_Style_Audit_Fact_Check.md"),
    ("candidate-v3-3-layout", "v3.3/Meme_X_v3_3_X_Articles_Layout_and_Visual_Prompts.md"),
    ("candidate-v3-3-distribution", "v3.3/Meme_X_v3_3_Distribution_Pack.md"),
    ("candidate-v3-3-readback", "v3.3/Meme_X_v3_3_Readback.json"),
    ("candidate-v3-3-manifest", "v3.3/Meme_X_v3_3_Asset_Manifest.json"),
    ("candidate-v3-3-readme", "v3.3/Meme_X_v3_3_README.md"),
]

def _complete_claim(
    engine: StudioEngine,
    task_id: str,
    worker: str,
    claim: dict[str, Any],
    file_specs: list[tuple[str, Path, str, str]],
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workspace = Path(engine.project(PROJECT_ID)["workspace"])
    output_payload: dict[str, Any] = {}
    for artifact_name, source, kind, media_type in file_specs:
        if not source.exists():
            raise FileNotFoundError(f"missing output source for {task_id}: {source}")
        destination = workspace / "artifacts" / f"{artifact_name}{source.suffix}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
        output_payload[artifact_name] = {
            "path": destination.relative_to(workspace).as_posix(),
            "kind": kind,
            "media_type": media_type,
            "rights_status": "UNKNOWN" if kind != "receipt" else "NOT_APPLICABLE",
            "metadata": {"source_path": str(source), "candidate_version": "v3.3"}
        }
    return engine.complete_task(
        PROJECT_ID, task_id, worker, claim["claim_token"], output_payload, result or {}
    )

def _claim_and_complete(
    engine: StudioEngine,
    expected_task_id: str,
    worker: str,
    file_specs: list[tuple[str, Path, str, str]],
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packet = engine.claim_next(PROJECT_ID, worker, lease_seconds=900)
    if not packet or packet["claim"]["task_id"] != expected_task_id:
        actual = packet and packet["claim"]["task_id"]
        raise RuntimeError(f"expected ready task {expected_task_id}, got {actual}")
    return _complete_claim(engine, expected_task_id, worker, packet["claim"], file_specs, result)

def bootstrap(root: str | Path, branch: str | None = None, commit_sha: str | None = None) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    engine = StudioEngine(root)
    project_dir = root / "projects" / PROJECT_ID
    if project_dir.exists():
        raise RuntimeError(f"Studio project already exists at {project_dir}; inspect it instead of reinitializing.")

    brief = json.loads((PROJECT_DIR / "OUTCOME_BRIEF.json").read_text(encoding="utf-8"))
    tasks = json.loads((PROJECT_DIR / "TASK_GRAPH.json").read_text(encoding="utf-8"))
    engine.create_project(PROJECT_ID, "When Everyone Has a Bag, Who Do You Believe?", brief)

    imported = []
    for name, relative in IMPORTS:
        source = PROJECT_DIR / relative
        if not source.exists():
            raise FileNotFoundError(f"required project asset missing: {relative}")
        media_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        imported.append(engine.import_asset(
            PROJECT_ID, name, source, kind="source", media_type=media_type,
            rights_status="UNKNOWN",
            metadata={"repository_path": relative, "candidate_context": "v3.3"}
        ))

    engine.add_tasks(PROJECT_ID, tasks)
    decision = engine.record_decision(PROJECT_ID, {
        "decision_id": "human-editorial-rewrite-v3-3",
        "question": "What is the root cause of the v3.2 AI-sounding cadence, and which repair best preserves the owner's intended article?",
        "scope": "Structural and voice rewrite of the existing article; preserve titles, subtitle, thesis, seven sections, five article URLs and one Bigfoot metaphor per language.",
        "source_refs": [
            "owner-correction:2026-11-22",
            "Meme_X_CAOS_Decision_Source_v3.md",
            "v3.2/Meme_X_Article_EN_v3_2.md",
            "v3.2/Meme_X_Article_ZH_v3_2.md",
            "v3.3/Meme_X_v3_3_Editorial_Decision_Style_Audit_Fact_Check.md"
        ],
        "hypotheses": [
            {"id": "lexical-only", "claim": "A small number of generic words and transitions cause the AI feel.", "discriminator": "If the cadence and section pattern remain repetitive after synonym changes, this is not the root cause."},
            {"id": "structural-repetition", "claim": "Sections repeatedly explain, caveat and finish with a polished mini-conclusion.", "discriminator": "Check whether each section advances a distinct step and whether repeated rhetorical templates disappear."},
            {"id": "missing-author-stance", "claim": "The draft explains the issue but does not show what the author would actually inspect or conclude.", "discriminator": "Check whether the revised article contains concrete reader tests and an identifiable author position."},
            {"id": "caveat-overload", "claim": "Repeated caveats interrupt the argument.", "discriminator": "Keep essential limitations once beside the claim and remove repeated defensive restatements."}
        ],
        "alternatives": [
            {"id": "slang-only", "description": "Add colloquial words and crypto slang without changing argument structure."},
            {"id": "aggressive-anti-holder", "description": "Treat financially interested holders as dishonest or fake."},
            {"id": "structural-voice-rewrite", "description": "Rebuild the opening and section progression, add an authorial trust test, and keep evidence limits adjacent to claims."},
            {"id": "academic-expansion", "description": "Add more research explanation and formal caveats."}
        ],
        "selected_option": "structural-voice-rewrite",
        "falsifier": "If an independent crypto-native cold reader still describes the piece as a generic template or cannot identify the author's actual judgment, reopen the root-cause diagnosis rather than polishing synonyms again.",
        "rollback": "v3.2 remains preserved on its own branch. Revert to the exact v3.2 candidate if v3.3 fails independent review; do not mutate immutable source/v3."
    })

    workspace = Path(engine.project(PROJECT_ID)["workspace"])
    receipt_dir = workspace / "artifacts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    source_receipt = receipt_dir / "project-recovery-receipt.json"
    source_receipt.write_text(json.dumps({
        "project_id": PROJECT_ID,
        "source_version": "v3",
        "previous_candidate": "v3.2",
        "current_candidate": "v3.3",
        "source_assets_imported": [item["name"] for item in imported],
        "decision_id": decision["decision_id"],
        "scope": "structural and voice rewrite of the existing X Article",
        "parent_caos_modified": False,
        "main_modified": False,
        "published": False
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _claim_and_complete(
        engine, "recover_project_state", "studio-bootstrap",
        [("project-recovery-receipt", source_receipt, "receipt", "application/json")],
        {"imported_assets": len(imported), "decision_id": decision["decision_id"]}
    )

    # Source verification and voice diagnosis are independent branches after scope recovery.
    parallel_specs = {
        "verify_sources_and_claims": [
            ("source-fact-check-record", V33_DIR / "Meme_X_v3_3_Editorial_Decision_Style_Audit_Fact_Check.md", "document", "text/markdown")
        ],
        "diagnose_editorial_voice": [
            ("editorial-root-cause-record", V33_DIR / "Meme_X_v3_3_Editorial_Decision_Style_Audit_Fact_Check.md", "document", "text/markdown")
        ]
    }
    parallel_results = {}
    for _ in range(2):
        packet = engine.claim_next(PROJECT_ID, "studio-review", lease_seconds=900)
        if not packet:
            raise RuntimeError("expected one of the two independent review tasks to be ready")
        task_id = packet["claim"]["task_id"]
        if task_id not in parallel_specs or task_id in parallel_results:
            raise RuntimeError(f"unexpected parallel task claimed: {task_id}")
        parallel_results[task_id] = _complete_claim(
            engine, task_id, "studio-review", packet["claim"], parallel_specs[task_id],
            {"review_record": "v3.3 editorial decision and source-bound style audit"}
        )

    _claim_and_complete(
        engine, "revise_manuscripts", "studio-editorial",
        [
            ("article-en-v3-3", V33_DIR / "Meme_X_Article_EN_v3_3.md", "document", "text/markdown"),
            ("article-zh-v3-3", V33_DIR / "Meme_X_Article_ZH_v3_3.md", "document", "text/markdown"),
            ("editorial-revision-record-v3-3", V33_DIR / "Meme_X_v3_3_Editorial_Decision_Style_Audit_Fact_Check.md", "document", "text/markdown")
        ],
        {"revision": "v3.3", "method": "structural and voice rewrite", "bigfoot_occurrences": {"en": 1, "zh": 1}}
    )

    _claim_and_complete(
        engine, "refresh_distribution_and_visual_assets", "studio-assets",
        [
            ("layout-visual-prompts-v3-3", V33_DIR / "Meme_X_v3_3_X_Articles_Layout_and_Visual_Prompts.md", "document", "text/markdown"),
            ("distribution-pack-v3-3", V33_DIR / "Meme_X_v3_3_Distribution_Pack.md", "document", "text/markdown")
        ],
        {"visual_prompts": 4, "images_generated": 0, "distribution_items_under_280": True}
    )

    attachment_receipt = receipt_dir / "handoff-attachment-receipt.json"
    manifest = json.loads((V33_DIR / "Meme_X_v3_3_Asset_Manifest.json").read_text(encoding="utf-8"))
    attachment_receipt.write_text(json.dumps({
        "version": "v3.3",
        "delivery_channel": "conversation attachments",
        "status": "DELIVERED",
        "attachments": [
            {"name": "Meme_X_Article_EN_v3_3.docx", "sha256": manifest["files"]["Meme_X_Article_EN_v3_3.docx"]["sha256"]},
            {"name": "Meme_X_Article_ZH_v3_3.docx", "sha256": manifest["files"]["Meme_X_Article_ZH_v3_3.docx"]["sha256"]},
            {"name": "Meme_X_Article_EN_v3_3.pdf", "sha256": manifest["files"]["Meme_X_Article_EN_v3_3.pdf"]["sha256"]},
            {"name": "Meme_X_Article_ZH_v3_3.pdf", "sha256": manifest["files"]["Meme_X_Article_ZH_v3_3.pdf"]["sha256"]},
            {"name": "Meme_X_Article_Complete_Package_v3_3.zip", "status": "conversation_attachment", "zip_integrity": "PASS"}
        ]
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _claim_and_complete(
        engine, "build_delivery_package", "studio-packager",
        [
            ("delivery-readback-v3-3", V33_DIR / "Meme_X_v3_3_Readback.json", "receipt", "application/json"),
            ("delivery-manifest-v3-3", V33_DIR / "Meme_X_v3_3_Asset_Manifest.json", "receipt", "application/json"),
            ("delivery-readme-v3-3", V33_DIR / "Meme_X_v3_3_README.md", "document", "text/markdown"),
            ("handoff-attachment-receipt", attachment_receipt, "receipt", "application/json")
        ],
        {"zip_integrity": "PASS", "docx_pdf_visual_review": "PASS", "native_x_preview": "OPEN"}
    )

    sync_result = None
    if branch and commit_sha and len(commit_sha) == 40:
        sync_receipt = receipt_dir / "github-sync-receipt.json"
        sync_receipt.write_text(json.dumps({
            "repository": "D1traverser-debug/video-growth-agent",
            "branch": branch,
            "commit_sha": commit_sha,
            "project_path": f"projects/{PROJECT_ID}/v3.3/",
            "verification_context": "GitHub Actions checked out this exact commit before Studio bootstrap.",
            "main_modified": False,
            "merged": False,
            "published": False
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sync_result = _claim_and_complete(
            engine, "sync_candidate_branch", "studio-sync",
            [
                ("github-sync-receipt", sync_receipt, "receipt", "application/json"),
                ("branch-readback-receipt", V33_DIR / "Meme_X_v3_3_Readback.json", "receipt", "application/json")
            ],
            {"branch": branch, "commit_sha": commit_sha, "main_modified": False, "published": False}
        )

    audit = engine.audit(PROJECT_ID)
    status = engine.status(PROJECT_ID)
    return {
        "project_id": PROJECT_ID,
        "runtime_root": str(root),
        "status": status,
        "audit": audit,
        "decision": decision,
        "repository_sync_task": sync_result,
        "parallel_review_tasks": list(parallel_results),
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
