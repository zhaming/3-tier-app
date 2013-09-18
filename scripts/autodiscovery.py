#!/usr/bin/env python
#coding:utf-8

# This script queries the state of MySQL servers and configures the
# WebApp

import os
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


class FarmRoleEngine(object):
    def _szradm(self, params):
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


def prepare_config_files(engine):
    mysql_role = "mysql2"

    mysql_role_id = engine.get_farm_role_id(mysql_role)
    mysql_hosts = engine.get_farm_role_hosts(mysql_role)
    mysql_params = engine.get_farm_role_params(mysql_role_id)

    files = []
    files.append(("mysql-username", "root"))
    files.append(("mysql-password", mysql_params.mysql2.root_password))

    def hosts_by_replication(replicating):
        replicating = "1" if replicating else "0"
        f = lambda host: host["replication-master"] == replicating
        hosts = filter(f, mysql_hosts)
        return "\n".join([host["internal-ip"] for host in hosts])

    files.append(("mysql-master", hosts_by_replication(True)))
    files.append(("mysql-slave", hosts_by_replication(False)))

    return files


def main():
    engine = FarmRoleEngine()
    config_dir = "/var/config"

    try:
        os.mkdir(config_dir)
    except OSError:
        pass

    for filename, contents in prepare_config_files(engine):
        with open(os.path.join(config_dir, filename), "w") as f:
            f.write(contents)


if __name__ == "__main__":
    main()
