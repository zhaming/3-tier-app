#coding:utf-8
from __future__ import unicode_literals

from scalr.tests import test_app


class CodingTestCase(test_app.BaseAppTestCase):
    def test_coding(self):
        """
        Check that we don't get an error due to encoding.
        """
        insert = 'é'

        r = self.client.post('/', data={'value': insert})
        self.assertEqual(r.status_code, 302)


        r = self.client.get('/')
        self.assertIn(insert, r.data.decode('utf-8'))
