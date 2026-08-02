import pytest
from shared.runtime.runtime_config import RuntimeEnvironment
from database.migration_control.connection import MigrationDatabaseTarget
from database.migration_control.target import ActualDatabaseTarget,MigrationTargetVerifier
from database.migration_control.errors import MigrationTargetError,MigrationTLSRequiredError

def test_target_contract_and_actual_verification():
 t=MigrationDatabaseTarget('h','npp_dev','u',RuntimeEnvironment.DEVELOPMENT)
 a=ActualDatabaseTarget('npp_dev','u','u',None,5432,True,'PostgreSQL')
 assert MigrationTargetVerifier().verify(t,a) is a
 with pytest.raises(MigrationTargetError): MigrationTargetVerifier().verify(t,ActualDatabaseTarget('postgres','u','u',None,5432,True,'x'))
 with pytest.raises(MigrationTLSRequiredError): MigrationTargetVerifier().verify(t,ActualDatabaseTarget('npp_dev','u','u',None,5432,False,'x'))
