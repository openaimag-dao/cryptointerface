from app.intelligence.news.classifier import classify, classify_portal_topic, detect_symbols


def test_detect_symbols_matches_watchlist_assets():
    symbols = detect_symbols("Bitcoin surges as Ethereum staking withdrawals spike")
    assert symbols == ["BTC", "ETH"]


def test_detect_symbols_ignores_unmentioned_assets():
    symbols = detect_symbols("Solana DEX volume surpasses expectations")
    assert symbols == ["SOL"]


def test_detect_symbols_empty_when_no_asset_mentioned():
    symbols = detect_symbols("Federal Reserve holds interest rates steady")
    assert symbols == []


def test_classify_bullish_article():
    result = classify(
        "Bitcoin ETF inflows hit record high as institutional demand accelerates",
        "Spot Bitcoin ETFs recorded their largest single-day inflow, a bullish signal for adoption.",
    )
    assert result.sentiment == "BULLISH"
    assert "BTC" in result.symbols
    assert result.category == "Institutional"
    assert result.confidence > 0


def test_classify_bearish_article():
    result = classify(
        "Exchange hacked, millions in Ethereum stolen",
        "A major exploit led to a security breach; regulators may pursue a lawsuit.",
    )
    assert result.sentiment == "BEARISH"
    assert result.category == "Security"
    assert result.impact_score > 30.0


def test_classify_neutral_article_with_no_keyword_hits():
    result = classify("Weekly market recap", "A quiet week for crypto markets overall.")
    assert result.sentiment == "NEUTRAL"
    assert result.confidence == 0.0


def test_classify_impact_score_bounded():
    result = classify(
        "SEC lawsuit, ETF ban, hack, bankruptcy, Federal Reserve interest rate hike",
        "regulation regulatory crackdown",
    )
    assert 0.0 <= result.impact_score <= 100.0


def test_classify_deterministic_same_input_same_output():
    first = classify("Bitcoin rallies", "Institutional adoption grows")
    second = classify("Bitcoin rallies", "Institutional adoption grows")
    assert first == second


def test_portal_topic_matches_ai_keywords_over_source_default():
    topic = classify_portal_topic("OpenAI releases new large language model", default_topic="CRYPTO")
    assert topic == "AI"


def test_portal_topic_matches_blockchain_keywords():
    topic = classify_portal_topic("Layer 2 rollup upgrade improves smart contract throughput", default_topic="CRYPTO")
    assert topic == "BLOCKCHAIN"


def test_portal_topic_falls_back_to_source_default_without_keyword_hits():
    assert classify_portal_topic("Weekly market recap", default_topic="CRYPTO") == "CRYPTO"
    assert classify_portal_topic("Weekly market recap", default_topic="INNOVATION") == "INNOVATION"


def test_portal_topic_deterministic_same_input_same_output():
    first = classify_portal_topic("Bitcoin ETF inflows hit record high", default_topic="CRYPTO")
    second = classify_portal_topic("Bitcoin ETF inflows hit record high", default_topic="CRYPTO")
    assert first == second
