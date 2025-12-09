import sys
import os
import json
import logging

# Asegurar que la raíz del proyecto esté en sys.path
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from database.database_migrator import DatabaseMigrator

logging.basicConfig(level=logging.INFO)

m = DatabaseMigrator(config_path='config.ini')
conf = m.load_mssql_config()

host = conf.get('host')
port = conf.get('port')
database = conf.get('database')
user = conf.get('user')
password = conf.get('password')
driver = conf.get('driver')
trusted = conf.get('trusted')

print('Testing MSSQL connection with:')
print(json.dumps({
    'host': host,
    'port': port,
    'database': database,
    'user': bool(user) and '***' or '',
    'driver': driver,
    'trusted': trusted
}, indent=2))

ok, msg = m.test_mssql_connection(host, port, database, user, password, driver, trusted)

print('\nRESULT:')
print(ok)
print(msg)

if not ok:
    sys.exit(2)
else:
    sys.exit(0)
