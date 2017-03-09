#!/bin/env python3
# -*- coding: utf-8 -*-

"""mission_shipper.py

This script exists to allow us to automatically generate the `@cnto_missions`
ArmA3 Mod in order to ship large missions (>5MB) to our players using our
already-existing mod distribution system.

See README.md for more details.
"""

import argparse
import functools
import logging
import os
import re
import shutil
import stat
import subprocess

import jinja2

MOD_DIRNAME = "@cnto_missions"
MISSION_SQM_PATH = "./mission.sqm"
MISSIONS_DIR_PATH = "./addons/missions/"
JINJA2_TEMPLATE_EXT = '.j2'
MAKEPBO_PATH = os.getenv('MAKEPBO_PATH', 'makepbo')

PARSER = argparse.ArgumentParser(
    description="Helper script for generating the @cnto_missions mod.",
)
PARSER.add_argument(
    '--template-path',
    default="./templates/",
    help="Source directory that contains the template files",
)
PARSER.add_argument(
    '--missions-path',
    default="./missions",
    help="Source directory for non-pboized missions to package."
)
PARSER.add_argument(
    '--build-path',
    default="./build",
    help="Build directory for storing the mod before pobization."
)
PARSER.add_argument(
    '--target-path',
    default="./",
    help="Target directory for storing the generated @cnto_missions mod.",
)

def missions_context(missions_path):
    """Helper function to fetch missions metadata.

    Iterates over every existing mission in the `missions_path` directory
    and 'parses' their `mission.sqm` files to fetch metadatas to use in the
    `config.cpp` template.
    """

    missions = list()
    for mission_dir in os.listdir(missions_path):
        mission_path = os.path.join(missions_path, mission_dir)
        statinfo = os.stat(mission_path)
        if not stat.S_ISDIR(statinfo.st_mode):
            continue

        # "Class name MUST match the name in the 'directory' path"
        # https://community.bistudio.com/wiki/CfgMissions#MPMissions
        # We need to extract the Map extension as well as convert
        # dashes to underscores because of syntactic limitations
        mission_classname = mission_dir[:mission_dir.rfind('.')].replace('-', '_')
        mission = {
            'classname': mission_classname,
            'metadata': {
                # The directory needs to use the same prefix as the addon's PBOPREFIX
                'directory': r'"cnto\missions\missions\{}"'.format(mission_dir),
            },
        }

        with open(os.path.join(mission_path, MISSION_SQM_PATH), 'r') as sqm_file:
            # I've given up on trying to do a proper parsing of SQM using a
            # grammar, so here goes the unreliable line-by-line match.
            briefing_match = re.compile(r'briefingName=(.*)$')
            for line in sqm_file.readlines():
                match = re.search(briefing_match, line)
                if match:
                    mission['metadata']['briefingName'] = match.group(1).rstrip().rstrip(';')

        missions.append(mission)

    return {
        'missions': missions,
    }

def template_context(template_base_path, template_path, *args, **kwargs):
    """Generic handler for fetching the context for a given template.
    """

    full_template_path = template_path[len(template_base_path):]
    supported_templates = {
        '{}/addons/missions/config.cpp.j2'.format(MOD_DIRNAME): missions_context,
    }

    return supported_templates[full_template_path](*args, **kwargs)

def build_copy_function(template_base_path, source_path, destination_path, *args, **kwargs):
    """Wrapper around shutil.copy2 to support generating templated files.
    """

    if str(source_path).endswith(JINJA2_TEMPLATE_EXT):
        # Jinja2 template file detected, generate the target file from it.
        destination_path = destination_path[:-len(JINJA2_TEMPLATE_EXT)]
        logging.info("Generating file '%s' from template", destination_path)
        with open(source_path, 'r') as template_source:
            template = jinja2.Template(template_source.read())
            with open(destination_path, 'w') as target_file:
                target_file.write(
                    template.render(
                        template_context(
                            template_base_path,
                            source_path,
                            *args,
                            **kwargs
                        ),
                    ),
                )
    else:
        return shutil.copy2(source_path, destination_path)


def main(template_path, missions_path, build_path, target_path):
    """Main function."""

    template_mod_path = os.path.join(template_path, MOD_DIRNAME)
    build_mod_path = os.path.join(build_path, MOD_DIRNAME)
    try:
        shutil.rmtree(build_mod_path)
        logging.info("Cleaning up build directory '%s'", build_mod_path)
    except FileNotFoundError:
        pass

    # Copy the template directory into the temporary build directory, and
    # generate templated files.
    shutil.copytree(
        template_mod_path,
        build_mod_path,
        copy_function=functools.partial(
            build_copy_function,
            template_path, missions_path=missions_path
        ),
    )

    # Populate the build directory with submitted missions
    for mission_dir in os.listdir(missions_path):
        mission_path = os.path.join(missions_path, mission_dir)
        statinfo = os.stat(mission_path)
        if not stat.S_ISDIR(statinfo.st_mode):
            continue
        shutil.copytree(
            os.path.join(missions_path, mission_dir),
            os.path.join(build_mod_path, MISSIONS_DIR_PATH, mission_dir),
        )

    target_mod_path = os.path.join(target_path, MOD_DIRNAME)
    try:
        shutil.rmtree(target_mod_path)
        logging.info("Cleaning up target directory '%s'", target_mod_path)
    except FileNotFoundError:
        pass

    # Populate the final target directory while ignoring to-be-pboized
    # subdirectories
    shutil.copytree(
        build_mod_path,
        target_mod_path,
        ignore=shutil.ignore_patterns('missions'),
    )
    logging.info("Generating missions.pbo")
    subprocess.check_call([
        'valgrind',
        MAKEPBO_PATH,
        "-A",
        os.path.join(build_mod_path, 'addons/missions'),
        os.path.join(target_mod_path, 'addons/missions.pbo')
    ])

if __name__ == '__main__':
    ARGS = PARSER.parse_args()
    LOGGER = logging.getLogger()
    LOGGER.setLevel(logging.INFO)
    main(**ARGS.__dict__)

#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
