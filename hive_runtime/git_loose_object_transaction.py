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
    flags=os.O_RDONLY|getattr(os,"O_BINARY",0)|getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_NONBLOCK",0)
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


PUBLISHED_CREATED = "created"
PUBLISHED_ALREADY_PRESENT = "already_present"


def _lstat_real_directory(path: Path, label: str) -> os.stat_result:
    try: st = path.lstat()
    except OSError as exc: raise GitStageUnsupportedRepositoryError(f"{label} is unprovable") from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise GitStageUnsupportedRepositoryError(f"{label} is not a real directory")
    return st


def _ensure_fanout_directory(objects_dir: Path, fanout: str) -> Path:
    """Create the 2-hex fanout directory if absent, proving it is a real directory.

    Fails closed on symlink/reparse/non-directory collisions rather than writing
    through them.
    """
    if len(fanout) != 2 or any(ch not in "0123456789abcdef" for ch in fanout):
        raise GitStageUnsupportedRepositoryError("object fanout path is not canonical")
    directory = objects_dir / fanout
    try:
        os.mkdir(directory, 0o755)
    except FileExistsError:
        pass
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError("cannot create the object fanout directory") from exc
    _lstat_real_directory(directory, "object fanout directory")
    return directory


class LooseObjectPublisher:
    """Content-addressed, no-clobber publication of one governed loose blob.

    This is the only place the capability writes into `.git/objects`. It never
    overwrites an existing object and never deletes one: an object already at the
    final path is accepted only after proving it is the exact approved blob.
    """

    mutation_authority_enabled = True

    def __init__(self, workspace_root: str | Path) -> None:
        self.workspace_root = Path(workspace_root)

    def publish(self, preparation: GitLooseObjectPreparation, compressed: bytes) -> str:
        digest = hashlib.sha256(compressed).hexdigest()
        if digest != preparation.compressed_sha256 or len(compressed) != preparation.compressed_bytes:
            raise GitStageUnavailableError("compressed object no longer matches the approved preparation")
        store = inspect_local_object_store(self.workspace_root)
        if store != preparation.store:
            raise GitStageUnavailableError("Git object-store identity changed before publication")
        if store.object_format != "sha1":
            raise GitStageUnsupportedRepositoryError("only the SHA-1 object format is supported")

        objects_dir = Path(self.workspace_root).resolve(strict=True) / ".git" / "objects"
        path = objects_dir / preparation.fanout / preparation.leaf

        existing = self._prove_existing_loose_blob(preparation)
        if existing is not None:
            return PUBLISHED_ALREADY_PRESENT

        _ensure_fanout_directory(objects_dir, preparation.fanout)

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags, 0o444)
        except FileExistsError:
            # A concurrent publisher won the race. Accept only an exact identity proof.
            if self._prove_existing_loose_blob(preparation) is None:
                raise GitStageUnsupportedRepositoryError("object path appeared but is not the approved blob")
            return PUBLISHED_ALREADY_PRESENT
        except OSError as exc:
            raise GitStageUnsupportedRepositoryError("cannot create the content-addressed object") from exc
        try:
            view = memoryview(compressed)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise GitStageUnsupportedRepositoryError("short write while publishing a blob object")
                view = view[written:]
            os.fsync(fd)
        except BaseException:
            os.close(fd)
            # The path was created exclusively by us microseconds ago. Removing it
            # can only discard our own partial object, never a foreign one.
            try: os.unlink(path)
            except OSError: pass
            raise
        else:
            os.close(fd)

        if self._prove_existing_loose_blob(preparation) is None:
            raise GitStageUnsupportedRepositoryError("published blob did not prove its own identity")
        return PUBLISHED_CREATED

    def _prove_existing_loose_blob(self, preparation: GitLooseObjectPreparation) -> ExistingLooseObjectProof | None:
        return verify_existing_loose_blob(self.workspace_root, preparation)


__all__=["LOOSE_OBJECT_TRANSACTION_CONTRACT","MAX_LOOSE_OBJECT_COMPRESSED_BYTES","PUBLISHED_ALREADY_PRESENT","PUBLISHED_CREATED","LooseObjectPublisher","GitLooseObjectPreparation","ExistingLooseObjectProof","PreAuthorityLooseObjectTransaction","prepare_loose_blob","verify_existing_loose_blob"]