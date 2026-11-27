"""Données mock et règles de gouvernance des tickets MaintiDoc.

Le serveur MCP ne fait qu'exposer ces fonctions. La règle centrale est qu'un
ticket ne peut être créé qu'avec un jeton d'approbation humaine lié au contenu.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import MOCK_DIR, ensure_dirs

HISTORY_PATH = MOCK_DIR / "maintenance_history.json"
TICKETS_PATH = MOCK_DIR / "tickets.json"
DRAFTS_PATH = MOCK_DIR / "ticket_drafts.json"
APPROVALS_PATH = MOCK_DIR / "approvals.json"
AUDIT_PATH = MOCK_DIR / "audit.jsonl"

DEFAULT_HISTORY = {
    "SAN-LAB-2000": [
        {"ticket": "INC-104", "date": "2026-09-18", "asset": "Fabric A",
         "summary": "Perte temporaire de chemin HBA1 ; surveillance", "status": "clos"},
        {"ticket": "INC-117", "date": "2026-10-02", "asset": "Disque B03",
         "summary": "Pré-alerte ; examen du groupe de protection", "status": "clos"},
        {"ticket": "INC-125", "date": "2026-10-20", "asset": "Volume VOL-DB",
         "summary": "Capacité à 88 % ; analyse de tendance", "status": "ouvert"},
        {"ticket": "INC-130", "date": "2026-10-25", "asset": "Contrôleur B",
         "summary": "Événement non reproductible ; suivi", "status": "ouvert"},
    ]
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_files() -> None:
    ensure_dirs()
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text(json.dumps(DEFAULT_HISTORY, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    for path in (TICKETS_PATH, DRAFTS_PATH, APPROVALS_PATH):
        if not path.exists():
            path.write_text("{}", encoding="utf-8")
    if not AUDIT_PATH.exists():
        AUDIT_PATH.touch()


def _read(path: Path) -> dict:
    _ensure_files()
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _audit(action: str, payload: dict) -> None:
    _ensure_files()
    with AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": _now(), "action": action, **payload},
                                ensure_ascii=False) + "\n")


def get_equipment_history(equipment_id: str) -> dict:
    history = _read(HISTORY_PATH)
    entries = history.get(equipment_id, [])
    _audit("get_equipment_history", {"equipment_id": equipment_id, "count": len(entries)})
    return {"ok": True, "equipment_id": equipment_id, "entries": entries}


def get_open_tickets(equipment_id: str) -> dict:
    tickets = _read(TICKETS_PATH)
    entries = [t for t in tickets.values()
               if t.get("equipment_id") == equipment_id and t.get("status") == "open"]
    _audit("get_open_tickets", {"equipment_id": equipment_id, "count": len(entries)})
    return {"ok": True, "equipment_id": equipment_id, "entries": entries}


def prepare_ticket(equipment_id: str, title: str, description: str) -> dict:
    """Prépare un brouillon ; aucune création n'a lieu ici."""
    drafts = _read(DRAFTS_PATH)
    draft_id = f"DRAFT-{uuid.uuid4().hex[:8]}"
    content = {"equipment_id": equipment_id, "title": title, "description": description}
    draft = {
        "draft_id": draft_id,
        "content": content,
        "content_hash": hashlib.sha256(
            json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "created_at": _now(),
        "status": "pending",
    }
    drafts[draft_id] = draft
    _write(DRAFTS_PATH, drafts)
    _audit("prepare_ticket", {"draft_id": draft_id, "equipment_id": equipment_id})
    return {"ok": True, "draft": draft}


def approve_ticket(draft_id: str, approver: str = "technicien-habilite") -> dict:
    """Simule l'approbation humaine et retourne un jeton lié au contenu."""
    drafts = _read(DRAFTS_PATH)
    if draft_id not in drafts:
        return {"ok": False, "error": "Brouillon inconnu"}
    draft = drafts[draft_id]
    token = f"APPROVAL-{uuid.uuid4().hex[:12]}"
    approvals = _read(APPROVALS_PATH)
    approvals[token] = {
        "draft_id": draft_id,
        "content_hash": draft["content_hash"],
        "approver": approver,
        "approved_at": _now(),
    }
    _write(APPROVALS_PATH, approvals)
    draft["status"] = "approved"
    _write(DRAFTS_PATH, drafts)
    _audit("approve_ticket", {"draft_id": draft_id, "approver": approver})
    return {"ok": True, "draft_id": draft_id, "approval_token": token}


def create_ticket(equipment_id: str, title: str, description: str,
                  approval_token: str, idempotency_key: str | None = None) -> dict:
    """Crée un ticket uniquement si le jeton correspond au contenu approuvé."""
    if idempotency_key:
        tickets = _read(TICKETS_PATH)
        for ticket in tickets.values():
            if ticket.get("idempotency_key") == idempotency_key:
                return {"ok": True, "ticket": ticket, "idempotent": True}

    approvals = _read(APPROVALS_PATH)
    approval = approvals.get(approval_token)
    if not approval:
        return {"ok": False, "error": "Jeton d'approbation absent ou inconnu"}

    content = {"equipment_id": equipment_id, "title": title, "description": description}
    content_hash = hashlib.sha256(
        json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if content_hash != approval["content_hash"]:
        return {"ok": False, "error": "Le contenu du ticket ne correspond pas à l'approbation"}

    tickets = _read(TICKETS_PATH)
    ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
    ticket = {
        "ticket_id": ticket_id,
        "equipment_id": equipment_id,
        "title": title,
        "description": description,
        "status": "open",
        "created_at": _now(),
        "approved_by": approval["approver"],
        "approval_token": approval_token,
        "idempotency_key": idempotency_key,
    }
    tickets[ticket_id] = ticket
    _write(TICKETS_PATH, tickets)
    _audit("create_ticket", {"ticket_id": ticket_id, "equipment_id": equipment_id,
                             "approved_by": approval["approver"]})
    return {"ok": True, "ticket": ticket, "idempotent": False}


def reset_mock() -> dict:
    """Réinitialise les données de démonstration."""
    for path in (TICKETS_PATH, DRAFTS_PATH, APPROVALS_PATH):
        _write(path, {})
    if AUDIT_PATH.exists():
        AUDIT_PATH.unlink()
    _ensure_files()
    return {"ok": True, "message": "Données mock réinitialisées"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Outils MCP MaintiDoc")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hist = sub.add_parser("history")
    p_hist.add_argument("equipment_id")

    p_prep = sub.add_parser("prepare")
    p_prep.add_argument("equipment_id")
    p_prep.add_argument("title")
    p_prep.add_argument("description")

    p_appr = sub.add_parser("approve")
    p_appr.add_argument("draft_id")

    sub.add_parser("reset")

    args = parser.parse_args()
    if args.command == "history":
        print(json.dumps(get_equipment_history(args.equipment_id), ensure_ascii=False, indent=2))
    elif args.command == "prepare":
        print(json.dumps(prepare_ticket(args.equipment_id, args.title, args.description),
                         ensure_ascii=False, indent=2))
    elif args.command == "approve":
        print(json.dumps(approve_ticket(args.draft_id), ensure_ascii=False, indent=2))
    elif args.command == "reset":
        print(json.dumps(reset_mock(), ensure_ascii=False, indent=2))
