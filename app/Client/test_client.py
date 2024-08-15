import pytest
from fastapi.testclient import TestClient
from main import app
from app.Client.service import *
from app.Client.schema import *
from app.Coach.service import *
from app.Coach.schema import *
from app.Client.service import get_db

client = TestClient(app)

# Test cases for client service functions
def test_create_database():
    db = get_db()
    assert create_database() is None

def test_get_db():
    db = get_db()
    assert db is not None

def test_get_client_organzation():
    db = get_db()
    email = "test@example.com"
    result = get_client_organzation(email, db)
    assert result is not None

def test_generate_own_member_id():
    member_id = generate_own_member_id()
    assert len(member_id) == 12

def test_create_client():
    db = get_db()
    client_data = RegisterClient(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
        mobile_number="1234567890",
    )
    result = create_client(client_data, db)
    assert result is not None

def test_create_client_for_app():
    db = get_db()
    client_data = RegisterClientApp(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
        mobile_number="1234567890",
    )
    result = create_client_for_app(client_data, db)
    assert result is not None

def test_create_client_organization():
    db = get_db()
    client_org_data = CreateClientOrganization(
        client_id=1,
        org_id=1,
    )
    result = create_client_organization(client_org_data, db)
    assert result is not None

def test_create_client_membership():
    db = get_db()
    client_membership_data = CreateClientMembership(
        client_id=1,
        membership_plan_id=1,
    )
    result = create_client_membership(client_membership_data, db)
    assert result is not None

def test_create_client_coach():
    db = get_db()
    client_id = 1
    coach_ids = [1, 2]
    result = create_client_coach(client_id, coach_ids, db)
    assert result is not None

def test_authenticate_client():
    db = get_db()
    email_address = "test@example.com"
    result = authenticate_client(email_address, db)
    assert result is not None

def test_login_client():
    db = get_db()
    email_address = "test@example.com"
    wallet_address = "0x1234567890"
    result = login_client(email_address, wallet_address, db)
    assert result is not None

def test_get_client_by_email():
    db = get_db()
    email_address = "test@example.com"
    result = get_client_by_email(email_address, db)
    assert result is not None

def test_get_business_clients():
    db = get_db()
    org_id = 1
    result = get_business_clients(org_id, db)
    assert result is not None

def test_update_client():
    db = get_db()
    client_id = 1
    client_data = ClientUpdate(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="1234567890",
        mobile_number="1234567890",
    )
    result = update_client(client_id, client_data, db)
    assert result is not None

def test_update_client_membership():
    db = get_db()
    client_id = 1
    membership_id = 1
    result = update_client_membership(client_id, membership_id, db)
    assert result is not None

def test_update_client_coach():
    db = get_db()
    client_id = 1
    coach_ids = [1, 2]
    result = update_client_coach(client_id, coach_ids, db)
    assert result is not None

def test_delete_client():
    db = get_db()
    client_id = 1
    result = delete_client(client_id, db)
    assert result is not None

def test_get_list_clients():
    db = get_db()
    org_id = 1
    result = get_list_clients(org_id, db)
    assert result is not None

def test_get_total_clients():
    db = get_db()
    org_id = 1
    result = get_total_clients(org_id, db)
    assert result is not None
    