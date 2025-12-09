import sys, os
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
	sys.path.insert(0, proj_root)

from database.database_migrator import DatabaseMigrator

m = DatabaseMigrator()
ok, msg = m.test_mssql_connection('localhost\\SQLEXPRESS','', 'clinic_db', '', '', 'ODBC Driver 17 for SQL Server', False)
print(ok)
print(msg)
