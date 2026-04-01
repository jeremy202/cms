from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cms import create_app


@pytest.fixture()
def client():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        app = create_app(
            {
                "TESTING": True,
                "DATABASE": str(db_path),
                "SECRET_KEY": "test",
            }
        )
        with app.test_client() as client:
            yield client


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Website Management CMS" in response.data


def test_create_website_and_page(client):
    create_website = client.post(
        "/websites/new",
        data={
            "name": "Portfolio",
            "domain": "portfolio.example.com",
            "tech_stack": "Flask",
            "status": "active",
        },
        follow_redirects=True,
    )
    assert create_website.status_code == 200
    assert b"Website created." in create_website.data

    websites = client.get("/api/websites")
    payload = websites.get_json()
    assert len(payload) == 1
    website_id = payload[0]["id"]

    create_page = client.post(
        f"/websites/{website_id}/pages/new",
        data={
            "title": "About",
            "slug": "about",
            "seo_description": "About page",
            "published": "on",
        },
        follow_redirects=True,
    )
    assert create_page.status_code == 200
    assert b"Page created." in create_page.data

    pages = client.get(f"/api/websites/{website_id}/pages")
    page_payload = pages.get_json()
    assert len(page_payload) == 1
    assert page_payload[0]["slug"] == "about"


def test_duplicate_domain_validation(client):
    payload = {
        "name": "Main Site",
        "domain": "main.example.com",
        "tech_stack": "Next.js",
        "status": "active",
    }
    first = client.post("/websites/new", data=payload)
    assert first.status_code == 302

    second = client.post("/websites/new", data=payload)
    assert second.status_code == 400
    assert b"That domain already exists." in second.data


def test_delete_website_cascades_pages(client):
    create_website = client.post(
        "/websites/new",
        data={
            "name": "Docs Site",
            "domain": "docs.example.com",
            "tech_stack": "Flask",
            "status": "active",
        },
    )
    assert create_website.status_code == 302

    website_id = client.get("/api/websites").get_json()[0]["id"]
    create_page = client.post(
        f"/websites/{website_id}/pages/new",
        data={"title": "Guide", "slug": "guide", "seo_description": "", "published": "on"},
    )
    assert create_page.status_code == 302
    assert len(client.get(f"/api/websites/{website_id}/pages").get_json()) == 1

    delete_website = client.post(f"/websites/{website_id}/delete")
    assert delete_website.status_code == 302
    assert client.get(f"/api/websites/{website_id}/pages").get_json() == []
