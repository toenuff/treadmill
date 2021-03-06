"""
Unit test for treadmill admin.
"""

# Disable C0302: Too many lines in the module
# pylint: disable=C0302

import hashlib
import unittest

# Disable W0611: Unused import
import tests.treadmill_test_deps  # pylint: disable=W0611

import mock
import ldap3

import treadmill
from treadmill import admin


class AdminTest(unittest.TestCase):
    """Tests supervisor routines."""

    def test_and_query(self):
        """Test."""
        query = admin.AndQuery('a', 1)
        self.assertEquals('(a=1)', str(query))

        query('b', '*')
        self.assertEquals('(&(a=1)(b=*))', str(query))

    def test_entry_to_dict(self):
        """Test entry to dict conversion."""
        # Disable W0212: Test access protected members of admin module.
        # pylint: disable=W0212
        schema = [
            ('a', 'a', str),
            ('b', 'b', [str]),
            ('c', 'C', int),
        ]

        self.assertEquals({'a': '1', 'b': ['x'], 'C': 1},
                          admin._entry_2_dict({'a': ['1'],
                                               'b': ['x'],
                                               'c': ['1']}, schema))

        self.assertEquals({'a': ['1'], 'b': ['x'], 'c': ['1']},
                          admin._dict_2_entry({'a': '1',
                                               'b': ['x'],
                                               'C': 1}, schema))

    def test_group_by_opt(self):
        """Tests group by attribute option."""
        # Disable W0212: Test access protected members of admin module.
        # pylint: disable=W0212
        self.assertEquals({'a': [('xxx', 'a', ['1']),
                                 ('yyy', 'a', ['2'])],
                           'b': [('xxx', 'b', ['3'])]},
                          admin._group_entry_by_opt({'xxx;a': ['1'],
                                                     'xxx;b': ['3'],
                                                     'yyy;a': ['2']}))

    def test_grouped_to_list_of_dict(self):
        """Test conversion of grouped by opt elements to dicts."""
        # Disable W0212: Test access protected members of admin module.
        # pylint: disable=W0212
        self.assertEquals(
            [{'name': 'http', 'port': 80}, {'name': 'tcp', 'port': 1000}],
            admin._grouped_to_list_of_dict(
                {'tm-ep-1': [('name', 'tm-ep-1', ['http']),
                             ('port', 'tm-ep-1', ['80']),
                             ('service-name', 'tm-s-1', ['x'])],
                 'tm-ep-2': [('name', 'tm-ep-2', ['tcp']),
                             ('port', 'tm-ep-2', ['1000']),
                             ('service-name', 'tm-s-2', ['x'])]},
                'tm-ep-',
                [('name', 'name', str), ('port', 'port', int)]))

    def test_remove_empty(self):
        """Test removal of empty values from entry."""
        # Access to protected member.
        #
        # pylint: disable=W0212
        self.assertEquals(
            {'aaa': ['a']},
            admin._remove_empty({'aaa': ['a'], 'b': [], 'c': {'a': []}})
        )

    def test_app_to_entry(self):
        """Tests convertion of app dictionary to ldap entry."""
        app = {
            '_id': 'xxx',
            'cpu': '100%',
            'memory': '1G',
            'disk': '1G',
            'tickets': [u'a', None, 'b'],
            'features': [],
            'environ': [{'name': 'a', 'value': 'b'}],
            'services': [
                {
                    'name': 'a',
                    'command': '/a',
                    'restart': {
                        'limit': 3,
                        'interval': 30,
                    },
                },
                {
                    'name': 'b',
                    'command': '/b',
                },
                {
                    'name': 'c',
                    'command': '/c',
                    'restart': {
                        'limit': 0,
                    },
                },
            ],
            'endpoints': [
                {'name': 'y', 'port': 2, 'type': 'infra'},
                {'name': 'x', 'port': 1, 'type': 'infra', 'proto': 'udp'},
            ],
            'affinity_limits': {'server': 1, 'rack': 2},
        }

        md5_a = hashlib.md5('a').hexdigest()
        md5_b = hashlib.md5('b').hexdigest()
        md5_c = hashlib.md5('c').hexdigest()
        md5_x = hashlib.md5('x').hexdigest()
        md5_y = hashlib.md5('y').hexdigest()
        md5_srv = hashlib.md5('server').hexdigest()
        md5_rack = hashlib.md5('rack').hexdigest()

        ldap_entry = {
            'app': ['xxx'],
            'cpu': ['100%'],
            'memory': ['1G'],
            'disk': ['1G'],
            'ticket': ['a', 'b'],
            'service-name;tm-service-' + md5_a: ['a'],
            'service-name;tm-service-' + md5_b: ['b'],
            'service-name;tm-service-' + md5_c: ['c'],
            'service-restart-limit;tm-service-' + md5_a: ['3'],
            'service-restart-limit;tm-service-' + md5_b: ['5'],
            'service-restart-limit;tm-service-' + md5_c: ['0'],
            'service-restart-interval;tm-service-' + md5_a: ['30'],
            'service-restart-interval;tm-service-' + md5_b: ['60'],
            'service-restart-interval;tm-service-' + md5_c: ['60'],
            'service-command;tm-service-' + md5_a: ['/a'],
            'service-command;tm-service-' + md5_b: ['/b'],
            'service-command;tm-service-' + md5_c: ['/c'],
            'endpoint-name;tm-endpoint-' + md5_x: ['x'],
            'endpoint-name;tm-endpoint-' + md5_y: ['y'],
            'endpoint-port;tm-endpoint-' + md5_x: ['1'],
            'endpoint-port;tm-endpoint-' + md5_y: ['2'],
            'endpoint-type;tm-endpoint-' + md5_x: ['infra'],
            'endpoint-type;tm-endpoint-' + md5_y: ['infra'],
            'endpoint-proto;tm-endpoint-' + md5_x: ['udp'],
            'envvar-name;tm-envvar-' + md5_a: ['a'],
            'envvar-value;tm-envvar-' + md5_a: ['b'],
            'affinity-level;tm-affinity-' + md5_srv: ['server'],
            'affinity-limit;tm-affinity-' + md5_srv: ['1'],
            'affinity-level;tm-affinity-' + md5_rack: ['rack'],
            'affinity-limit;tm-affinity-' + md5_rack: ['2'],
        }

        self.assertEquals(ldap_entry, admin.Application(None).to_entry(app))

        # When converting to entry, None are skipped, and unicode is converted
        # to str.
        #
        # Adjuest app['tickets'] accordingly.
        app['tickets'] = ['a', 'b']
        # Account for default restart values
        app['services'][1]['restart'] = {'limit': 5, 'interval': 60}
        app['services'][2]['restart']['interval'] = 60
        self.assertEquals(app, admin.Application(None).from_entry(ldap_entry))

    def test_server_to_entry(self):
        """Tests convertion of app dictionary to ldap entry."""
        srv = {
            '_id': 'xxx',
            'cell': 'yyy',
            'traits': ['a', 'b', 'c'],
        }

        ldap_entry = {
            'server': ['xxx'],
            'cell': ['yyy'],
            'trait': ['a', 'b', 'c'],
        }

        self.assertEquals(ldap_entry, admin.Server(None).to_entry(srv))
        self.assertEquals(srv, admin.Server(None).from_entry(ldap_entry))

    def test_cell_to_entry(self):
        """Tests conversion of cell to ldap entry."""
        cell = {
            '_id': 'test',
            'username': 'xxx',
            'location': 'x',
            'archive-server': 'y',
            'archive-username': 'z',
            'version': '1.2.3',
            'root': '',
            'ssq-namespace': 's',
            'masters': [
                {'idx': 1,
                 'hostname': 'abc',
                 'zk-client-port': 5000,
                 'zk-jmx-port': 6000,
                 'zk-followers-port': 7000,
                 'zk-election-port': 8000,
                 'kafka-client-port': 9000}
            ]
        }
        cell_admin = admin.Cell(None)
        self.assertEquals(cell,
                          cell_admin.from_entry(cell_admin.to_entry(cell)))

    def test_schema(self):
        """Test schema parsing."""
        # Disable W0212: Test access protected members of admin module.
        # pylint: disable=W0212
        attrs = [
            '{0}( %s NAME x1 DESC \'x x\''
            ' ORDERING integerOrderingMatch'
            ' SYNTAX 1.3.6.1.4.1.1466.115.121.1.27'
            ' )' % (admin._TREADMILL_ATTR_OID_PREFIX + '11'),
            '{1}( %s NAME x2 DESC \'x x\''
            ' SUBSTR caseIgnoreSubstringsMatch'
            ' EQUALITY caseIgnoreMatch'
            ' SYNTAX 1.3.6.1.4.1.1466.115.121.1.15'
            ' )' % (admin._TREADMILL_ATTR_OID_PREFIX + '22'),
        ]

        obj_classes = [
            '{0}( %s NAME o1 DESC \'x x\''
            ' SUP top STRUCTURAL'
            ' MUST ( xxx ) MAY ( a $ b )'
            ' )' % (admin._TREADMILL_OBJCLS_OID_PREFIX + '33'),
        ]

        admin_obj = admin.Admin(None, None)
        admin_obj.ldap = ldap3.Connection(ldap3.Server('fake'),
                                          client_strategy=ldap3.MOCK_SYNC)

        admin_obj.ldap.strategy.add_entry(
            'cn={1}treadmill,cn=schema,cn=config',
            {'olcAttributeTypes': attrs, 'olcObjectClasses': obj_classes}
        )

        admin_obj.ldap.bind()

        self.assertEquals(
            {
                'dn': 'cn={1}treadmill,cn=schema,cn=config',
                'objectClasses': {
                    'o1': {
                        'idx': 33,
                        'desc': 'x x',
                        'must': ['xxx'],
                        'may': ['a', 'b'],
                    },
                },
                'attributeTypes': {
                    'x1': {
                        'idx': 11,
                        'desc': 'x x',
                        'type': 'int'
                    },
                    'x2': {
                        'idx': 22,
                        'desc': 'x x',
                        'type': 'str',
                        'ignore_case': True
                    },
                }
            },
            admin_obj.schema()
        )

    @mock.patch('ldap3.Connection.add', mock.Mock())
    def test_init(self):
        """Tests init logic."""
        admin_obj = admin.Admin(None, None)
        admin_obj.ldap = ldap3.Connection(ldap3.Server('fake'),
                                          client_strategy=ldap3.MOCK_SYNC)

        admin_obj.init('test.com')

        dn_list = [arg[0][0] for arg in admin_obj.ldap.add.call_args_list]

        self.assertTrue('dc=test,dc=com' in dn_list)
        self.assertTrue('ou=treadmill,dc=test,dc=com' in dn_list)
        self.assertTrue('ou=apps,ou=treadmill,dc=test,dc=com' in dn_list)


