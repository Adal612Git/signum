from __future__ import annotations

from typing import Any, Dict, List

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional
    requests = None  # type: ignore

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

from ._utils import b64, env, load_artifacts, write_export_result


def _http_json(
    method: str, url: str, headers: Dict[str, str], json_body: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    if requests is not None:
        try:
            r = requests.request(method, url, headers=headers, json=json_body, timeout=30)
            r.raise_for_status()
            return r.json() if r.content else {}
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(str(e))
    if httpx is not None:
        try:
            r = httpx.request(method, url, headers=headers, json=json_body, timeout=30)
            r.raise_for_status()
            return r.json() if r.content else {}  # type: ignore[no-any-return]
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(str(e))
    raise RuntimeError("No HTTP client available (install requests or httpx)")


def _docs_to_markdown(docs: Dict[str, Any]) -> str:
    parts: List[str] = []
    intro = str(docs.get("intro") or "").strip()
    usage = str(docs.get("usage") or "").strip()
    if intro:
        parts.append(f"# Project Documentation\n\n{intro}\n")
    if usage:
        parts.append(f"## Usage\n\n{usage}\n")
    if not parts:
        parts.append("# Project Documentation\n\n(Empty docs.json)\n")
    return "\n\n".join(parts)


def export_to_github(project_id: str) -> Dict[str, Any]:
    token = env("GITHUB_TOKEN")
    if not token:
        return {"status": "failed", "error": "Missing GITHUB_TOKEN env var"}

    try:
        artifacts = load_artifacts(project_id)
        backlog = artifacts.get("backlog") or {}
        docs = artifacts.get("docs") or {}

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "signum-export",
        }

        # Get current user
        me = _http_json("GET", "https://api.github.com/user", headers)
        owner = me.get("login")
        if not owner:
            return {"status": "failed", "error": "Cannot resolve GitHub user"}

        # Create repo
        repo_name = f"{project_id}-signum"
        repo = _http_json(
            "POST",
            "https://api.github.com/user/repos",
            headers,
            {"name": repo_name, "auto_init": False},
        )
        repo_full = repo.get("full_name") or f"{owner}/{repo_name}"
        repo_url = repo.get("html_url") or f"https://github.com/{repo_full}"

        # Create README.md from docs.json
        readme_md = _docs_to_markdown(docs)
        put_body = {
            "message": "Add README from docs.json",
            "content": b64(readme_md),
        }
        _http_json(
            "PUT", f"https://api.github.com/repos/{repo_full}/contents/README.md", headers, put_body
        )

        # Create issues per user story
        for epic in backlog.get("epics") or []:
            for us in epic.get("user_stories") or []:
                title = str(us.get("benefit") or us.get("id") or "User Story")
                tasks = us.get("tasks") or []
                body_lines = ["Tasks:"] + [f"- [ ] {t.get('name') or t.get('id')}" for t in tasks]
                body = "\n".join(body_lines)
                _http_json(
                    "POST",
                    f"https://api.github.com/repos/{repo_full}/issues",
                    headers,
                    {"title": title, "body": body},
                )

        result = {"status": "ok", "url": repo_url}
        write_export_result(project_id, "github", result)
        return result
    except Exception as e:  # noqa: BLE001
        result = {"status": "failed", "error": str(e)}
        write_export_result(project_id, "github", result)
        return result
