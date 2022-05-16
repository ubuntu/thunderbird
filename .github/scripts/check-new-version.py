#!/usr/bin/python3

import logging
import lxml.html
import sys
from http import HTTPStatus
from packaging import version
from urllib import request


ROOT_URL = "https://ftp.mozilla.org/pub/thunderbird/candidates/"

BETA = "beta"
RELEASE = "release"
ESR = "esr"
CHANNELS = (BETA, RELEASE, ESR)


def get_latest_build(candidate):
    result = request.urlopen(ROOT_URL + candidate + "-candidates/")
    if result.getcode() != HTTPStatus.OK:
        logging.error("failed to fetch the list of builds for {}"
                      .format(candidate))
        return 0
    builds = lxml.html.fromstring(result.read())
    builds = builds.xpath("//a[contains(@href,'-candidates/build')]/text()")
    builds.sort()
    return int(builds[-1][:-1].split('build')[-1])


def test_version(current_version, candidate):
    nv = version.parse(candidate)
    cv = version.parse(current_version.split('-')[0])
    if nv >= cv:
        build = get_latest_build(candidate)
        if nv > cv or build > int(current_version.split('-')[1]):
            return '{}-{}'.format(candidate, build)
    return None


def check_new_candidates(channel, current_version):
    new_version = current_version
    result = request.urlopen(ROOT_URL)
    if result.getcode() != HTTPStatus.OK:
        sys.exit("failed to fetch list of candidates")
    candidates = lxml.html.fromstring(result.read())
    candidates = candidates.xpath("//a[contains(@href,'-candidates/')]/text()")
    candidates = [c[:-12] for c in candidates if not c.startswith("None")]
    for candidate in candidates:
        if channel == BETA and "b" not in candidate:
            continue
        if channel == ESR and not candidate.endswith("esr"):
            continue
        if channel == RELEASE and \
           ("b" in candidate or candidate.endswith("esr")):
            continue
        new_version = test_version(new_version, candidate) or new_version
    if new_version != current_version:
        logging.info("new version: {} > {}"
                     .format(new_version, current_version))
        print(new_version)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    if len(sys.argv) != 3:
        logging.error("Usage: {program} channel current_version"
                      .format(program=sys.argv[0]))
        sys.exit(1)
    assert sys.argv[1] in CHANNELS
    check_new_candidates(*sys.argv[1:])
