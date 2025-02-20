# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from pathlib import Path
import json

import click

from ..commands import TranslationsCommands
from .utils import pass_cli_config, run_steps

from jinja2 import Environment, FileSystemLoader

import polib


@click.group()
def translations():
    """Commands for translations management."""


@translations.command()
@click.option(
    "--babel-ini",
    "-b",
    default="translations/babel.ini",
    help="Relative path to babel.ini (including filename).",
)
@pass_cli_config
def extract(cli_config, babel_ini):
    """Extract messages for i18n support (translations)."""
    click.secho("Extracting messages...", fg="green")
    steps = TranslationsCommands.extract(
        msgid_bugs_address=cli_config.get_author_email(),
        copyright_holder=cli_config.get_author_name(),
        babel_file=cli_config.get_project_dir() / Path("translations/babel.ini"),
        output_file=cli_config.get_project_dir() / Path("translations/messages.pot"),
        input_dirs=cli_config.get_project_dir(),
    )
    on_fail = "Failed to extract messages."
    on_success = "Messages extracted successfully."

    run_steps(steps, on_fail, on_success)


@translations.command()
@click.option("--locale", "-l", required=True, help="Locale to initialize.")
@pass_cli_config
def init(cli_config, locale):
    """Initialized message catalog for a given locale."""
    click.secho("Initializing messages catalog...", fg="green")
    steps = TranslationsCommands.init(
        output_dir=cli_config.get_project_dir() / Path("translations/"),
        input_file=cli_config.get_project_dir() / Path("translations/messages.pot"),
        locale=locale,
    )
    on_fail = f"Failed to initialize message catalog for {locale}."
    on_success = f"Message catalog for {locale} initialized successfully."

    run_steps(steps, on_fail, on_success)


@translations.command()
@pass_cli_config
def update(cli_config):
    """Update messages catalog."""
    click.secho("Updating messages catalog...", fg="green")
    steps = TranslationsCommands.update(
        output_dir=cli_config.get_project_dir() / Path("translations/"),
        input_file=cli_config.get_project_dir() / Path("translations/messages.pot"),
    )
    on_fail = f"Failed to update message catalog."
    on_success = f"Message catalog updated successfully."

    run_steps(steps, on_fail, on_success)


@translations.command()
@click.option("--fuzzy", "-f", default=True, is_flag=True, help="Use fuzzyness.")
@pass_cli_config
def compile(cli_config, fuzzy):
    """Compile message catalog."""
    click.secho("Compiling catalog...", fg="green")
    commands = TranslationsCommands(
        project_path=cli_config.get_project_dir(),
        instance_path=cli_config.get_instance_path(),
    )
    steps = commands.compile(fuzzy=fuzzy)
    on_fail = "Failed to compile catalog."
    on_success = "Catalog compiled successfully."

    run_steps(steps, on_fail, on_success)


@translations.command()
@click.option("--token", "-t", required=True, help="API token for your Transifex account.")
@click.option("--languages", "-l", required=True,
              help="Languages you want to download translations for (one or multiple comma separated values).")
@click.option("--javascript", "-js", default=False, is_flag=True,
              help="Download all available JS translations from Transifex.")
@click.option("--python", "-py", default=False, is_flag=True,
              help="Download all available Python translations from Transifex.")
