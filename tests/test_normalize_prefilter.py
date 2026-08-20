from ai_weather_signals.pipeline.normalize import author_hash, normalized_text, text_hash
from ai_weather_signals.pipeline.prefilter import prefilter


def test_normalization_and_stable_hash() -> None:
    assert normalized_text("  СИЛЬНЫЙ   дождь https://example.test/x ") == "сильный дождь"
    assert text_hash("Rain  now") == text_hash("RAIN now")
    assert author_hash("source", "42", "secret-salt") == author_hash("source", "42", "secret-salt")


def test_multilingual_prefilter() -> None:
    assert prefilter("У нас в Москве сильный дождь", {"москва"}).candidate
    assert prefilter("Heavy snow in Chicago right now", {"chicago"}).candidate
    assert not prefilter("Обычный рабочий день", {"москва"}).candidate


def test_southeast_asian_weather_terms() -> None:
    assert prefilter("Banjir bandang melanda Jakarta").candidate
    assert prefilter("Mưa lớn gây ngập tại Hà Nội").candidate
    assert prefilter("ฝนตกหนักและน้ำท่วมในเชียงใหม่").candidate
    assert prefilter("Bagyo at baha sa Manila").candidate
    assert prefilter("ទឹកជំនន់ និង ភ្លៀងខ្លាំង").candidate
    assert prefilter("ນ້ຳຖ້ວມ ແລະ ຝົນຕົກໜັກ").candidate


def test_global_regional_weather_terms() -> None:
    assert prefilter("Mafuriko na mvua kubwa yameikumba Nairobi").candidate
    assert prefilter("বন্যা ও ভারী বৃষ্টি ঢাকায়").candidate
    assert prefilter("台風と大雨が大阪を襲った").candidate
    assert prefilter("폭우와 홍수가 부산에서 발생했다").candidate
    assert prefilter("سیل و باران شدید در تهران").candidate
    assert prefilter("Powódź i ulewa w Warszawie").candidate
    assert prefilter("Су тасқыны Алматы маңында").candidate


def test_english_weather_terms_do_not_match_inside_words() -> None:
    assert not prefilter("I can feel the voice banks flowing through my veins").candidate
    assert not prefilter("It secured a liquor license during its time off").candidate
    assert not prefilter("Ukraine has lost export revenue").candidate
