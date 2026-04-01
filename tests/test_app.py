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


def register(client, username: str, password: str = "password123", role: str = "editor"):
    return client.post(
        "/auth/register",
        json={"username": username, "password": password, "role": role},
        headers={"Accept": "application/json"},
    )


def login(client, username: str, password: str = "password123"):
    return client.post(
        "/auth/login",
        json={"username": username, "password": password},
        headers={"Accept": "application/json"},
    )


def create_site(client, name: str, domain: str, tags: str = ""):
    return client.post(
        "/api/websites",
        json={
            "name": name,
            "domain": domain,
            "tech_stack": "Flask",
            "status": "active",
            "tags": tags,
        },
    )


def test_auth_required_for_api(client):
    response = client.get("/api/websites")
    assert response.status_code == 401
    assert response.get_json()["error"] == "authentication required"


def test_register_login_and_create_website(client):
    reg = register(client, "alice")
    assert reg.status_code == 201
    assert reg.get_json()["username"] == "alice"

    create = create_site(client, "Portfolio", "portfolio.example.com", tags="portfolio, personal")
    assert create.status_code == 201

    payload = client.get("/api/websites").get_json()
    assert len(payload) == 1
    assert set(payload[0]["tags"]) == {"portfolio", "personal"}


def test_multi_user_ownership_boundaries(client):
    register(client, "owner")
    create_site(client, "Owner Site", "owner.example.com")
    website_id = client.get("/api/websites").get_json()[0]["id"]
    client.post("/auth/logout", json={}, headers={"Accept": "application/json"})

    register(client, "other")
    denied = client.get(f"/api/websites/{website_id}/pages")
    assert denied.status_code == 200
    assert denied.get_json() == []


def test_page_markdown_and_preview(client):
    register(client, "author")
    create_site(client, "Docs", "docs.example.com")
    website_id = client.get("/api/websites").get_json()[0]["id"]

    create_page = client.post(
        f"/api/websites/{website_id}/pages",
        json={
            "title": "Guide",
            "slug": "guide",
            "seo_description": "Guide page",
            "content_markdown": "# Heading\n\n**bold** and [link](https://example.com)",
            "published": True,
        },
    )
    assert create_page.status_code == 201

    pages = client.get(f"/api/websites/{website_id}/pages").get_json()
    page_id = pages[0]["id"]

    preview = client.get(f"/pages/{page_id}")
    assert preview.status_code == 200
    assert b"<h1>Heading</h1>" in preview.data
    assert b"<strong>bold</strong>" in preview.data


def test_deployment_tracking_for_website(client):
    register(client, "deploy-user")
    create_site(client, "Main", "main.example.com")
    website_id = client.get("/api/websites").get_json()[0]["id"]

    create_deployment = client.post(
        f"/api/websites/{website_id}/deployments",
        json={
            "provider": "vercel",
            "project_name": "main-prod",
            "production_url": "https://main.example.com",
            "preview_url": "https://preview-main.example.com",
            "branch": "main",
            "status": "active",
        },
    )
    assert create_deployment.status_code == 201

    deployments = client.get(f"/api/websites/{website_id}/deployments").get_json()
    assert len(deployments) == 1
    assert deployments[0]["provider"] == "vercel"


def test_dashboard_search_filter_sort_and_tag(client):
    register(client, "filter-user")
    create_site(client, "Alpha Site", "alpha.example.com", tags="marketing")
    create_site(client, "Beta Blog", "beta.example.com", tags="blog, content")

    filtered = client.get("/api/websites?q=beta&tag=blog&status=active&sort=name_desc")
    assert filtered.status_code == 200
    names = [item["name"] for item in filtered.get_json()]
    assert "Beta Blog" in names
    assert "Alpha Site" not in names


def test_duplicate_domain_validation(client):
    register(client, "domain-user")
    payload = {
        "name": "Main Site",
        "domain": "main.example.com",
        "tech_stack": "Next.js",
        "status": "active",
        "tags": "",
    }
    first = client.post("/api/websites", json=payload)
    assert first.status_code == 201

    second = client.post("/api/websites", json=payload)
    assert second.status_code == 400
    assert second.get_json()["error"] == "domain already exists"


def test_delete_website_cascades_pages_and_deployments(client):
    register(client, "cascade-user")
    create_site(client, "Docs Site", "docs2.example.com")
    website_id = client.get("/api/websites").get_json()[0]["id"]

    page = client.post(
        f"/api/websites/{website_id}/pages",
        json={
            "title": "Guide",
            "slug": "guide",
            "seo_description": "",
            "content_markdown": "text",
            "published": True,
        },
    )
    assert page.status_code == 201

    deploy = client.post(
        f"/api/websites/{website_id}/deployments",
        json={
            "provider": "netlify",
            "project_name": "docs2",
            "production_url": "",
            "preview_url": "",
            "branch": "main",
            "status": "active",
        },
    )
    assert deploy.status_code == 201

    assert len(client.get(f"/api/websites/{website_id}/pages").get_json()) == 1
    assert len(client.get(f"/api/websites/{website_id}/deployments").get_json()) == 1

    delete_website = client.delete(f"/api/websites/{website_id}")
    assert delete_website.status_code == 200
    assert client.get(f"/api/websites/{website_id}/pages").get_json() == []
    assert client.get(f"/api/websites/{website_id}/deployments").get_json() == []
