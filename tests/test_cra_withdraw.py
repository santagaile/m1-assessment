"""CR-A: iesnieguma atsaukšana (tracker/CR-A.md). Viena rinda = viens tests."""

import logging

import pytest

from app import storage

REASON = "Problēma jau ir atrisināta"


def _create(client, payload, status=None):
    submission = client.post("/submissions", json=payload).json()
    if status is not None:
        storage.update_status(submission["id"], status)
    return submission


def _withdraw(client, submission_id, body):
    return client.post(f"/submissions/{submission_id}/withdraw", json=body)


def _status(client, submission_id):
    return client.get(f"/submissions/{submission_id}").json()["status"]


def _actions(client, submission_id):
    return [
        e["action"] for e in client.get(f"/submissions/{submission_id}/audit").json()
    ]


def _assert_invalid_state(response):
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"


def test_cra_ac1_received_withdrawn(client, valid_payload):
    submission = _create(client, valid_payload)
    response = _withdraw(client, submission["id"], {"reason": REASON})
    assert response.status_code == 200
    assert response.json()["status"] == "WITHDRAWN"
    # Precizējums: termiņš nemainās
    assert response.json()["dueDate"] == submission["dueDate"]


def test_cra_ac2_in_progress_withdrawn(client, valid_payload):
    submission = _create(client, valid_payload, "IN_PROGRESS")
    response = _withdraw(client, submission["id"], {"reason": REASON})
    assert response.status_code == 200
    assert response.json()["status"] == "WITHDRAWN"


def test_cra_ac3_answered_409(client, valid_payload):
    submission = _create(client, valid_payload, "ANSWERED")
    response = _withdraw(client, submission["id"], {"reason": REASON})
    _assert_invalid_state(response)
    assert _status(client, submission["id"]) == "ANSWERED"
    assert _actions(client, submission["id"]) == ["CREATE"]


def test_cra_ac4_second_withdraw_409(client, valid_payload):
    submission = _create(client, valid_payload)
    assert _withdraw(client, submission["id"], {"reason": REASON}).status_code == 200
    response = _withdraw(client, submission["id"], {"reason": REASON})
    _assert_invalid_state(response)
    assert _actions(client, submission["id"]) == ["CREATE", "WITHDRAW"]


def test_cra_ac5_unknown_id_404(client):
    response = _withdraw(client, "IES-2026-999999", {"reason": REASON})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize(
    "body",
    [{}, {"reason": None}, {"reason": "a" * 9}, {"reason": "a" * 501}],
    ids=["missing", "null", "9_chars", "501_chars"],
)
def test_cra_ac6_invalid_reason_400(client, valid_payload, body):
    submission = _create(client, valid_payload)
    response = _withdraw(client, submission["id"], body)
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert [d["field"] for d in error["details"]] == ["reason"]
    assert _status(client, submission["id"]) == "RECEIVED"
    assert _actions(client, submission["id"]) == ["CREATE"]


@pytest.mark.parametrize("length", [10, 500])
def test_cra_ac6_reason_length_boundaries_accepted(client, valid_payload, length):
    submission = _create(client, valid_payload)
    response = _withdraw(client, submission["id"], {"reason": "a" * length})
    assert response.status_code == 200


def test_cra_ac7_audit_has_withdraw_with_reason(client, valid_payload):
    submission = _create(client, valid_payload)
    _withdraw(client, submission["id"], {"reason": REASON})
    entries = client.get(f"/submissions/{submission['id']}/audit").json()
    assert entries[-1]["action"] == "WITHDRAW"
    assert entries[-1]["detail"] == REASON


def test_cra_ac8_no_personal_data_in_logs_or_errors(client, valid_payload, caplog):
    caplog.set_level(logging.DEBUG)
    received = _create(client, valid_payload)
    answered = _create(client, valid_payload, "ANSWERED")
    caplog.clear()

    responses = [
        _withdraw(client, received["id"], {"reason": "a" * 9}),
        _withdraw(client, received["id"], {"reason": REASON}),
        _withdraw(client, received["id"], {"reason": REASON}),
        _withdraw(client, answered["id"], {"reason": REASON}),
        _withdraw(client, "IES-2026-999999", {"reason": REASON}),
    ]
    storage.update_status(received["id"], "IN_PROGRESS")

    error_texts = [r.text for r in responses if r.status_code >= 400]
    assert len(error_texts) == 4
    for value in ("personalCode", "fullName", "email", "body"):
        secret = valid_payload[value]
        assert secret not in caplog.text
        for text in error_texts:
            assert secret not in text


def test_cra_forwarded_409_until_clarified(client, valid_payload):
    # Pagaidu lēmums: tracker/CR-A.md jautājums par FORWARDED ir atvērts.
    submission = _create(client, valid_payload, "FORWARDED")
    response = _withdraw(client, submission["id"], {"reason": REASON})
    _assert_invalid_state(response)
    assert _status(client, submission["id"]) == "FORWARDED"
