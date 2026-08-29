"""SEO-friendly slug generation, e.g. /news/openai-launches-new-ai-model
instead of /article?id=123 (see backend/README.md's SEO section).

Deterministic: the same (title, url) always produces the same slug, so
re-ingesting an already-deduped article (ON CONFLICT DO NOTHING) never
needs a second slug. Uniqueness comes from an 8-hex-char suffix derived
from the article's URL rather than a DB lookup-and-retry loop — URLs are
already unique per `NewsArticle.url`, so this can't collide in practice.
"""

import hashlib
import re

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_MAX_SLUG_TITLE_LENGTH = 80


def slugify(title: str, url: str) -> str:
    base = _NON_ALNUM_RE.sub("-", title.lower()).strip("-")[:_MAX_SLUG_TITLE_LENGTH].strip("-")
    if not base:
        base = "article"
    suffix = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{suffix}"


def simple_slugify(text: str) -> str:
    """No uniqueness suffix — for names that are naturally stable and
    reused across many rows (e.g. `Entity.name`, `Author.name`), unlike
    `slugify()`'s per-article URLs. "Bitcoin" and "bitcoin" collapse to
    the same slug on purpose, which is how entity dedup by name works."""
    base = _NON_ALNUM_RE.sub("-", text.lower()).strip("-")[:_MAX_SLUG_TITLE_LENGTH].strip("-")
    return base or "entity"
