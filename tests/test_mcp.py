from maintidoc.mcp_store import (
    approve_ticket,
    create_ticket,
    prepare_ticket,
    reset_mock,
)


def test_ticket_requires_approval():
    reset_mock()
    result = create_ticket(
        equipment_id="SAN-LAB-2000",
        title="Test",
        description="Sans jeton",
        approval_token="INVALID",
    )
    assert result["ok"] is False


def test_ticket_approval_and_idempotence():
    reset_mock()
    draft = prepare_ticket("SAN-LAB-2000", "Test", "Description")["draft"]
    approval = approve_ticket(draft["draft_id"])

    first = create_ticket(
        "SAN-LAB-2000", "Test", "Description",
        approval["approval_token"], idempotency_key="unit-test-1",
    )
    assert first["ok"] is True
    assert first["idempotent"] is False

    second = create_ticket(
        "SAN-LAB-2000", "Test", "Description",
        approval["approval_token"], idempotency_key="unit-test-1",
    )
    assert second["ok"] is True
    assert second["idempotent"] is True
    assert second["ticket"]["ticket_id"] == first["ticket"]["ticket_id"]


def test_modified_content_is_rejected():
    reset_mock()
    draft = prepare_ticket("SAN-LAB-2000", "Test", "Description")["draft"]
    approval = approve_ticket(draft["draft_id"])
    result = create_ticket(
        "SAN-LAB-2000", "Autre titre", "Description",
        approval["approval_token"],
    )
    assert result["ok"] is False
    assert "correspond" in result["error"]
