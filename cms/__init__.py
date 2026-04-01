from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for


DEFAULT_DATABASE = "cms.db"


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=str(Path(app.instance_path) / DEFAULT_DATABASE),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    with app.app_context():
        init_db()

    register_routes(app)
    return app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(app_config("DATABASE"))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def app_config(key: str) -> Any:
    from flask import current_app

    return current_app.config[key]


def close_db(_: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db_path = Path(app_config("DATABASE"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS websites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            domain TEXT NOT NULL UNIQUE,
            tech_stack TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            slug TEXT NOT NULL,
            seo_description TEXT,
            published INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (website_id) REFERENCES websites (id) ON DELETE CASCADE,
            UNIQUE(website_id, slug)
        );
        """
    )
    db.commit()
    db.close()


def query_db(query: str, args: tuple[Any, ...] = (), one: bool = False) -> Any:
    db = get_db()
    cur = db.execute(query, args)
    rows = cur.fetchall()
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute_db(query: str, args: tuple[Any, ...] = ()) -> int:
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    row_id = cur.lastrowid
    cur.close()
    return row_id


def register_routes(app: Flask) -> None:
    app.teardown_appcontext(close_db)

    @app.get("/")
    def dashboard() -> str:
        websites = query_db(
            """
            SELECT w.*, COUNT(p.id) AS page_count
            FROM websites w
            LEFT JOIN pages p ON p.website_id = w.id
            GROUP BY w.id
            ORDER BY w.created_at DESC
            """
        )
        recent_pages = query_db(
            """
            SELECT p.*, w.name AS website_name
            FROM pages p
            JOIN websites w ON w.id = p.website_id
            ORDER BY p.updated_at DESC
            LIMIT 10
            """
        )
        return render_template("dashboard.html", websites=websites, recent_pages=recent_pages)

    @app.get("/websites/new")
    def new_website_form() -> str:
        return render_template("website_form.html", website=None)

    @app.post("/websites/new")
    def create_website() -> Any:
        name = request.form.get("name", "").strip()
        domain = request.form.get("domain", "").strip()
        tech_stack = request.form.get("tech_stack", "").strip()
        status = request.form.get("status", "active").strip() or "active"

        if not name or not domain:
            flash("Name and domain are required.", "error")
            return render_template("website_form.html", website=request.form), 400

        try:
            execute_db(
                "INSERT INTO websites (name, domain, tech_stack, status) VALUES (?, ?, ?, ?)",
                (name, domain, tech_stack, status),
            )
        except sqlite3.IntegrityError:
            flash("That domain already exists.", "error")
            return render_template("website_form.html", website=request.form), 400

        flash("Website created.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/websites/<int:website_id>/edit")
    def edit_website_form(website_id: int) -> Any:
        website = query_db("SELECT * FROM websites WHERE id = ?", (website_id,), one=True)
        if website is None:
            return "Website not found", 404
        return render_template("website_form.html", website=website)

    @app.post("/websites/<int:website_id>/edit")
    def update_website(website_id: int) -> Any:
        website = query_db("SELECT * FROM websites WHERE id = ?", (website_id,), one=True)
        if website is None:
            return "Website not found", 404

        name = request.form.get("name", "").strip()
        domain = request.form.get("domain", "").strip()
        tech_stack = request.form.get("tech_stack", "").strip()
        status = request.form.get("status", "active").strip() or "active"

        if not name or not domain:
            flash("Name and domain are required.", "error")
            return render_template("website_form.html", website=request.form), 400

        try:
            execute_db(
                "UPDATE websites SET name = ?, domain = ?, tech_stack = ?, status = ? WHERE id = ?",
                (name, domain, tech_stack, status, website_id),
            )
        except sqlite3.IntegrityError:
            flash("That domain already exists.", "error")
            return render_template("website_form.html", website=request.form), 400

        flash("Website updated.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/websites/<int:website_id>/delete")
    def delete_website(website_id: int) -> Any:
        execute_db("DELETE FROM websites WHERE id = ?", (website_id,))
        flash("Website deleted.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/websites/<int:website_id>/pages")
    def pages_for_website(website_id: int) -> Any:
        website = query_db("SELECT * FROM websites WHERE id = ?", (website_id,), one=True)
        if website is None:
            return "Website not found", 404
        pages = query_db(
            "SELECT * FROM pages WHERE website_id = ? ORDER BY updated_at DESC",
            (website_id,),
        )
        return render_template("pages.html", website=website, pages=pages)

    @app.get("/websites/<int:website_id>/pages/new")
    def new_page_form(website_id: int) -> Any:
        website = query_db("SELECT * FROM websites WHERE id = ?", (website_id,), one=True)
        if website is None:
            return "Website not found", 404
        return render_template("page_form.html", website=website, page=None)

    @app.post("/websites/<int:website_id>/pages/new")
    def create_page(website_id: int) -> Any:
        website = query_db("SELECT * FROM websites WHERE id = ?", (website_id,), one=True)
        if website is None:
            return "Website not found", 404

        title = request.form.get("title", "").strip()
        slug = request.form.get("slug", "").strip()
        seo_description = request.form.get("seo_description", "").strip()
        published = 1 if request.form.get("published") == "on" else 0

        if not title or not slug:
            flash("Title and slug are required.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        try:
            execute_db(
                """
                INSERT INTO pages (website_id, title, slug, seo_description, published)
                VALUES (?, ?, ?, ?, ?)
                """,
                (website_id, title, slug, seo_description, published),
            )
        except sqlite3.IntegrityError:
            flash("Slug must be unique per website.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        flash("Page created.", "success")
        return redirect(url_for("pages_for_website", website_id=website_id))

    @app.get("/pages/<int:page_id>/edit")
    def edit_page_form(page_id: int) -> Any:
        page = query_db("SELECT * FROM pages WHERE id = ?", (page_id,), one=True)
        if page is None:
            return "Page not found", 404
        website = query_db("SELECT * FROM websites WHERE id = ?", (page["website_id"],), one=True)
        return render_template("page_form.html", website=website, page=page)

    @app.post("/pages/<int:page_id>/edit")
    def update_page(page_id: int) -> Any:
        page = query_db("SELECT * FROM pages WHERE id = ?", (page_id,), one=True)
        if page is None:
            return "Page not found", 404

        title = request.form.get("title", "").strip()
        slug = request.form.get("slug", "").strip()
        seo_description = request.form.get("seo_description", "").strip()
        published = 1 if request.form.get("published") == "on" else 0

        if not title or not slug:
            website = query_db("SELECT * FROM websites WHERE id = ?", (page["website_id"],), one=True)
            flash("Title and slug are required.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        try:
            execute_db(
                """
                UPDATE pages
                SET title = ?, slug = ?, seo_description = ?, published = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, slug, seo_description, published, page_id),
            )
        except sqlite3.IntegrityError:
            website = query_db("SELECT * FROM websites WHERE id = ?", (page["website_id"],), one=True)
            flash("Slug must be unique per website.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        flash("Page updated.", "success")
        return redirect(url_for("pages_for_website", website_id=page["website_id"]))

    @app.post("/pages/<int:page_id>/delete")
    def delete_page(page_id: int) -> Any:
        page = query_db("SELECT * FROM pages WHERE id = ?", (page_id,), one=True)
        if page is None:
            return "Page not found", 404
        execute_db("DELETE FROM pages WHERE id = ?", (page_id,))
        flash("Page deleted.", "success")
        return redirect(url_for("pages_for_website", website_id=page["website_id"]))

    @app.get("/api/websites")
    def api_websites() -> Any:
        websites = query_db(
            """
            SELECT w.*, COUNT(p.id) AS page_count
            FROM websites w
            LEFT JOIN pages p ON p.website_id = w.id
            GROUP BY w.id
            ORDER BY w.created_at DESC
            """
        )
        return jsonify([dict(row) for row in websites])

    @app.get("/api/websites/<int:website_id>/pages")
    def api_pages(website_id: int) -> Any:
        pages = query_db(
            "SELECT * FROM pages WHERE website_id = ? ORDER BY updated_at DESC",
            (website_id,),
        )
        return jsonify([dict(row) for row in pages])