class TenantTest(unittest.TestCase):
    """Tests Tenant ldapobject routines."""

    def setUp(self):
        self.tnt = admin.Tenant(admin.Admin(None, 'ou=treadmill,dc=xx,dc=com'))

    def test_to_entry(self):
        """Tests convertion of tenant dictionary to ldap entry."""
        tenant = {'tenant': 'foo', 'systems': [3032]}
        ldap_entry = {
            'tenant': ['foo'],
            'system': ['3032'],
        }

        self.assertEquals(ldap_entry, self.tnt.to_entry(tenant))
        self.assertEquals(tenant, self.tnt.from_entry(ldap_entry))

        tenant = {'tenant': 'foo:bar', 'systems': [3032]}
        ldap_entry = {
            'tenant': ['foo:bar'],
            'system': ['3032'],
        }
        self.assertEquals(tenant, self.tnt.from_entry(ldap_entry))
        self.assertTrue(
            self.tnt.dn('foo:bar').startswith(
                'tenant=bar,tenant=foo,ou=allocations,'))


class AllocationTest(unittest.TestCase):
    """Tests Allocation ldapobject routines."""

    def setUp(self):
        self.alloc = admin.Allocation(
            admin.Admin(None, 'ou=treadmill,dc=xx,dc=com'))

    def test_dn(self):
        """Tests allocation identity to dn mapping."""
        self.assertTrue(
            self.alloc.dn('foo:bar/prod1').startswith(
                'allocation=prod1,tenant=bar,tenant=foo,ou=allocations,'))

    def test_to_entry(self):
        """Tests conversion of allocation to LDAP entry."""
        obj = {'environment': 'prod'}
        ldap_entry = {
            'environment': ['prod'],
        }
        self.assertEquals(ldap_entry, self.alloc.to_entry(obj))

    @mock.patch('treadmill.admin.Admin.search', mock.Mock())
    @mock.patch('treadmill.admin.LdapObject.get', mock.Mock(return_value={}))
    def test_get(self):
        """Tests loading cell allocations."""
        treadmill.admin.Admin.search.return_value = [
            ('cell=xxx,allocation=prod1,...',
             {'cell': ['xxx'],
              'memory': ['1G'],
              'cpu': ['100%'],
              'disk': ['2G'],
              'rank': [100],
              'trait': ['a', 'b'],
              'priority;tm-alloc-assignment-123': [80],
              'pattern;tm-alloc-assignment-123': ['ppp.ttt'],
              'priority;tm-alloc-assignment-345': [60],
              'pattern;tm-alloc-assignment-345': ['ppp.ddd']})
        ]
        obj = self.alloc.get('foo:bar/prod1')
        treadmill.admin.Admin.search.assert_called_with(
            search_base='allocation=prod1,tenant=bar,tenant=foo,'
                        'ou=allocations,ou=treadmill,dc=xx,dc=com',
            search_filter='(objectclass=tmCellAllocation)',
            attributes=mock.ANY
        )
        self.assertEquals(obj['reservations'][0]['cell'], 'xxx')
        self.assertEquals(obj['reservations'][0]['disk'], '2G')
        self.assertEquals(obj['reservations'][0]['rank'], 100)
        self.assertEquals(obj['reservations'][0]['traits'], ['a', 'b'])
        self.assertIn(
            {'pattern': 'ppp.ttt', 'priority': 80},
            obj['reservations'][0]['assignments'])


if __name__ == '__main__':
    unittest.main()