@pass_cli_config
def download_transifex(cli_config, token, languages, javascript, python):
    """Compile message catalog."""
    # TODO Should this be two commands or one with flags for js and python?
    if python or javascript:
        js_resources = {
            "invenio-administration-messages-ui": "invenio_administration",
            "invenio-app-rdm-messages-ui": "invenio_app_rdm",
            "invenio-communities-messages-ui": "invenio_communities",
            "invenio-rdm-records-messages-ui": "invenio_rdm_records",
            "invenio-requests-messages-ui": "invenio_requests",
            "invenio-search-ui-messages-js": "invenio_search_ui"
        }

        python_resources = {
            "invenio-access-messages": "invenio_access",
            "invenio-accounts-messages": "invenio_accounts",
            "invenio-administration-messages": "invenio_administration",
            "invenio-app-rdm-messages": "invenio_app_rdm",
            "invenio-banners-messages": "invenio_banners",
            "invenio-communities-messages": "invenio_communities",
            "invenio-drafts-resources-messages": "invenio_drafts_resources",
            "invenio-files-rest-messages": "invenio_files_rest",
            "invenio-formatter-messages": "invenio_formatter",
            "invenio-github-messages": "invenio_github",
            "invenio-i18n-messages": "invenio_i18n",
            "invenio-notifications-messages": "invenio_notifications",
            "invenio-oaiserver-messages": "invenio_oaiserver",
            "invenio-oauth2server-messages": "invenio_oauth2server",
            "invenio-oauthclient-messages": "invenio_oauthclient",
            "invenio-pages-messages": "invenio_pages",
            "invenio-pidstore-messages": "invenio_pidstore",
            "invenio-previewer-messages": "invenio_previewer",
            "invenio-rdm-records-messages": "invenio_rdm_records",
            "invenio-records-messages": "invenio_records",
            "invenio-records-permissions-messages": "invenio_records_permissions",
            "invenio-records-resources-messages": "invenio_records_resources",
            "invenio-records-ui-messages": "invenio_records_ui",
            "invenio-requests-messages": "invenio_requests",
            "invenio-saml-messages": "invenio_saml",
            "invenio-search-ui-messages": "invenio_search_ui",
            "invenio-theme-messages": "invenio_theme",
            "invenio-userprofiles-messages": "invenio_userprofiles",
            "invenio-users-resources-messages": "invenio_users_resources",
            "invenio-vocabularies-messages": "invenio_vocabularies",
            "invenio-webhooks-messages": "invenio_webhooks",
            "marshmallow-utils-messages": "marshmallow-utils"
        }

        file_loader = FileSystemLoader('.')
        env = Environment(loader=file_loader)

        with open('collected_config', 'w') as f:
            if javascript:
                template = env.get_template("config-template-js")

                for resource, module in js_resources.items():
                    if module == "invenio_app_rdm":
                        output = template.render(resource=resource, module=module, theme="/theme")
                    else:
                        output = template.render(resource=resource, module=module)

                    f.write(output)
                    f.write("\n\n")

            if python:
                template = env.get_template("config-template-python")

                for resource, module in python_resources.items():
                    if module == "invenio_app_rdm":
                        output = template.render(resource=resource, module=module, theme="/theme")
                    else:
                        output = template.render(resource=resource, module=module)

                    f.write(output)
                    f.write("\n\n")

        # TODO Transifex downloads to path in config, change config if a different file location for *.po files is needed
        commands = TranslationsCommands(
            project_path=cli_config.get_project_dir(),
            instance_path=cli_config.get_instance_path(),
        )
        steps = commands.download_transifex(api_token=token, languages=languages)
        on_fail = "Failed to download translations."
        on_success = "Downloaded translations successfully."

        run_steps(steps, on_fail, on_success)

        collected_translations = {}

        languages_array = languages.split(",")
        for language in languages_array:
            collected_translations[language] = {}

            if javascript:
                for resource, module in js_resources.items():
                    if module == "invenio_app_rdm":
                        po_path = f"./{module}/theme/assets/semantic-ui/translations/{module}/messages/{language}/messages.po"
                    else:
                        po_path = f"./{module}/assets/semantic-ui/translations/{module}/messages/{language}/messages.po"

                    collected_translations[language][module] = _po_file_to_dict(po_path)

            if python:
                for resource, module in python_resources.items():
                    po_path = f"./{module}/translations/{language}/LC_MESSAGES/messages.po"
                    collected_translations[language][module] = _po_file_to_dict(po_path)

            with open(f"collected_translations_{language}.json", 'w', encoding='utf-8') as f:
                json.dump(collected_translations[language], f, indent=4, ensure_ascii=False)
    else:
        click.secho("Please use either the --py or the --js flag to specify which translation should be downloaded.",
                    fg="yellow")


def _po_file_to_dict(po_path):
    pofile = polib.pofile(po_path)
    po_translations = {}

    for entry in pofile:
        po_translations[entry.msgid] = entry.msgstr
        if entry.msgstr_plural:
            po_translations[entry.msgid] = entry.msgstr_plural[0]
            po_translations[entry.msgid + "_plural"] = entry.msgstr_plural[
                1]  # TODO pluralization does work differently for babel! need to change that

    return po_translations
