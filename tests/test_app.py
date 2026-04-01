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
        data={"username": username, "password": password, "role": role},
        follow_redirects=True,
    )


def login(client, username: str, password: str = "password123"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def create_site(client, name: str, domain: str, tags: str = ""):
    return client.post(
        "/websites/new",
        data={
            "name": name,
            "domain": domain,
            "tech_stack": "Flask",
            "status": "active",
            "tags": tags,
        },
        follow_redirects=True,
    )


def test_auth_required_for_dashboard(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_register_login_and_create_website(client):
    reg = register(client, "alice")
    assert reg.status_code == 200
    assert b"Account created and signed in." in reg.data

    create = create_site(client, "Portfolio", "portfolio.example.com", tags="portfolio, personal")
    assert create.status_code == 200
    assert b"Website created." in create.data

    api = client.get("/api/websites")
    payload = api.get_json()
    assert len(payload) == 1
    assert set(payload[0]["tags"]) == {"portfolio", "personal"}


def test_multi_user_ownership_boundaries(client):
    register(client, "owner")
    create_site(client, "Owner Site", "owner.example.com")
    website_id = client.get("/api/websites").get_json()[0]["id"]
    client.post("/auth/logout", follow_redirects=True)

    register(client, "other")
    denied = client.get(f"/websites/{website_id}/pages", follow_redirects=False)
    assert denied.status_code == 404


def test_page_markdown_and_preview(client):
    register(client, "author")
    create_site(client, "Docs", "docs.example.com")
    website_id = client.get("/api/websites").get_json()[0]["id"]

    create_page = client.post(
        f"/websites/{website_id}/pages/new",
        data={
            "title": "Guide",
            "slug": "guide",
            "seo_description": "Guide page",
            "content_markdown": "# Heading\\n\\n**bold** and [link](https://example.com)",
            "published": "on",
        },
        follow_redirects=True,
    )
    assert create_page.status_code == 200
    assert b"Page created." in create_page.data

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
        f"/websites/{website_id}/deployments/new",
        data={
            "provider": "vercel",
            "project_name": "main-prod",
            "production_url": "https://main.example.com",
            "preview_url": "https://preview-main.example.com",
            "branch": "main",
            "status": "active",
        },
        follow_redirects=True,
    )
    assert create_deployment.status_code == 200
    assert b"Deployment saved." in create_deployment.data

    deployments = client.get(f"/api/websites/{website_id}/deployments").get_json()
    assert len(deployments) == 1
    assert deployments[0]["provider"] == "vercel"


def test_dashboard_search_filter_sort_and_tag(client):
    register(client, "filter-user")
    create_site(client, "Alpha Site", "alpha.example.com", tags="marketing")
    create_site(client, "Beta Blog", "beta.example.com", tags="blog, content")

    filtered = client.get("/?q=beta&tag=blog&status=active&sort=name_desc")
    assert filtered.status_code == 200
    assert b"Beta Blog" in filtered.data
    assert b"Alpha Site" not in filtered.data


def test_duplicate_domain_validation(client):
    register(client, "domain-user")
    payload = {
        "name": "Main Site",
        "domain": "main.example.com",
        "tech_stack": "Next.js",
        "status": "active",
        "tags": "",
    }
    first = client.post("/websites/new", data=payload)
    assert first.status_code == 302

    second = client.post("/websites/new", data=payload)
    assert second.status_code == 400
    assert b"That domain already exists." in second.data


def test_delete_website_cascades_pages_and_deployments(client):
    register(client, "cascade-user")
    create_site(client, "Docs Site", "docs2.example.com")
    website_id = client.get("/api/websites").get_json()[0]["id"]

    page = client.post(
        f"/websites/{website_id}/pages/new",
        data={
            "title": "Guide",
            "slug": "guide",
            "seo_description": "",
            "content_markdown": "text",
            "published": "on",
        },
    )
    assert page.status_code == 302

    deploy = client.post(
        f"/websites/{website_id}/deployments/new",
        data={
            "provider": "netlify",
            "project_name": "docs2",
            "production_url": "",
            "preview_url": "",
            "branch": "main",
            "status": "active",
        },
    )
    assert deploy.status_code == 302

    assert len(client.get(f"/api/websites/{website_id}/pages").get_json()) == 1
    assert len(client.get(f"/api/websites/{website_id}/deployments").get_json()) == 1

    delete_website = client.post(f"/websites/{website_id}/delete")
    assert delete_website.status_code == 302
    assert client.get(f"/api/websites/{website_id}/pages").get_json() == []
    assert client.get(f"/api/websites/{website_id}/deployments").get_json() == []
