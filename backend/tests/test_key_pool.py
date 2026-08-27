from app.services.gemini_key_pool import GeminiKeyPool


def test_key_pool_discovers_arbitrary_number_without_exposing_secrets():
    pool = GeminiKeyPool(environ={"GEMINI_API_KEY_3": "secret-3", "GEMINI_API_KEY_1": "secret-1"})
    first, second = pool.acquire(), pool.acquire()
    assert (first.index, second.index) == (1, 3)
    assert "secret" not in first.public_state()


def test_credential_failure_rotates_key():
    pool = GeminiKeyPool(environ={"GEMINI_API_KEY_1": "one", "GEMINI_API_KEY_2": "two"})
    first = pool.acquire()
    pool.report_failure(first.index, credential=True)
    assert pool.acquire().index == 2

