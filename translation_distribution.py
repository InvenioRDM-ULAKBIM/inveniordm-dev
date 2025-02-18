import json
import logging
from pathlib import Path
# import re
from importlib.metadata import entry_points

from invenio_app.factory import create_app

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = create_app()

EXCEPTIONAL_PACKAGE_NAME_MAPPER = {
    "jobs": "invenio-jobs",
    "invenio-previewer-theme": "invenio-previewer",
    "invenio-app-rdm-theme": "invenio-app-rdm"
}

tr_path = "js_translations"


def distribute_translations(translations_jsons_path: str) -> None:
    with (app.app_context()):
        # Get package names and assets path from webpack entrypoints
        bundle_entrypoints = [ep for ep in entry_points(group="invenio_assets.webpack")]
        PACKAGE_TRANSLATIONS_BASE_PATHS = {}
        for bundle_entrypoint in bundle_entrypoints:
            package_name = bundle_entrypoint.name.replace("_", "-")
            bundle = bundle_entrypoint.load()
            if bundle.path:
                if package_name in EXCEPTIONAL_PACKAGE_NAME_MAPPER:
                    package_name = EXCEPTIONAL_PACKAGE_NAME_MAPPER[package_name]
                PACKAGE_TRANSLATIONS_BASE_PATHS[package_name] = Path(bundle.path) / "translations"

        # Get combined translation files by languages
        source_translation_files = {}
        for path in Path(translations_jsons_path).iterdir():
            if path.is_file() and path.suffix == ".json":
                source_translation_files[path.stem] = path

        for lang in source_translation_files:
            with open(source_translation_files[lang], 'r') as source_translations_file:
                combined_translations = source_translations_file.read()
                combined_translations = json.loads(combined_translations)
                for package in combined_translations:
                    # package = re.sub(r"-messages-(ui|js)", "", domain)
                    if package in PACKAGE_TRANSLATIONS_BASE_PATHS:
                        module = package.replace("-", "_")
                        target_translations_path = PACKAGE_TRANSLATIONS_BASE_PATHS[package] / module / "messages" / lang
                        logging.debug(
                            f"{target_translations_path} is being used for {package} translations in {lang}.")
                        if not Path(target_translations_path).exists():
                            logging.warning(
                                f"Translations {lang} not found in {PACKAGE_TRANSLATIONS_BASE_PATHS[package] / module / "messages"}. Creating...")
                            Path(target_translations_path).mkdir()

                        target_translations_file_path = Path(target_translations_path) / "translations.json"
                        with open(target_translations_file_path, "w+") as target_translations_file:
                            try:
                                target_translations_file.write(
                                    json.dumps(combined_translations[package], indent=2, ensure_ascii=False))
                                logging.info(f"Translations for {package} in {lang} have been written.")
                            except (OSError, PermissionError) as e:
                                logging.error(f"Failed to write translations for {package} in {lang}: {str(e)}")
                            except Exception as e:
                                logging.error(f"Error processing translations for {package} in {lang}: {str(e)}")


if __name__ == "__main__":
    distribute_translations(tr_path)
