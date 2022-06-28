#!/usr/bin/python3

import configparser
import os.path
import sys


# Mozilla products, when not packaged as a snap, use dedicated profiles per
# installation by default, unless instructed otherwise (legacy mode). See
# https://support.mozilla.org/en-US/kb/understanding-depth-profile-installation
# for details.
# We want to import existing profiles from a package of Firefox typically
# installed in a well-known location. The following is a list of hashes for
# such well-known locations, in descending order of popularity/likeliness
# on distributions compatible with snaps:
KNOWN_INSTALL_HASHES = [
    'FDC34C9F024745EB',  # /usr/lib/thunderbird (Debian, Ubuntu, Arch)
    '3DDF446CE6CB1A45',  # /usr/lib64/thunderbird (Fedora)
    '9238613B8C3D2579',  # /opt/thunderbird (Gentoo thunderbird-bin)
]


def _patch_imported_profiles(profiles_file):
    profiles = configparser.RawConfigParser()
    profiles.optionxform = lambda option: option
    profiles.read(profiles_file)

    known_install = False
    for known_hash in KNOWN_INSTALL_HASHES:
        install_section = 'Install{}'.format(known_hash)
        if install_section in profiles:
            known_install = True
            break
    if not known_install:
        return

    try:
        profile_path = profiles.get(install_section, 'Default')
    except configparser.NoOptionError:
        return
    if not profile_path:
        return
    print('Found default profile: {}'.format(profile_path))

    for section in profiles:
        if section.startswith('Profile'):
            try:
                path = profiles.get(section, 'Path')
            except configparser.NoOptionError:
                continue
            else:
                if path == profile_path:
                    # We found the section for the default profile,
                    # explicitly mark it as such …
                    profiles.set(section, 'Default', '1')
                    # … and remove the default marker from any other profile
                    # that might have had it.
                    for other_section in profiles:
                        if other_section.startswith('Profile') and \
                                other_section != section:
                            profiles.remove_option(other_section, 'Default')
                    # Delete the Install section as it is meaningless
                    # (and unused) in legacy mode.
                    profiles.remove_section(install_section)
                    # Write back the modified profiles.ini
                    with open(profiles_file, 'w') as profiles_fd:
                        profiles.write(profiles_fd, False)
                    return


if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
        expected_arg = '/path/to/profiles_dir/profiles.ini'
        print('Usage: {} {}'.format(sys.argv[0], expected_arg))
        sys.exit(1)
    _patch_imported_profiles(sys.argv[1])
