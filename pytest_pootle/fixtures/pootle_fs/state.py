# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
from fnmatch import fnmatch

import pytest

from django.db.models import Q
from django.utils.functional import cached_property


FS_PATH_QS = OrderedDict((
    ("all", (
        (None, None, None))),
    ("language0", (
        (Q(pootle_path__startswith="/language0"),
         "/language0/*", None))),
    ("fs/language1", (
        (Q(pootle_path__startswith="/language1"),
         None, "/fs/language1/*"))),
    ("store0.po", (
        (Q(pootle_path__endswith="store0.po"),
         "*/store0.po", "*/store0.po"))),
    ("none", (
        (False, "/language0/*", "/fs/language1/*")))))


class DummyPlugin(object):

    def __init__(self, project):
        self.project = project

    def find_translations(self, fs_path=None, pootle_path=None):
        for pp in self.resources.stores.values_list("pootle_path", flat=True):
            if pootle_path and not fnmatch(pp, pootle_path):
                continue
            fp = self.get_fs_path(pp)
            if fs_path and not fnmatch(fp, fs_path):
                continue
            yield pp, fp

    @cached_property
    def resources(self):
        from pootle_fs.resources import FSProjectResources

        return FSProjectResources(self.project)

    def get_fs_path(self, pootle_path):
        return "/fs%s" % pootle_path


@pytest.fixture
def project0_dummy_plugin(settings, request):
    from pootle.core.plugin import provider
    from pootle_fs.delegate import fs_plugins
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    @provider(fs_plugins, weak=False)
    def plugin_provider(**kwargs):
        return dict(dummyfs=DummyPlugin)

    project = Project.objects.get(code="project0")
    settings.POOTLE_FS_PATH = "/tmp/foo/"
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"

    request.addfinalizer(
        lambda: fs_plugins.disconnect(plugin_provider))
    return FSPlugin(project)


@pytest.fixture(params=FS_PATH_QS.keys())
def fs_path_queries(project0_dummy_plugin, request):
    return project0_dummy_plugin, FS_PATH_QS[request.param]