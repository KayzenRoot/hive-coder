from __future__ import annotations

"""Authority-free staging plan that binds worktree observations to blob OIDs."""

from dataclasses import dataclass
from typing import Sequence

from .git_loose_object_transaction import GitLooseObjectPreparation
from .git_stage import GitStagePreparation, GitStageUnavailableError

STAGE_PLAN_CONTRACT="hive-git-stage-plan-v1"

@dataclass(frozen=True)
class GitStagePathPlan:
    path:str
    worktree_sha256:str
    worktree_bytes:int
    blob_oid:str

@dataclass(frozen=True)
class GitStagePlan:
    contract:str
    repository_identity:str
    repository_head:str
    index_sha256:str
    paths:tuple[GitStagePathPlan,...]


def bind_stage_plan(stage:GitStagePreparation,objects:Sequence[GitLooseObjectPreparation])->GitStagePlan:
    observed=stage.observed
    by_digest={(obj.candidate.content_sha256,obj.candidate.content_bytes):obj for obj in objects}
    plans=[]
    for item in observed.worktree_states:
        obj=by_digest.get((item.content_sha256,item.content_bytes))
        if obj is None: raise ValueError(f"no approved blob candidate for {item.path}")
        plans.append(GitStagePathPlan(item.path,item.content_sha256,item.content_bytes,obj.candidate.oid))
    if len(plans)!=len(objects): raise ValueError("object candidates must bind one-to-one to approved worktree states")
    return GitStagePlan(STAGE_PLAN_CONTRACT,observed.repository_identity,observed.repository_head,observed.index_sha256,tuple(plans))

class PreAuthorityStageExecutor:
    mutation_authority_enabled=False
    def publish(self,plan:GitStagePlan,*,permit_token:str)->None:
        del plan,permit_token
        raise GitStageUnavailableError("governed Git staging publication is not yet authorized")

__all__=["STAGE_PLAN_CONTRACT","GitStagePathPlan","GitStagePlan","bind_stage_plan","PreAuthorityStageExecutor"]