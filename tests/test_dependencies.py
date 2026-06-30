def test_chatbot_dependencies_importable():
    import bs4
    import dotenv
    import google.genai
    import rapidfuzz
    import requests

    assert bs4 is not None
    assert dotenv is not None
    assert google.genai is not None
    assert rapidfuzz is not None
    assert requests is not None
