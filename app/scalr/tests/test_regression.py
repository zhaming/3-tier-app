#coding:utf-8

from scalr.tests import test_app
from scalr.tests import test_db

class CodingTestCase(test_app.BaseAppTestCase):
    def test_coding(self):
        """
        Check that we don't get an error due to encoding.
        """
        insert = 'é'

        r = self.client.post('/', data={'value': insert})
        self.assertEqual(r.status_code, 302)

        r = self.client.get('/')
        self.assertIn(insert, r.data)


class SocketResolutionErrorsTestCase(test_db.DBTestCase):
    def test_no_host(self):
        """
        Check that we catch all types of socket error when resolving the IPs
        for the DB hosts.
        """
        for invalid in ("", "example.com"):
            self.conn_info._master = invalid
            self.assertEqual(1, len(self.conn_info.master.ips()))
            self.assertIn("Resolution error", self.conn_info.master.ips()[0])
