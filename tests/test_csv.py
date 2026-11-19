import csv
import io
from datetime import date

from tests.conftest import auth_headers
from tests.test_applications import make_app


def upload(client, text, headers=None, filename="applications.csv"):
    return client.post(
        "/applications/import",
        files={"file": (filename, text.encode("utf-8"), "text/csv")},
        headers=headers,
    )


def companies(client, headers=None):
    return sorted(a["company"] for a in client.get("/applications", headers=headers).json())


# Export

def test_export_includes_your_applications(auth_client):
    make_app(auth_client, company="Acme", notes="Referral, from Sam")  # comma tests quoting
    make_app(auth_client, company="Globex", status="interviewing")

    response = auth_client.get("/applications/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert {r["company"] for r in rows} == {"Acme", "Globex"}
    acme = next(r for r in rows if r["company"] == "Acme")
    assert acme["notes"] == "Referral, from Sam"
    assert acme["status"] == "applied"


def test_export_only_includes_your_own(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    make_app(client, headers=alice, company="Alice Co")
    rows = list(csv.DictReader(io.StringIO(client.get("/applications/export", headers=bob).text)))
    assert rows == []


def test_exported_file_can_be_imported_again(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    make_app(client, headers=alice, company="Acme", status="offer", job_url="https://acme.com/jobs/1")
    exported = client.get("/applications/export", headers=alice).text

    result = upload(client, exported, headers=bob).json()
    assert result["imported"] == 1
    bob_app = client.get("/applications", headers=bob).json()[0]
    assert (bob_app["company"], bob_app["status"], bob_app["job_url"]) == ("Acme", "offer", "https://acme.com/jobs/1")


# Import

def test_import_with_spreadsheet_style_headers(auth_client):
    text = (
        "Company Name,Position,Stage,Application Date,Link,Comments\n"
        "Acme,SWE Intern,Interview,11/03/2026,https://acme.com/jobs/1,Phone screen Friday\n"
        "Globex,Backend Intern,,,,\n"
    )
    result = upload(auth_client, text).json()
    assert result == {"imported": 2, "skipped": [], "warnings": []}

    apps = {a["company"]: a for a in auth_client.get("/applications").json()}
    assert apps["Acme"]["status"] == "interviewing"
    assert apps["Acme"]["date_applied"] == "2026-11-03"
    assert apps["Globex"]["status"] == "applied"  # blank status defaults to Applied
    assert apps["Globex"]["date_applied"] == date.today().isoformat()  # blank date defaults to today


def test_imported_applications_get_a_starting_history_event(auth_client):
    upload(auth_client, "company,role,status\nAcme,SWE Intern,offer\n")
    created = auth_client.get("/applications").json()[0]
    history = auth_client.get(f"/applications/{created['id']}/history").json()
    assert [(e["from_status"], e["to_status"]) for e in history] == [(None, "offer")]


def test_bad_rows_are_skipped_and_reported(auth_client):
    text = (
        "company,role,date applied,job url\n"
        "Acme,SWE Intern,2026-11-01,\n"
        ",Missing Company,2026-11-01,\n"
        "Globex,Intern,not a date,\n"
        "Initech,Intern,2026-11-01,not a url\n"
        "\n"
        "Hooli,Intern,2026-11-02,\n"
        "Umbrella,Intern,someday,\n"
    )
    result = upload(auth_client, text).json()
    assert result["imported"] == 2
    assert [problem["row"] for problem in result["skipped"]] == [3, 4, 5, 8]  # spreadsheet line numbers
    assert companies(auth_client) == ["Acme", "Hooli"]


def test_unknown_status_imports_as_applied_with_a_warning(auth_client):
    result = upload(auth_client, "company,role,status\nAcme,Intern,thinking about it\n").json()
    assert result["imported"] == 1
    assert result["warnings"][0]["row"] == 2
    assert auth_client.get("/applications").json()[0]["status"] == "applied"


def test_import_needs_company_and_role_columns(auth_client):
    response = upload(auth_client, "name,date\nAcme,2026-11-01\n")
    assert response.status_code == 400
    assert "company" in response.json()["detail"]


def test_import_rejects_files_over_one_megabyte(auth_client):
    big = "company,role\n" + "Acme,Intern\n" * 100_000
    assert upload(auth_client, big).status_code == 413


def test_import_only_adds_to_your_account(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    upload(client, "company,role\nAcme,Intern\n", headers=alice)
    assert companies(client, headers=bob) == []


def test_import_and_export_require_login(client):
    assert client.get("/applications/export").status_code == 401
    assert upload(client, "company,role\nAcme,Intern\n").status_code == 401
