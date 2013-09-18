#!/usr/bin/env python
#coding:utf-8

# This script queries the state of MySQL servers and configures the
# WebApp

import subprocess
import copy
from xml.etree import ElementTree


class FarmRoleException(Exception):
    pass

class FarmRoleNotFound(FarmRoleException):
    pass

class DuplicateFarmRole(FarmRoleException):
    pass


class NoSuchParam(Exception):
    pass


class FarmRoleParams(object):
    def __init__(self, tree):
        self._tree = tree

    def __getattr__(self, attr):
        match = self._tree.find(attr)
        if match is None:
            raise NoSuchParam
        if match.getchildren():
            return FarmRoleParams(match)
        return match.text

    def __repr__(self):
        return "<FarmRoleParams: {0}>".format(self._tree.tag)


class RoleEngine(object):
    def _szradm(params):
        params = copy.copy(params)
        params.insert(0, "szradm")
        out_text = subprocess.check_output(params)
        return ElementTree.fromstring(out_text)

    def _get_farm_role(self, behaviour):
        args = ["-q", "list-roles", "behaviour={0}".format(behaviour)]
        t = self._szradm(args)
        roles = t.find("roles")
        role = roles.findall("role")

        if not role:
            raise FarmRoleNotFound()
        elif len(role) > 1:
            raise DuplicateFarmRole()
        else:
            role, = role
            return role

    def get_farm_role_id(self, behaviour):
        role = self._get_farm_role(behaviour)
        return int(role.attrib["id"])

    def get_farm_role_hosts(self, behaviour):
        role = self._get_farm_role(behaviour)
        hosts = role.find("hosts")
        return [host.attrib for host in hosts.findall("host")]

    def get_farm_role_params(self, farm_role_id):
        params = ["-q", "list-farm-role-params", "farm-role-id={0}".format(farm_role_id)]
        return FarmRoleParams(self._szradm(params))
