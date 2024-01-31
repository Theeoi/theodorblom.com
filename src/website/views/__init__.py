from importlib import import_module
from pathlib import Path


def register_blueprints(app):
    views_directory = Path(__file__).parent
    view_files = [f for f in views_directory.glob("*.py") if f.stem != "__init__"]

    for view_file in view_files:
        blueprint_name = view_file.stem
        view_module = import_module(f".{blueprint_name}", package="website.views")
        blueprint = getattr(view_module, blueprint_name)
        app.register_blueprint(blueprint)
