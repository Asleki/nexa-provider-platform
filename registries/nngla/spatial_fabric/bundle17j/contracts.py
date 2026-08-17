from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class AllocatorFamily(str,Enum):
    ADDRESS_ID='ADDRESS_ID'; ADDRESS_DISPLAY_NUMBER='ADDRESS_DISPLAY_NUMBER'; PARCEL_REFERENCE='PARCEL_REFERENCE'; SITE_ID='SITE_ID'; TITLE_REFERENCE='TITLE_REFERENCE'; GEOMETRY_ID_BASELINE='GEOMETRY_ID_BASELINE'
class ExecutionBasis(str,Enum):
    MEMORY_CONTRACT='MEMORY_CONTRACT'; POSTGRESQL_CONTRACT='POSTGRESQL_CONTRACT'; POSTGRESQL_INTEGRATION='POSTGRESQL_INTEGRATION'
@dataclass(frozen=True,slots=True)
class StressResult:
    scenario_id:str; allocator_family:AllocatorFamily; execution_basis:ExecutionBasis; parallel_requests:int; requested_count:int; successful_count:int; unique_identity_count:int; duplicate_identity_count:int; collision_count:int; idempotent_replay_count:int; rollback_count:int; retry_count:int; unexpected_error_count:int; elapsed_ms:float; operations_per_second:float; status:str
    def __post_init__(self):
        if self.parallel_requests<1 or self.requested_count<0: raise ValueError('invalid stress dimensions')
        if min(self.successful_count,self.unique_identity_count,self.duplicate_identity_count,self.collision_count,self.idempotent_replay_count,self.rollback_count,self.retry_count,self.unexpected_error_count)<0: raise ValueError('stress counts cannot be negative')
        if self.elapsed_ms<0 or self.operations_per_second<0: raise ValueError('stress timing cannot be negative')
        if self.status not in {'PASS','FAIL','CONTRACT_READY_NOT_EXECUTED'}: raise ValueError('unsupported stress status')
@dataclass(frozen=True,slots=True)
class RecoveryResult:
    case_id:str; target_family:str; sequence_consumed:bool; transaction_committed:bool; identifier_reused:bool; idempotent_retry_same_result:bool; expected_gap_allowed:bool; status:str
    def __post_init__(self):
        if self.identifier_reused: raise ValueError('immutable identifiers must never be reused')
        if self.status!='PASS': raise ValueError('recovery contract must pass')
__all__=['AllocatorFamily','ExecutionBasis','StressResult','RecoveryResult']
