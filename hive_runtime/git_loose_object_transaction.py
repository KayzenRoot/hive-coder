from __future__ import annotations

"""Pre-authority loose Git object preparation and exact existing-object proof."""

import hashlib
import os
import stat
import zlib
from dataclasses import dataclass
from pathlib import Path

from .git_object_candidate import GitBlobCandidate, MAX_GIT_BLOB_BYTES, prepare_git_blob_candidate
from .git_object_store_inspector import GitObjectStoreEnvelope, inspect_local_object_store
from .git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError

LOOSE_OBJECT_TRANSACTION_CONTRACT = "hive-git-loose-object-transaction-v1"
MAX_LOOSE_OBJECT_COMPRESSED_BYTES = MAX_GIT_BLOB_BYTES + (1024 * 1024)

@dataclass(frozen=True)
class GitLooseObjectPreparation:
    contract: str; candidate: GitBlobCandidate; store: GitObjectStoreEnvelope; fanout: str; leaf: str; compressed_sha256: str; compressed_bytes: int
    @property
    def relative_object_path(self) -> str: return f"objects/{self.fanout}/{self.leaf}"

@dataclass(frozen=True)
class ExistingLooseObjectProof:
    oid: str; identity: str; compressed_sha256: str; compressed_bytes: int; content_sha256: str; content_bytes: int

def prepare_loose_blob(workspace_root: str | Path, content: bytes) -> tuple[GitLooseObjectPreparation, bytes]:
    candidate = prepare_git_blob_candidate(content); store = inspect_local_object_store(workspace_root)
    if store.object_format != "sha1" or len(candidate.oid) != 40: raise GitStageUnsupportedRepositoryError("loose-object format is outside the proven envelope")
    framed = b"blob " + str(len(content)).encode("ascii") + b"\x00" + content; compressed = zlib.compress(framed)
    return GitLooseObjectPreparation(LOOSE_OBJECT_TRANSACTION_CONTRACT,candidate,store,candidate.oid[:2],candidate.oid[2:],hashlib.sha256(compressed).hexdigest(),len(compressed)), compressed

def _read_existing_regular_nofollow(path: Path) -> tuple[bytes, os.stat_result]:
    flags=os.O_RDONLY|getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_NONBLOCK",0)
    try: fd=os.open(path,flags)
    except FileNotFoundError: raise
    except OSError as exc: raise GitStageUnsupportedRepositoryError("existing loose object is not safely readable") from exc
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode): raise GitStageUnsupportedRepositoryError("existing loose object is not a regular file")
        chunks=[]; total=0
        while True:
            chunk=os.read(fd,1024*1024)
            if not chunk: break
            total+=len(chunk)
            if total>MAX_LOOSE_OBJECT_COMPRESSED_BYTES: raise GitStageUnsupportedRepositoryError("existing loose object exceeds governed compressed ceiling")
            chunks.append(chunk)
        return b"".join(chunks),st
    finally: os.close(fd)

def _inflate_bounded(compressed: bytes) -> bytes:
    inflater=zlib.decompressobj(); ceiling=MAX_GIT_BLOB_BYTES+128
    try:
        framed=inflater.decompress(compressed,ceiling+1)
        if len(framed)>ceiling or inflater.unconsumed_tail: raise GitStageUnsupportedRepositoryError("existing loose object expands beyond governed ceiling")
        tail=inflater.flush(ceiling+1-len(framed)); framed+=tail
    except zlib.error as exc: raise GitStageUnsupportedRepositoryError("existing loose object has invalid zlib framing") from exc
    if len(framed)>ceiling or not inflater.eof or inflater.unused_data: raise GitStageUnsupportedRepositoryError("existing loose object has invalid or trailing zlib framing")
    return framed

def verify_existing_loose_blob(workspace_root: str | Path, preparation: GitLooseObjectPreparation) -> ExistingLooseObjectProof | None:
    store=inspect_local_object_store(workspace_root)
    if store!=preparation.store: raise GitStageUnavailableError("Git object-store identity changed after preparation")
    path=Path(workspace_root).resolve(strict=True)/".git"/preparation.relative_object_path
    try: compressed,st=_read_existing_regular_nofollow(path)
    except FileNotFoundError: return None
    framed=_inflate_bounded(compressed); nul=framed.find(b"\x00")
    if nul<=0: raise GitStageUnsupportedRepositoryError("existing loose object has invalid Git framing")
    header,content=framed[:nul],framed[nul+1:]; parts=header.split(b" ",1)
    if len(parts)!=2 or parts[0]!=b"blob" or not parts[1].isdigit(): raise GitStageUnsupportedRepositoryError("existing object is not a canonical blob")
    if int(parts[1])!=len(content): raise GitStageUnsupportedRepositoryError("existing blob length framing is invalid")
    oid=hashlib.sha1(framed).hexdigest(); content_sha=hashlib.sha256(content).hexdigest()
    if oid!=preparation.candidate.oid or content_sha!=preparation.candidate.content_sha256 or len(content)!=preparation.candidate.content_bytes: raise GitStageUnsupportedRepositoryError("existing loose object conflicts with approved blob identity")
    return ExistingLooseObjectProof(oid,f"posix:{int(st.st_dev)}:{int(st.st_ino)}:{int(st.st_mode)}",hashlib.sha256(compressed).hexdigest(),len(compressed),content_sha,len(content))

class PreAuthorityLooseObjectTransaction:
    mutation_authority_enabled=False
    def __init__(self,workspace_root:str|Path)->None:self.workspace_root=Path(workspace_root)
    def prepare(self,content:bytes)->tuple[GitLooseObjectPreparation,bytes]:return prepare_loose_blob(self.workspace_root,content)
    def inspect_existing(self,preparation:GitLooseObjectPreparation)->ExistingLooseObjectProof|None:return verify_existing_loose_blob(self.workspace_root,preparation)
    def publish(self,preparation:GitLooseObjectPreparation,compressed:bytes)->None:
        del preparation,compressed; raise GitStageUnavailableError("loose-object publication authority is unavailable")
    def close(self)->None:return None

__all__=["LOOSE_OBJECT_TRANSACTION_CONTRACT","MAX_LOOSE_OBJECT_COMPRESSED_BYTES","GitLooseObjectPreparation","ExistingLooseObjectProof","PreAuthorityLooseObjectTransaction","prepare_loose_blob","verify_existing_loose_blob"]