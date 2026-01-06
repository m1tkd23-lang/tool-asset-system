#src/tool_asset_system/web/app.py

from __future__ import annotations

from flask import Flask

from tool_asset_system.web.routes_parts import bp as parts_bp
from tool_asset_system.web.routes_api import bp as api_bp
from tool_asset_system.web.routes_assemblies import bp as assemblies_bp
from tool_asset_system.web.routes_tooling_lists import bp as tooling_lists_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "dev"
    app.register_blueprint(parts_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(assemblies_bp)
    app.register_blueprint(tooling_lists_bp)
    return app