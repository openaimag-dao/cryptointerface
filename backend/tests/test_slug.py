from app.utils.slug import slugify


def test_slugify_lowercases_and_hyphenates():
    slug = slugify("OpenAI Launches New AI Model", "https://example.com/a")
    assert slug.startswith("openai-launches-new-ai-model-")


def test_slugify_strips_punctuation():
    slug = slugify("Bitcoin's Price: Up 10%!", "https://example.com/b")
    assert " " not in slug
    assert "'" not in slug
    assert ":" not in slug
    assert "%" not in slug


def test_slugify_truncates_long_titles():
    long_title = "word " * 40
    slug = slugify(long_title, "https://example.com/c")
    base, _, suffix = slug.rpartition("-")
    assert len(base) <= 80
    assert len(suffix) == 8


def test_slugify_falls_back_when_title_has_no_alnum_chars():
    slug = slugify("!!!", "https://example.com/d")
    assert slug.startswith("article-")


def test_slugify_is_deterministic_for_the_same_input():
    first = slugify("Bitcoin rallies", "https://example.com/e")
    second = slugify("Bitcoin rallies", "https://example.com/e")
    assert first == second


def test_slugify_differs_by_url_for_identical_titles():
    first = slugify("Weekly recap", "https://example.com/f")
    second = slugify("Weekly recap", "https://example.com/g")
    assert first != second
