from __future__ import annotations

import sqlite3
from functools import wraps
from pathlib import Path
from typing import Any, Callable

import bleach
import markdown
from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


DEFAULT_DATABASE = "cms.db"

ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "target", "rel"]}


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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'editor',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS websites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            name TEXT NOT NULL,
            domain TEXT NOT NULL UNIQUE,
            tech_stack TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            slug TEXT NOT NULL,
            seo_description TEXT,
            content_markdown TEXT NOT NULL DEFAULT '',
            published INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (website_id) REFERENCES websites (id) ON DELETE CASCADE,
            UNIQUE(website_id, slug)
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS website_tags (
            website_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (website_id, tag_id),
            FOREIGN KEY (website_id) REFERENCES websites (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            project_name TEXT NOT NULL,
            production_url TEXT,
            preview_url TEXT,
            branch TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (website_id) REFERENCES websites (id) ON DELETE CASCADE
        );
        """
    )

    ensure_schema_upgrades(db)
    db.commit()
    db.close()


def ensure_schema_upgrades(db: sqlite3.Connection) -> None:
    page_cols = get_table_columns(db, "pages")
    if "content_markdown" not in page_cols:
        db.execute("ALTER TABLE pages ADD COLUMN content_markdown TEXT NOT NULL DEFAULT ''")

    website_cols = get_table_columns(db, "websites")
    if "owner_id" not in website_cols:
        db.execute("ALTER TABLE websites ADD COLUMN owner_id INTEGER")

    if has_rows(db, "websites") and has_null_owner_websites(db):
        first_user = db.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
        if first_user is None:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("legacy-admin", generate_password_hash("change-this-password"), "admin"),
            )
            first_user = db.execute("SELECT id FROM users WHERE username = ?", ("legacy-admin",)).fetchone()
        db.execute("UPDATE websites SET owner_id = ? WHERE owner_id IS NULL", (first_user[0],))


def has_rows(db: sqlite3.Connection, table: str) -> bool:
    row = db.execute(f"SELECT EXISTS(SELECT 1 FROM {table})").fetchone()
    return bool(row[0])


def has_null_owner_websites(db: sqlite3.Connection) -> bool:
    row = db.execute("SELECT EXISTS(SELECT 1 FROM websites WHERE owner_id IS NULL)").fetchone()
    return bool(row[0])


def get_table_columns(db: sqlite3.Connection, table_name: str) -> set[str]:
    rows = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


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


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(**kwargs: Any) -> Any:
        if g.user is None:
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def parse_tags(raw_tags: str) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for item in raw_tags.split(","):
        cleaned = item.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            tags.append(cleaned)
    return tags


def set_website_tags(website_id: int, tags: list[str]) -> None:
    db = get_db()
    db.execute("DELETE FROM website_tags WHERE website_id = ?", (website_id,))
    for tag_name in tags:
        row = db.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
        if row is None:
            cur = db.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
            tag_id = cur.lastrowid
            cur.close()
        else:
            tag_id = row[0]
        db.execute("INSERT OR IGNORE INTO website_tags (website_id, tag_id) VALUES (?, ?)", (website_id, tag_id))
    db.commit()


def get_website_tags(website_id: int) -> list[str]:
    rows = query_db(
        """
        SELECT t.name
        FROM tags t
        JOIN website_tags wt ON wt.tag_id = t.id
        WHERE wt.website_id = ?
        ORDER BY t.name ASC
        """,
        (website_id,),
    )
    return [row["name"] for row in rows]


def get_owned_website(website_id: int) -> sqlite3.Row | None:
    return query_db(
        "SELECT * FROM websites WHERE id = ? AND owner_id = ?",
        (website_id, g.user["id"]),
        one=True,
    )


def get_owned_page(page_id: int) -> sqlite3.Row | None:
    return query_db(
        """
        SELECT p.*
        FROM pages p
        JOIN websites w ON w.id = p.website_id
        WHERE p.id = ? AND w.owner_id = ?
        """,
        (page_id, g.user["id"]),
        one=True,
    )


def get_owned_deployment(deployment_id: int) -> sqlite3.Row | None:
    return query_db(
        """
        SELECT d.*
        FROM deployments d
        JOIN websites w ON w.id = d.website_id
        WHERE d.id = ? AND w.owner_id = ?
        """,
        (deployment_id, g.user["id"]),
        one=True,
    )


def render_markdown(content: str) -> str:
    html = markdown.markdown(content or "", extensions=["extra", "sane_lists"])
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return bleach.linkify(cleaned)


def register_routes(app: Flask) -> None:
    app.teardown_appcontext(close_db)

    @app.before_request
    def load_logged_in_user() -> None:
        user_id = session.get("user_id")
        if user_id is None:
            g.user = None
            return
        g.user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)

    @app.get("/auth/register")
    def register() -> str:
        return render_template("register.html")

    @app.post("/auth/register")
    def register_post() -> Any:
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "editor").strip() or "editor"

        if len(username) < 3 or len(password) < 8:
            flash("Username must be >= 3 chars and password >= 8 chars.", "error")
            return render_template("register.html"), 400

        try:
            user_id = execute_db(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role),
            )
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
            return render_template("register.html"), 400

        session.clear()
        session["user_id"] = user_id
        flash("Account created and signed in.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/auth/login")
    def login() -> str:
        return render_template("login.html")

    @app.post("/auth/login")
    def login_post() -> Any:
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid credentials.", "error")
            return render_template("login.html"), 400

        session.clear()
        session["user_id"] = user["id"]
        flash("Logged in.", "success")
        next_path = request.args.get("next")
        if next_path:
            return redirect(next_path)
        return redirect(url_for("dashboard"))

    @app.post("/auth/logout")
    def logout() -> Any:
        session.clear()
        flash("Logged out.", "success")
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard() -> str:
        q = request.args.get("q", "").strip()
        status_filter = request.args.get("status", "all").strip()
        tag_filter = request.args.get("tag", "all").strip().lower()
        sort_key = request.args.get("sort", "newest").strip()

        sort_map = {
            "newest": "w.created_at DESC",
            "oldest": "w.created_at ASC",
            "name_asc": "w.name COLLATE NOCASE ASC",
            "name_desc": "w.name COLLATE NOCASE DESC",
            "pages_desc": "page_count DESC, w.created_at DESC",
        }
        sort_sql = sort_map.get(sort_key, sort_map["newest"])

        where_clauses = ["w.owner_id = ?"]
        args: list[Any] = [g.user["id"]]

        if q:
            where_clauses.append("(w.name LIKE ? OR w.domain LIKE ? OR IFNULL(w.tech_stack, '') LIKE ?)")
            like = f"%{q}%"
            args.extend([like, like, like])

        if status_filter != "all":
            where_clauses.append("w.status = ?")
            args.append(status_filter)

        if tag_filter != "all":
            where_clauses.append(
                "EXISTS (SELECT 1 FROM website_tags wtf JOIN tags tf ON tf.id = wtf.tag_id WHERE wtf.website_id = w.id AND tf.name = ?)"
            )
            args.append(tag_filter)

        where_sql = " AND ".join(where_clauses)
        websites = query_db(
            f"""
            SELECT
                w.*,
                COUNT(DISTINCT p.id) AS page_count,
                COUNT(DISTINCT d.id) AS deployment_count,
                GROUP_CONCAT(DISTINCT t.name) AS tags_csv
            FROM websites w
            LEFT JOIN pages p ON p.website_id = w.id
            LEFT JOIN deployments d ON d.website_id = w.id
            LEFT JOIN website_tags wt ON wt.website_id = w.id
            LEFT JOIN tags t ON t.id = wt.tag_id
            WHERE {where_sql}
            GROUP BY w.id
            ORDER BY {sort_sql}
            """,
            tuple(args),
        )

        normalized_websites = []
        for website in websites:
            item = dict(website)
            tags_csv = item.pop("tags_csv", None)
            item["tags"] = tags_csv.split(",") if tags_csv else []
            normalized_websites.append(item)

        recent_pages = query_db(
            """
            SELECT p.*, w.name AS website_name
            FROM pages p
            JOIN websites w ON w.id = p.website_id
            WHERE w.owner_id = ?
            ORDER BY p.updated_at DESC
            LIMIT 10
            """,
            (g.user["id"],),
        )
        available_tags = query_db(
            """
            SELECT DISTINCT t.name
            FROM tags t
            JOIN website_tags wt ON wt.tag_id = t.id
            JOIN websites w ON w.id = wt.website_id
            WHERE w.owner_id = ?
            ORDER BY t.name ASC
            """,
            (g.user["id"],),
        )

        return render_template(
            "dashboard.html",
            websites=normalized_websites,
            recent_pages=recent_pages,
            available_tags=[row["name"] for row in available_tags],
            filters={
                "q": q,
                "status": status_filter,
                "tag": tag_filter,
                "sort": sort_key,
            },
        )

    @app.get("/websites/new")
    @login_required
    def new_website_form() -> str:
        return render_template("website_form.html", website=None, tag_text="")

    @app.post("/websites/new")
    @login_required
    def create_website() -> Any:
        name = request.form.get("name", "").strip()
        domain = request.form.get("domain", "").strip()
        tech_stack = request.form.get("tech_stack", "").strip()
        status = request.form.get("status", "active").strip() or "active"
        tag_text = request.form.get("tags", "").strip()

        if not name or not domain:
            flash("Name and domain are required.", "error")
            return render_template("website_form.html", website=request.form, tag_text=tag_text), 400

        try:
            website_id = execute_db(
                "INSERT INTO websites (owner_id, name, domain, tech_stack, status) VALUES (?, ?, ?, ?, ?)",
                (g.user["id"], name, domain, tech_stack, status),
            )
        except sqlite3.IntegrityError:
            flash("That domain already exists.", "error")
            return render_template("website_form.html", website=request.form, tag_text=tag_text), 400

        set_website_tags(website_id, parse_tags(tag_text))
        flash("Website created.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/websites/<int:website_id>/edit")
    @login_required
    def edit_website_form(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404
        return render_template(
            "website_form.html",
            website=website,
            tag_text=", ".join(get_website_tags(website_id)),
        )

    @app.post("/websites/<int:website_id>/edit")
    @login_required
    def update_website(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404

        name = request.form.get("name", "").strip()
        domain = request.form.get("domain", "").strip()
        tech_stack = request.form.get("tech_stack", "").strip()
        status = request.form.get("status", "active").strip() or "active"
        tag_text = request.form.get("tags", "").strip()

        if not name or not domain:
            flash("Name and domain are required.", "error")
            return render_template("website_form.html", website=request.form, tag_text=tag_text), 400

        try:
            execute_db(
                "UPDATE websites SET name = ?, domain = ?, tech_stack = ?, status = ? WHERE id = ?",
                (name, domain, tech_stack, status, website_id),
            )
        except sqlite3.IntegrityError:
            flash("That domain already exists.", "error")
            return render_template("website_form.html", website=request.form, tag_text=tag_text), 400

        set_website_tags(website_id, parse_tags(tag_text))
        flash("Website updated.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/websites/<int:website_id>/delete")
    @login_required
    def delete_website(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404
        execute_db("DELETE FROM websites WHERE id = ?", (website_id,))
        flash("Website deleted.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/websites/<int:website_id>/pages")
    @login_required
    def pages_for_website(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404
        pages = query_db(
            "SELECT * FROM pages WHERE website_id = ? ORDER BY updated_at DESC",
            (website_id,),
        )
        return render_template("pages.html", website=website, pages=pages)

    @app.get("/websites/<int:website_id>/pages/new")
    @login_required
    def new_page_form(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404
        return render_template("page_form.html", website=website, page=None)

    @app.post("/websites/<int:website_id>/pages/new")
    @login_required
    def create_page(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404

        title = request.form.get("title", "").strip()
        slug = request.form.get("slug", "").strip()
        seo_description = request.form.get("seo_description", "").strip()
        content_markdown = request.form.get("content_markdown", "").strip()
        published = 1 if request.form.get("published") == "on" else 0

        if not title or not slug:
            flash("Title and slug are required.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        try:
            execute_db(
                """
                INSERT INTO pages (website_id, title, slug, seo_description, content_markdown, published)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (website_id, title, slug, seo_description, content_markdown, published),
            )
        except sqlite3.IntegrityError:
            flash("Slug must be unique per website.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        flash("Page created.", "success")
        return redirect(url_for("pages_for_website", website_id=website_id))

    @app.get("/pages/<int:page_id>")
    @login_required
    def view_page(page_id: int) -> Any:
        page = get_owned_page(page_id)
        if page is None:
            return "Page not found", 404
        website = get_owned_website(page["website_id"])
        if website is None:
            return "Website not found", 404
        return render_template(
            "page_view.html",
            website=website,
            page=page,
            rendered_content=render_markdown(page["content_markdown"]),
        )

    @app.get("/pages/<int:page_id>/edit")
    @login_required
    def edit_page_form(page_id: int) -> Any:
        page = get_owned_page(page_id)
        if page is None:
            return "Page not found", 404
        website = get_owned_website(page["website_id"])
        return render_template("page_form.html", website=website, page=page)

    @app.post("/pages/<int:page_id>/edit")
    @login_required
    def update_page(page_id: int) -> Any:
        page = get_owned_page(page_id)
        if page is None:
            return "Page not found", 404

        title = request.form.get("title", "").strip()
        slug = request.form.get("slug", "").strip()
        seo_description = request.form.get("seo_description", "").strip()
        content_markdown = request.form.get("content_markdown", "").strip()
        published = 1 if request.form.get("published") == "on" else 0

        if not title or not slug:
            website = get_owned_website(page["website_id"])
            flash("Title and slug are required.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        try:
            execute_db(
                """
                UPDATE pages
                SET title = ?, slug = ?, seo_description = ?, content_markdown = ?, published = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, slug, seo_description, content_markdown, published, page_id),
            )
        except sqlite3.IntegrityError:
            website = get_owned_website(page["website_id"])
            flash("Slug must be unique per website.", "error")
            return render_template("page_form.html", website=website, page=request.form), 400

        flash("Page updated.", "success")
        return redirect(url_for("pages_for_website", website_id=page["website_id"]))

    @app.post("/pages/<int:page_id>/delete")
    @login_required
    def delete_page(page_id: int) -> Any:
        page = get_owned_page(page_id)
        if page is None:
            return "Page not found", 404
        execute_db("DELETE FROM pages WHERE id = ?", (page_id,))
        flash("Page deleted.", "success")
        return redirect(url_for("pages_for_website", website_id=page["website_id"]))

    @app.get("/websites/<int:website_id>/deployments")
    @login_required
    def deployments_for_website(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404
        deployments = query_db(
            "SELECT * FROM deployments WHERE website_id = ? ORDER BY updated_at DESC",
            (website_id,),
        )
        return render_template("deployments.html", website=website, deployments=deployments)

    @app.post("/websites/<int:website_id>/deployments/new")
    @login_required
    def create_deployment(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return "Website not found", 404

        provider = request.form.get("provider", "").strip().lower()
        project_name = request.form.get("project_name", "").strip()
        production_url = request.form.get("production_url", "").strip()
        preview_url = request.form.get("preview_url", "").strip()
        branch = request.form.get("branch", "").strip()
        status = request.form.get("status", "active").strip() or "active"

        if provider not in {"vercel", "netlify"}:
            flash("Provider must be vercel or netlify.", "error")
            return redirect(url_for("deployments_for_website", website_id=website_id))
        if not project_name:
            flash("Project name is required.", "error")
            return redirect(url_for("deployments_for_website", website_id=website_id))

        execute_db(
            """
            INSERT INTO deployments (website_id, provider, project_name, production_url, preview_url, branch, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (website_id, provider, project_name, production_url, preview_url, branch, status),
        )
        flash("Deployment saved.", "success")
        return redirect(url_for("deployments_for_website", website_id=website_id))

    @app.get("/deployments/<int:deployment_id>/edit")
    @login_required
    def edit_deployment_form(deployment_id: int) -> Any:
        deployment = get_owned_deployment(deployment_id)
        if deployment is None:
            return "Deployment not found", 404
        website = get_owned_website(deployment["website_id"])
        return render_template("deployment_form.html", website=website, deployment=deployment)

    @app.post("/deployments/<int:deployment_id>/edit")
    @login_required
    def update_deployment(deployment_id: int) -> Any:
        deployment = get_owned_deployment(deployment_id)
        if deployment is None:
            return "Deployment not found", 404

        provider = request.form.get("provider", "").strip().lower()
        project_name = request.form.get("project_name", "").strip()
        production_url = request.form.get("production_url", "").strip()
        preview_url = request.form.get("preview_url", "").strip()
        branch = request.form.get("branch", "").strip()
        status = request.form.get("status", "active").strip() or "active"

        if provider not in {"vercel", "netlify"}:
            flash("Provider must be vercel or netlify.", "error")
            website = get_owned_website(deployment["website_id"])
            return render_template("deployment_form.html", website=website, deployment=request.form), 400
        if not project_name:
            flash("Project name is required.", "error")
            website = get_owned_website(deployment["website_id"])
            return render_template("deployment_form.html", website=website, deployment=request.form), 400

        execute_db(
            """
            UPDATE deployments
            SET provider = ?, project_name = ?, production_url = ?, preview_url = ?, branch = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (provider, project_name, production_url, preview_url, branch, status, deployment_id),
        )
        flash("Deployment updated.", "success")
        return redirect(url_for("deployments_for_website", website_id=deployment["website_id"]))

    @app.post("/deployments/<int:deployment_id>/delete")
    @login_required
    def delete_deployment(deployment_id: int) -> Any:
        deployment = get_owned_deployment(deployment_id)
        if deployment is None:
            return "Deployment not found", 404
        execute_db("DELETE FROM deployments WHERE id = ?", (deployment_id,))
        flash("Deployment deleted.", "success")
        return redirect(url_for("deployments_for_website", website_id=deployment["website_id"]))

    @app.get("/api/websites")
    @login_required
    def api_websites() -> Any:
        websites = query_db(
            """
            SELECT
                w.*,
                COUNT(DISTINCT p.id) AS page_count,
                COUNT(DISTINCT d.id) AS deployment_count,
                GROUP_CONCAT(DISTINCT t.name) AS tags_csv
            FROM websites w
            LEFT JOIN pages p ON p.website_id = w.id
            LEFT JOIN deployments d ON d.website_id = w.id
            LEFT JOIN website_tags wt ON wt.website_id = w.id
            LEFT JOIN tags t ON t.id = wt.tag_id
            WHERE w.owner_id = ?
            GROUP BY w.id
            ORDER BY w.created_at DESC
            """,
            (g.user["id"],),
        )

        payload = []
        for row in websites:
            item = dict(row)
            item["tags"] = item.pop("tags_csv", "").split(",") if item.get("tags_csv") else []
            payload.append(item)
        return jsonify(payload)

    @app.get("/api/websites/<int:website_id>/pages")
    @login_required
    def api_pages(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return jsonify([])
        pages = query_db(
            "SELECT * FROM pages WHERE website_id = ? ORDER BY updated_at DESC",
            (website_id,),
        )
        return jsonify([dict(row) for row in pages])

    @app.get("/api/websites/<int:website_id>/deployments")
    @login_required
    def api_deployments(website_id: int) -> Any:
        website = get_owned_website(website_id)
        if website is None:
            return jsonify([])
        deployments = query_db(
            "SELECT * FROM deployments WHERE website_id = ? ORDER BY updated_at DESC",
            (website_id,),
        )
        return jsonify([dict(row) for row in deployments])
