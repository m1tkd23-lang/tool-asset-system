#src/tool_asset_system/web/app.py

from __future__ import annotations

from flask import Flask

from tool_asset_system.web.routes_parts import bp as parts_bp
from tool_asset_system.web.routes_api import bp as api_bp

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "dev"  # 社内運用なら.env化候補（後で）
    app.register_blueprint(parts_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app
