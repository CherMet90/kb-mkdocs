# main.py
from pathlib import Path
import frontmatter
from datetime import datetime

DOCS_DIR = Path("docs")


def define_env(env):
    """
    Вызывается mkdocs-macros-plugin.
    """
    config = env.conf  # конфиг mkdocs (site_url, extra и т.п.)

    # базовый префикс, который мы задали в mkdocs.yml -> extra.base_path
    base_path = config.get("extra", {}).get("base_path", "/")

    # гарантируем ведущий и один завершающий слеш
    if not base_path.startswith("/"):
        base_path = "/" + base_path
    if not base_path.endswith("/"):
        base_path = base_path + "/"

    @env.macro
    def latest_posts(limit=10):
        """
        Возвращает список последних статей по дате (из фронт-маттера).
        """
        posts = []

        for md_path in DOCS_DIR.rglob("*.md"):
            if md_path.name == "latest.md":
                continue

            text = md_path.read_text(encoding="utf-8")
            try:
                post = frontmatter.loads(text)
            except Exception:
                continue

            meta = post.metadata or {}
            date_str = meta.get("date")
            title = meta.get("title")

            if not date_str or not title:
                continue

            try:
                date = datetime.fromisoformat(str(date_str))
            except ValueError:
                continue

            rel_path = md_path.relative_to(DOCS_DIR)
            rel_url = str(rel_path.with_suffix("")).replace("\\", "/") + "/"
            url = base_path + rel_url

            more_separator = "<!-- more -->"
            if more_separator in post.content:
                # Если разделитель есть, берем все до него
                excerpt = post.content.split(more_separator)[0].strip()
            else:
                # Если разделителя нет, используем фолбэк: первые 3 непустые строки
                body = post.content.strip().splitlines()
                non_empty = [line for line in body if line.strip() and not line.strip().startswith("#")]
                excerpt = "\n".join(non_empty[:3])

            posts.append(
                {
                    "title": title,
                    "date": date,
                    "url": url,
                    "excerpt": excerpt,
                }
            )

        posts.sort(key=lambda p: p["date"], reverse=True)
        return posts[: int(limit)]