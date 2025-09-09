from __future__ import annotations

from typing import Any, Dict, List

try:  # Prefer requests, fallback to httpx
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dep
    requests = None  # type: ignore

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

from ._utils import env, load_artifacts, write_export_result


def _http_post(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if requests is not None:
        try:
            r = requests.post(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(str(e))
    if httpx is not None:
        try:
            r = httpx.post(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()  # type: ignore[no-any-return]
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(str(e))
    raise RuntimeError("No HTTP client available (install requests or httpx)")


def export_to_trello(project_id: str) -> Dict[str, Any]:
    """Create a Trello board with EPIC lists and USR cards with task checklists."""
    key = env("TRELLO_KEY")
    token = env("TRELLO_TOKEN") or env("TRELLO_API_TOKEN")
    if not key or not token:
        return {"status": "failed", "error": "Missing TRELLO_KEY/TRELLO_TOKEN env vars"}

    try:
        artifacts = load_artifacts(project_id)
        backlog = artifacts.get("backlog") or {}
        epics: List[Dict[str, Any]] = backlog.get("epics") or []
        if not epics:
            return {"status": "failed", "error": "Missing backlog epics"}

        base = "https://api.trello.com/1"
        auth = {"key": key, "token": token}

        # Create board
        board = _http_post(f"{base}/boards/", {**auth, "name": f"{project_id} - SIGNUM"})
        board_id = board.get("id")
        board_url = board.get("url")
        if not board_id:
            return {"status": "failed", "error": "Failed to create board"}

        # For each epic, create a list and cards
        for epic in epics:
            list_obj = _http_post(
                f"{base}/boards/{board_id}/lists",
                {**auth, "name": f"EPIC: {epic.get('title') or epic.get('id')}"},
            )
            list_id = list_obj.get("id")
            if not list_id:
                continue
            for us in epic.get("user_stories") or []:
                title = str(us.get("benefit") or us.get("id") or "User Story")
                card = _http_post(
                    f"{base}/cards",
                    {**auth, "name": title, "idList": list_id},
                )
                card_id = card.get("id")
                if not card_id:
                    continue
                # Add checklist with tasks
                checklist = _http_post(
                    f"{base}/cards/{card_id}/checklists",
                    {**auth, "name": "Tasks"},
                )
                cl_id = checklist.get("id")
                if cl_id:
                    for task in us.get("tasks") or []:
                        _http_post(
                            f"{base}/checklists/{cl_id}/checkItems",
                            {**auth, "name": str(task.get("name") or task.get("id"))},
                        )

        result = {"status": "ok", "url": board_url}
        write_export_result(project_id, "trello", result)
        return result
    except Exception as e:  # noqa: BLE001
        result = {"status": "failed", "error": str(e)}
        write_export_result(project_id, "trello", result)
        return result
