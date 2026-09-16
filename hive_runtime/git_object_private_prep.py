from __future__ import annotations

"""Private loose-object preparation contract with zero publication authority."""

import hashlib
from dataclasses import dataclass

from .git_loose_object_transaction import GitLooseObjectPreparation
from .git_stage import GitStageUnavailableError

PRIVATE_OBJECT_PREP_CONTRACT="hive-git-private-object-prep-v1"

@dataclass(frozen=True)
class PrivateObjectPlan:
    contract:str
    oid:str
    object_relative_path:str
    compressed_sha256:str
    compressed_bytes:int
    temp_name_prefix:str


def plan_private_object(prepared:GitLooseObjectPreparation,compressed:bytes)->PrivateObjectPlan:
    digest=hashlib.sha256(compressed).hexdigest()
    if digest!=prepared.compressed_sha256 or len(compressed)!=prepared.compressed_bytes: raise ValueError("compressed blob no longer matches approved preparation")
    return PrivateObjectPlan(PRIVATE_OBJECT_PREP_CONTRACT,prepared.candidate.oid,prepared.relative_object_path,digest,len(compressed),f".hive-{prepared.candidate.oid}-")

class PrivateObjectPreparer:
    mutation_authority_enabled=False
    def plan(self,prepared:GitLooseObjectPreparation,compressed:bytes)->PrivateObjectPlan:return plan_private_object(prepared,compressed)
    def materialize_private_temp(self,plan:PrivateObjectPlan,compressed:bytes)->None:
        del plan,compressed
        raise GitStageUnavailableError("private object materialization is not yet platform-proven")
    def publish(self,plan:PrivateObjectPlan)->None:
        del plan
        raise GitStageUnavailableError("Git object publication authority is unavailable")

__all__=["PRIVATE_OBJECT_PREP_CONTRACT","PrivateObjectPlan","PrivateObjectPreparer","plan_private_object"]