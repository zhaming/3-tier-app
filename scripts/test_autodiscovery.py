#!/usr/bin/env python
#coding:utf-8
from xml.etree import ElementTree

import unittest

import autodiscovery

VALID_ROLES_RESPONSE = """<?xml version="1.0" ?>
<response>
    <roles>
        <role behaviour="mysql2,chef" id="123" name="mysql64-ubuntu1204" role-id="456">
            <hosts>
                <host cloud-location="us-east-1" external-ip="23.22.147.1" index="1" internal-ip="10.190.214.199" replication-master="1" status="Running"/>
                <host cloud-location="us-east-1" external-ip="54.227.143.73" index="2" internal-ip="10.157.42.56" replication-master="0" status="Running"/>
                <host cloud-location="us-east-1" external-ip="54.27.18.54" index="2" internal-ip="10.160.20.42" replication-master="0" status="Running"/>
            </hosts>
        </role>
    </roles>
</response>
"""

EMPTY_ROLES_RESPONSE = """<?xml version="1.0" ?>
<response>
    <roles/>
</response>
"""

DUPLICATE_ROLES_RESPONSE = """<?xml version="1.0" ?>
<response>
    <roles>
        <role behaviour="mysql2,chef" id="123" name="mysql64-ubuntu1204" role-id="456">
            <hosts/>
        </role>
        <role behaviour="mysql2,chef" id="456" name="mysql64-ubuntu1204" role-id="456">
            <hosts/>
        </role>
    </roles>
</response>
"""

FARM_ROLE_PARAMS_RESPONSE = """<?xml version="1.0" ?>
<response>
    <volumes/>
    <mysql2>
        <replication_master>1</replication_master>
        <volume_config>
            <iops/>
            <name>/dev/sdg</name>
            <tags>
                <farm_role_id>57838</farm_role_id>
                <service>mysql2</service>
                <creator>scalarizr</creator>
                <farm_id>16560</farm_id>
                <role_id>39552</role_id>
                <db_replication_role>1</db_replication_role>
            </tags>
            <avail_zone>us-east-1d</avail_zone>
            <volume_type>standard</volume_type>
            <fstype>ext3</fstype>
            <snap/>
            <mpoint>/mnt/dbstorage</mpoint>
            <version>2.0</version>
            <device>/dev/xvdg</device>
            <type>ebs</type>
            <id>vol-1301cc64</id>
            <size>10</size>
        </volume_config>
        <snapshot_config>
            <version>2.0</version>
            <type>ebs</type>
            <id>snap-c47ff7c5</id>
            <tags>
                <farm_role_id>57838</farm_role_id>
                <service>mysql2</service>
                <creator>scalarizr</creator>
                <log_pos>370</log_pos>
                <farm_id>16560</farm_id>
                <role_id>39552</role_id>
                <db_replication_role>1</db_replication_role>
                <log_file>binlog.000012</log_file>
            </tags>
            <description>MySQL data bundle (farm: 16560 role: mysql64-ubuntu1204)</description>
        </snapshot_config>
        <root_password>root_pwd</root_password>
        <repl_password>repl_pwd</repl_password>
        <stat_password>stat_pwd</stat_password>
        <log_pos>370</log_pos>
        <log_file>binlog.000012</log_file>
    </mysql2>
    <chef/>
</response>
"""


class TestFarmRoleEngine(autodiscovery.FarmRoleEngine):
    def __init__(self):
        self.responses = []
        self.params = []

    def _szradm(self, params):
        self.params.append(params)
        return ElementTree.fromstring(self.responses.pop(0))


class RoleEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = TestFarmRoleEngine()

    def test_ok(self):
        self.engine.responses = [VALID_ROLES_RESPONSE]
        role_id = self.engine.get_farm_role_id("mysql2")
        self.assertEqual(["-q list-roles behaviour=mysql2".split()], self.engine.params)
        self.assertEqual(123, role_id)

    def test_not_found(self):
        self.engine.responses = [EMPTY_ROLES_RESPONSE, EMPTY_ROLES_RESPONSE]
        self.assertRaises(autodiscovery.FarmRoleNotFound, self.engine._get_farm_role, "a")
        self.assertRaises(autodiscovery.FarmRoleException, self.engine._get_farm_role, "a")

    def test_duplicate(self):
        self.engine.responses = [DUPLICATE_ROLES_RESPONSE, DUPLICATE_ROLES_RESPONSE]
        self.assertRaises(autodiscovery.DuplicateFarmRole, self.engine._get_farm_role, "a")
        self.assertRaises(autodiscovery.FarmRoleException, self.engine._get_farm_role, "a")

    def test_get_farm_role_hosts(self):
        self.engine.responses = [VALID_ROLES_RESPONSE]
        hosts = self.engine.get_farm_role_hosts("mysql2")
        self.assertEqual(["-q list-roles behaviour=mysql2".split()], self.engine.params)
        self.assertEqual(3, len(hosts))
        self.assertEqual("1", hosts[0]["index"])
        self.assertEqual("2", hosts[1]["index"])
        self.assertEqual("0", hosts[1]["replication-master"])

    def test_get_farm_role_params(self):
        self.engine.responses = [FARM_ROLE_PARAMS_RESPONSE]
        params = self.engine.get_farm_role_params("123")
        self.assertEqual(["-q list-farm-role-params farm-role-id=123".split()], self.engine.params)
        self.assertEqual("response", params._tree.tag)


class RoleParamsTestCase(unittest.TestCase):
    def setUp(self):
        self.params = autodiscovery.FarmRoleParams(ElementTree.fromstring(FARM_ROLE_PARAMS_RESPONSE))

    def test_traversal(self):
        vc = self.params.mysql2.volume_config
        self.assertIsInstance(vc, autodiscovery.FarmRoleParams)
        self.assertEqual("volume_config", vc._tree.tag)

    def test_attribute(self):
        self.assertEqual("root_pwd", self.params.mysql2.root_password)

    def test_exceptions(self):
        self.assertRaises(autodiscovery.NoSuchParam, getattr, self.params, "blah")


class ConfigParamsTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = TestFarmRoleEngine()
        self.engine.responses = [VALID_ROLES_RESPONSE, VALID_ROLES_RESPONSE, FARM_ROLE_PARAMS_RESPONSE]

    def test_config(self):
        config = autodiscovery.prepare_config_files(self.engine)
        self.assertEqual([
            ('mysql-username', 'root'), ('mysql-password', 'root_pwd'),
            ('mysql-master', '10.190.214.199'), ('mysql-slave', '10.157.42.56\n10.160.20.42')
        ], config)


if __name__ == "__main__":
    unittest.main()
