from app.intelligence.news.sources import NEWS_SOURCES

VALID_TOPICS = {"CRYPTO", "AI", "BLOCKCHAIN", "INNOVATION"}


def test_every_source_has_a_valid_default_topic():
    for source in NEWS_SOURCES:
        assert source.default_topic in VALID_TOPICS, f"{source.id} has an unknown default_topic {source.default_topic!r}"


def test_every_portal_topic_has_at_least_one_source():
    covered = {source.default_topic for source in NEWS_SOURCES}
    assert covered == VALID_TOPICS


def test_source_ids_are_unique():
    ids = [source.id for source in NEWS_SOURCES]
    assert len(ids) == len(set(ids))


def test_source_urls_are_https():
    for source in NEWS_SOURCES:
        assert source.rss_url.startswith("https://"), f"{source.id} is not served over https"
