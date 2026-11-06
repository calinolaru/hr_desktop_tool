from datetime import datetime, timedelta, timezone

import pytest

import core.license_manager as license_manager
from core.trial_guard import TimeRollbackError


def test_time_rollback_is_reported_as_license_error(tmp_path, monkeypatch):
    license_path = tmp_path / "license.json"
    license_path.write_text('{"payload":"payload","signature":"signature"}', encoding="utf-8")
    payload = {
        "type": "trial",
        "company": "Example",
        "vat": "RO123",
        "machine": "machine-id",
        "issued_at": "2025-01-01T00:00:00+00:00",
        "expires": "2025-01-08T00:00:00+00:00",
    }

    monkeypatch.setattr(license_manager, "_license_file_path", lambda: license_path)
    monkeypatch.setattr(license_manager, "verify_signature", lambda *_: True)
    monkeypatch.setattr(license_manager, "b64decode_json", lambda _: payload)
    monkeypatch.setattr(license_manager, "get_machine_fingerprint", lambda: "machine-id")

    def reject_rollback():
        raise TimeRollbackError("clock moved backwards")

    monkeypatch.setattr(license_manager, "enforce_no_time_rollback", reject_rollback)

    with pytest.raises(license_manager.LicenseError, match="clock moved backwards"):
        license_manager.load_and_validate_license()


def test_license_file_must_contain_a_json_object(tmp_path, monkeypatch):
    license_path = tmp_path / "license.json"
    license_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(license_manager, "_license_file_path", lambda: license_path)

    with pytest.raises(license_manager.LicenseError, match="obiect JSON"):
        license_manager.load_and_validate_license()


def test_license_payload_must_decode_to_a_json_object(tmp_path, monkeypatch):
    license_path = tmp_path / "license.json"
    license_path.write_text('{"payload":"payload","signature":"signature"}', encoding="utf-8")
    monkeypatch.setattr(license_manager, "_license_file_path", lambda: license_path)
    monkeypatch.setattr(license_manager, "verify_signature", lambda *_: True)
    monkeypatch.setattr(license_manager, "b64decode_json", lambda _: [])

    with pytest.raises(license_manager.LicenseError, match="obiect JSON"):
        license_manager.load_and_validate_license()


@pytest.mark.parametrize(
    ("hours_remaining", "expected_days"),
    [(1, 1), (24, 1), (25, 2), (-1, 0)],
)
def test_days_until_expiry_rounds_up_remaining_days(
    hours_remaining, expected_days, monkeypatch
):
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    license_info = license_manager.LicenseInfo(
        license_type="trial",
        company="Example",
        vat="RO123",
        machine="machine-id",
        issued_at="2025-01-01T00:00:00+00:00",
        expires=(now + timedelta(hours=hours_remaining)).isoformat(),
    )
    monkeypatch.setattr(license_manager, "_utc_now", lambda: now)

    assert license_manager.days_until_expiry(license_info) == expected_days
