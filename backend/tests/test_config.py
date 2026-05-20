from app.config import Settings


def test_settings_defaults():
    s = Settings(_env_file=None)
    assert s.confidence_threshold == 70
    assert s.timezone == "Asia/Kolkata"
