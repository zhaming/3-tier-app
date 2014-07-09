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
        """
        Make a call to szradm, check for errors, and return the output
        """

        params = copy.copy(params)
        params.insert(0, "/usr/local/bin/szradm")
        proc = subprocess.Popen(params, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.wait():
            raise FarmRoleException("Unable to access szradm: %s", proc.stderr.read())
        return ElementTree.parse(proc.stdout)

    def _get_farm_roles(self, behaviour):
        """
        Retrieve the list of Farm Roles matching a selected behaviour in the
        current Farm

        Internally, this invokes szradm -q list-roles and parses the XML
        """

        args = ["-q", "list-roles"]
        t = self._szradm(args)
        all_roles = t.find("roles")

        matching_roles = []
        for role in all_roles:
            behaviours = role.attrib["behaviour"].split(",")
            if behaviour in role.attrib["behaviour"]:
                matching_roles.append(role)

        return matching_roles

    def _get_farm_role(self, behaviour):
        """
        Retrieve the Farm Role matching a selected behaviour in the
        current Farm

        This function will fail if multiple Farm Roles match the same
        behaviour
        """

        matching_roles = self._get_farm_roles(behaviour)

        if not matching_roles:
            raise FarmRoleNotFound()
        elif len(matching_roles) > 1:
            raise DuplicateFarmRole()
        else:
            role, = matching_roles
            return role

    def get_farm_role_id(self, behaviour):
        """
        Get the ID for the Farm Role matching a selected behaviour in the
        current Farm

        This function will fail if multiple Farm Roles match the same
        behaviour
        """
        role = self._get_farm_role(behaviour)
        return int(role.attrib["id"])

    def get_farm_role_hosts(self, behaviour):
        """
        Get a list of Hosts for the Farm Role matching a selected behaviour
        in the current Farm

        Returns a list of dicts. Each dict represents a host

        This function will fail if multiple Farm Roles match the same
        behaviour
        """
        role = self._get_farm_role(behaviour)
        hosts = role.find("hosts")
        return [host.attrib for host in hosts.findall("host")]

    def get_farm_role_params(self, farm_role_id):
        """
        Returns the Role parameters for the Farm Role matching the selected ID
        in the current Farm
        """
        params = ["-q", "list-farm-role-params", "farm-role-id={0}".format(farm_role_id)]
        return FarmRoleParams(self._szradm(params))


def prepare_config_files(engine):
    mysql_role = "mysql2"

    # Retrieve the ID of the MySQL Role
    mysql_role_id = engine.get_farm_role_id(mysql_role)

    # Retrieve the list of MySQL hosts
    mysql_hosts = engine.get_farm_role_hosts(mysql_role)

    # Retrieve MySQL configuration
    mysql_params = engine.get_farm_role_params(mysql_role_id)

    # Create configuration files
    files = []

    # Start with MySQL configuration
    # We're using the Scalr admin user to access the database
    # Note: this is pretty unsafe. Don't use this in production - this is only
    # an example
    files.append(("mysql-username", "scalr"))
    files.append(("mysql-password", mysql_params.mysql2.root_password))

    # Create a filter function that lets us parse through the list of MySQL
    # servers and tell the master from the slaves
    def hosts_by_replication(replicating):
        replicating = "1" if replicating else "0"
        replication_filter = lambda host: host["replication-master"] == replicating

        running_filter = lambda host: host["status"] == "Running"

        hosts = filter(running_filter, filter(replication_filter, mysql_hosts))
        return "\n".join([host["internal-ip"] for host in hosts])

    # Create a configuration file with the MySQL master's IP
    files.append(("mysql-master", hosts_by_replication(True)))

    # Add a configuration file with MySQL slave IPs
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
            f.write(contents or "")


if __name__ == "__main__":
    main()
