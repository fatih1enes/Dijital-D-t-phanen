"""Unit tests for GeminiCascadeManager and model tier cascade logic."""

from app.services.cascade_manager import CascadeModelProfile, GeminiCascadeManager


def test_cascade_manager_order():
    """Verify default ordering matches user specification: 3.8 -> 3.7 -> 3.6 -> 3.5 -> 3.5-lite."""
    mgr = GeminiCascadeManager()
    expected_order = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ]
    assert mgr.get_order() == expected_order
    for m in expected_order:
        assert m in mgr.profiles
        assert mgr.profiles[m].model_name == m


def test_cascade_profile_availability_and_rpm():
    """Verify that a profile respects its RPM limit and tracks usage."""
    profile = CascadeModelProfile(model_name="test-model", rpm=3, rpd=10)

    # Initially available
    avail, reason = profile.is_available()
    assert avail is True
    assert reason == "ok"

    # Record 3 calls
    profile.record_usage()
    profile.record_usage()
    profile.record_usage()
    assert profile.daily_requests == 3

    # Now RPM is full
    avail, reason = profile.is_available()
    assert avail is False
    assert "Dakikalık limit dolu" in reason


def test_cascade_503_fallback():
    """Verify that a 503 UNAVAILABLE error triggers immediate fallback to next model and cooldown."""
    mgr = GeminiCascadeManager()

    # Mock call function: fails on 3.8 with 503, succeeds on 3.7
    calls = []

    def mock_call(model_name: str):
        calls.append(model_name)
        if model_name == "gemini-3.8-flash":
            raise Exception(
                "503 The model is currently experiencing high demand. Please try again later."
            )
        return f"Response from {model_name}"

    result = mgr.execute_with_cascade(mock_call)

    assert result == "Response from gemini-3.7-flash"
    assert calls == ["gemini-3.8-flash", "gemini-3.7-flash"]

    # Verify gemini-3.8-flash is now in cooldown
    p_38 = mgr.profiles["gemini-3.8-flash"]
    avail_38, reason_38 = p_38.is_available()
    assert avail_38 is False
    assert "Geçici soğumada" in reason_38

    # Subsequent calls should immediately skip 3.8 and start from 3.7
    calls.clear()
    result2 = mgr.execute_with_cascade(mock_call)
    assert result2 == "Response from gemini-3.7-flash"
    assert calls == ["gemini-3.7-flash"]


def test_cascade_rpm_fluid_handoff():
    """Verify that when 3.8 fills its 5 RPM, the manager fluidly hands off to 3.7 without sleeping."""
    mgr = GeminiCascadeManager()
    p_38 = mgr.profiles["gemini-3.8-flash"]

    # Fill 3.8's 5 RPM
    for _ in range(5):
        p_38.record_usage()

    avail_38, _ = p_38.is_available()
    assert avail_38 is False

    # Next call should seamlessly choose 3.7
    calls = []

    def mock_call(model_name: str):
        calls.append(model_name)
        return f"Success: {model_name}"

    result = mgr.execute_with_cascade(mock_call)
    assert result == "Success: gemini-3.7-flash"
    assert calls == ["gemini-3.7-flash"]

    # Now fill 3.7's 5 RPM
    p_37 = mgr.profiles["gemini-3.7-flash"]
    for _ in range(5):
        p_37.record_usage()

    # Next call should seamlessly choose 3.6
    calls.clear()
    result = mgr.execute_with_cascade(mock_call)
    assert result == "Success: gemini-3.6-flash"
    assert calls == ["gemini-3.6-flash"]


def test_cascade_daily_exhaustion():
    """Verify that a 429 daily quota exhaustion marks model exhausted for the day and moves to next."""
    mgr = GeminiCascadeManager()

    calls = []

    def mock_call(model_name: str):
        calls.append(model_name)
        if model_name in ["gemini-3.8-flash", "gemini-3.7-flash"]:
            raise Exception("429 RESOURCE_EXHAUSTED: You have exceeded your current quota per day.")
        return f"Success from {model_name}"

    result = mgr.execute_with_cascade(mock_call)
    assert result == "Success from gemini-3.6-flash"
    assert calls == ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"]

    # Both 3.8 and 3.7 should now be exhausted for today
    assert mgr.profiles["gemini-3.8-flash"].is_exhausted_today is True
    assert mgr.profiles["gemini-3.7-flash"].is_exhausted_today is True

    # Next call will skip both directly and hit 3.6
    calls.clear()
    result = mgr.execute_with_cascade(mock_call)
    assert result == "Success from gemini-3.6-flash"
    assert calls == ["gemini-3.6-flash"]


def test_cascade_status_summary():
    """Verify status summary output matches expected structure for UI/API consumption."""
    mgr = GeminiCascadeManager()
    summary = mgr.get_status_summary()
    assert len(summary) == 5
    first = summary[0]
    assert first["model"] == "gemini-3.8-flash"
    assert first["rpm"] == 5
    assert first["rpd"] == 20
    assert first["available"] is True
    assert "daily_requests" in first
    assert "tier" in first


async def test_cascade_mode_settings_api(async_client):
    """Verify that gemini_cascade_mode and gemini_cascade_models can be updated and retrieved via API."""
    # Read initial
    res = await async_client.get("/api/settings")
    assert res.status_code == 200
    assert "gemini_cascade_mode" in res.json()
    assert "gemini_cascade_models" in res.json()

    # Update to False and set custom 4-model chain
    custom_models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
    res2 = await async_client.post(
        "/api/settings", json={"gemini_cascade_mode": False, "gemini_cascade_models": custom_models}
    )
    assert res2.status_code == 200
    res3 = await async_client.get("/api/settings")
    assert res3.json()["gemini_cascade_mode"] is False
    assert res3.json()["gemini_cascade_models"] == custom_models

    # Update back to True with 5 models
    default_5 = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ]
    res4 = await async_client.post(
        "/api/settings", json={"gemini_cascade_mode": True, "gemini_cascade_models": default_5}
    )
    assert res4.status_code == 200
    res5 = await async_client.get("/api/settings")
    assert res5.json()["gemini_cascade_mode"] is True
    assert res5.json()["gemini_cascade_models"] == default_5


def test_cascade_with_custom_4_models():
    """Verify that the cascade engine functions seamlessly when user configures only 4 models."""
    mgr = GeminiCascadeManager()
    four_models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
    mgr.configure_chain(four_models)

    assert mgr.get_order() == four_models
    assert len(mgr.get_order()) == 4

    # Execution works across these 4 models
    calls = []

    def mock_call(m: str):
        calls.append(m)
        if m == "gemini-3.8-flash":
            raise Exception("503 Overloaded")
        return f"Success: {m}"

    res = mgr.execute_with_cascade(mock_call)
    assert res == "Success: gemini-3.7-flash"
    assert calls == ["gemini-3.8-flash", "gemini-3.7-flash"]


def test_cascade_skips_empty_slots():
    """Verify that empty inputs or whitespace in the chain are stripped out."""
    mgr = GeminiCascadeManager()
    dirty_list = ["gemini-3.8-flash", "", "   ", "gemini-3.5-flash-lite", None]
    mgr.configure_chain(dirty_list)

    expected = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
    assert mgr.get_order() == expected
    assert len(mgr.get_order()) == 2
