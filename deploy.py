#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# from functools import partial
import logging
import os
import shutil

from babel.support import Translations
import click
import confuse
import ipdb  # NOQA
import jinja2


def dumps(content, path):
    log.info('Exporting to {}'.format(path))
    with open(path, 'w') as out:
        out.writelines(content)


def mkdirs(path):
    if not os.path.exists(path):
        log.debug('Creating path: {}'.format(path))
        os.makedirs(path)


def ext_url(path):
    path_build = os.environ['PATH_BUILD']
    path = path.strip()
    if path[0] == '/':
        path = path.lstrip('/')
        path = os.path.join(path_build, path)
        path = 'file://{}'.format(path)
    return path


# CONFIG
# overide default location of the config.yaml file
os.environ['DEVCONFDIR'] = './'
config = confuse.Configuration('devconf')

# Define the supported sites available
# SITES = tuple(list(config['sites'].get()) + ['all'])

# BUILD
PATH_BUILD = './build'

# TEMPLATES
# Set-up Template loading
PATH_TEMPLATES = './templates'
_loader = jinja2.FileSystemLoader(PATH_TEMPLATES)

# FIXME: move this to 'init' command or something...
locale_dir = './i18n'
# prepare the build
if not os.path.exists(locale_dir):
    mkdirs(locale_dir)

msgdomain = 'html'
default_locale = 'en_US'
list_of_desired_locales = ['en', 'cs', 'sk']
extensions = ['jinja2.ext.i18n', 'jinja2.ext.with_']

'''
Create the folder structure (no whitespace after the commas!!!)
> mkdir -pv ./il8n/{en_US,cs_CZ,sk_SK}/LC_MESSAGES/
> pybabel -v extract -F babel.cfg -o ./il8n/messages.pot ./

Init/Update
3.1 Init
> pybabel init -l en_US -d ./il8n -i ./il8n/messages.pot
> pybabel init -l cs_CZ -d ./il8n -i ./il8n/messages.pot
> pybabel init -l sk_SK -d ./il8n -i ./il8n/messages.pot

3.2 Update
> pybabel update -l en_US -d ./il8n -i ./il8n/messages.pot
> pybabel update -l cs_CZ -d ./il8n -i ./il8n/messages.pot
> pybabel update -l sk_SK -d ./il8n -i ./il8n/messages.pot

Compile
> pybabel compile -f -d ./il8n
'''

translations = Translations.load(locale_dir, list_of_desired_locales)
jinja2_env = jinja2.Environment(loader=_loader,
                                autoescape=True,
                                extensions=extensions)
jinja2_env.install_gettext_translations(translations)

PATH_STATIC = './static'

# LOGGING
# Setup console logging
log = logging.getLogger('devconf')
logging.basicConfig(format='%(message)s')


# add the ext to the jinja environment
jinja2_env.filters['url'] = ext_url


@click.group()
@click.option('--quiet', '-q', is_flag=True, default=False)
@click.option('--debug', '-d', is_flag=True, default=False)
def cli(quiet, debug):
    if quiet:
        log.setLevel(logging.WARN)
    elif debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)


def _clean(build=True):
    if build and os.path.exists(PATH_BUILD):
        log.debug('Cleaning up old builds in {}'.format(PATH_BUILD))
        shutil.rmtree(PATH_BUILD)


@cli.command('build')
@click.option('--branch', '-b', type=str, default='devel')
@click.option('--clean', '-c', is_flag=True, default=False)
def build(branch, clean):
    # Clean up the previous build
    _clean(build=True)

    static_path = PATH_STATIC
    # Copy out all the static files to root of output directory
    for _path in os.listdir(static_path):
        from_path = os.path.join(static_path, _path)
        to_path = os.path.join(PATH_BUILD, _path)
        if os.path.exists(to_path):
            log.warning('"static" path already exists: {}'.format(to_path))
        else:
            log.debug(
                'Copying "static" to build dir: {}'.format(to_path))
            shutil.copytree(from_path, to_path)

    templates = (
        'index.html',
        'media-policy.html',
        'coc.html',
        'speaker-agreement.html',
        'cz/index.html',
        'cz/2017/index.html',
        'cz/2017/roadshow-bratislava.html',
        'cz/2017/roadshow-prague.html',
        'cz/2018/index.html',
        )

    os.environ['PATH_BUILD'] = os.path.abspath(PATH_BUILD)

    # Now build all the pages for the site
    for path in templates:
        # [/]{{site}}/template.html
        site = path.split('/')[0] if '/' in path else ''

        params = {
            # FIXME: only if DEBUG on, otherwise don't include private keys
            '__site': site,
            '__branch': branch,
            '__template': path,
        }

        # Render the template
        template = jinja2_env.get_template(path)
        content = template.render(**params)

        # Save the rendered page to disk
        dest_file = os.path.join(PATH_BUILD, path)
        # create the directory struct where the file will live
        mkdirs(os.path.dirname(dest_file))
        # dump the rendered file
        dumps(content, dest_file)

        assert os.path.exists(dest_file)





if __name__ == '__main__':
    cli(obj={})