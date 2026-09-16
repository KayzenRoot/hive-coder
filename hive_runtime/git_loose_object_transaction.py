from __future__ import annotations

"""Pre-authority loose Git object preparation and exact existing-object proof."""

import hashlib
import os
import stat
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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
    """Crash-safe, content-addressed, no-clobber publication of one loose blob.

    This is the only place the capability writes into `.git/objects`. The final
    canonical OID pathname is never opened for writing: the complete compressed
    object is materialized and digest-verified in Hive-owned private storage
    outside the object store, then promoted atomically with a no-clobber
    primitive. A crash before promotion therefore leaves the canonical pathname
    absent, and a canonical pathname never contains partial bytes.

    An existing object is never overwritten and never deleted: it is accepted
    only after proving it is the exact approved blob.

    A published object keeps the private temporary's owner-only creation mode
    (0600). That is deliberately more restrictive than Git's conventional 0444
    and is never a disclosure risk, whereas 0444 would make the capability's own
    temporary impossible to unlink on Windows, where a read-only file cannot be
    deleted. The mode is not part of any approval binding.
    """

    mutation_authority_enabled = True

    def __init__(self, workspace_root: str | Path, *, preparer=None) -> None:
        from .git_object_private_prep import PrivateObjectPreparer

        self.workspace_root = Path(workspace_root)
        self._preparer = preparer if preparer is not None else PrivateObjectPreparer(self.workspace_root)

    def publish(
        self,
        preparation: GitLooseObjectPreparation,
        compressed: bytes,
        *,
        pre_publish_check: Callable[[], None] | None = None,
    ) -> str:
        """Publish one blob, invoking ``pre_publish_check`` at the final-link boundary.

        ``pre_publish_check`` is a Hive-owned authority check supplied by the
        caller. It runs after every preparation and revalidation step and
        immediately before the atomic promotion, so a cancellation, takeover,
        expiry or emergency transition occurring during preparation cannot let a
        canonical object appear. A failure there leaves the canonical pathname
        absent, produces no success receipt, and lets the private temporary follow
        the normal identity-safe cleanup. It is an authority check, never a bypass
        and never a test-only hook.
        """
        digest = hashlib.sha256(compressed).hexdigest()
        if digest != preparation.compressed_sha256 or len(compressed) != preparation.compressed_bytes:
            raise GitStageUnavailableError("compressed object no longer matches the approved preparation")
        store = inspect_local_object_store(self.workspace_root)
        if store != preparation.store:
            raise GitStageUnavailableError("Git object-store identity changed before publication")
        if store.object_format != "sha1":
            raise GitStageUnsupportedRepositoryError("only the SHA-1 object format is supported")

        objects_dir = Path(self.workspace_root).resolve(strict=True) / ".git" / "objects"
        final_path = objects_dir / preparation.fanout / preparation.leaf

        # Fast path: an already-correct object needs no temp, no promotion and no
        # new mutation, so no authority check is consumed here; the caller's own
        # external checks already protect that flow.
        if self._prove_existing_loose_blob(preparation) is not None:
            return PUBLISHED_ALREADY_PRESENT

        # 1) Materialize the COMPLETE compressed object in private repo-local
        #    storage. Nothing canonical is visible while this happens.
        from .git_object_private_prep import plan_private_object

        plan = plan_private_object(preparation, compressed)
        temp = self._preparer.materialize_private_temp(plan, compressed)
        temp_path = Path(temp.identity.path)
        try:
            # 2) Re-prove the store and the private temp immediately before promotion.
            if inspect_local_object_store(self.workspace_root) != preparation.store:
                raise GitStageUnavailableError("Git object-store identity changed during publication")
            live = temp_path.lstat()
            if not temp.identity.matches(live):
                raise GitStageUnavailableError("private object temporary identity changed before promotion")
            on_disk = temp_path.read_bytes()
            if hashlib.sha256(on_disk).hexdigest() != preparation.compressed_sha256:
                raise GitStageUnavailableError("private object temporary digest changed before promotion")
            if len(on_disk) != preparation.compressed_bytes:
                raise GitStageUnavailableError("private object temporary length changed before promotion")

            _ensure_fanout_directory(objects_dir, preparation.fanout)

            # 3) Final authority check at the real publication boundary, after all
            #    preparation and revalidation and immediately before the promotion.
            #    A failure here must not produce a canonical object.
            if pre_publish_check is not None:
                pre_publish_check()

            # 3) Promote atomically as create-if-absent. os.link is no-clobber on
            #    POSIX and on Windows/NTFS, and never overwrites an existing object.
            try:
                os.link(temp_path, final_path)
                created = True
            except FileExistsError:
                created = False
            except (OSError, NotImplementedError, AttributeError) as exc:
                raise GitStageUnsupportedRepositoryError(
                    "the filesystem does not support no-clobber object promotion"
                ) from exc

            if not created:
                # Another publisher won the race. Accept only an exact proof.
                if self._prove_existing_loose_blob(preparation) is None:
                    raise GitStageUnsupportedRepositoryError("object path appeared but is not the approved blob")
                return PUBLISHED_ALREADY_PRESENT

            # 4) Prove the promoted object is the exact approved blob.
            if self._prove_existing_loose_blob(preparation) is None:
                raise GitStageUnsupportedRepositoryError("published blob did not prove its own identity")
            return PUBLISHED_CREATED
        finally:
            # 5) Remove only our own private temp, identity-checked. A failure here
            #    leaves an inert temporary in the Hive-owned directory.
            try:
                self._preparer.cleanup_private_temp(temp)
            except Exception:
                pass

    def _prove_existing_loose_blob(self, preparation: GitLooseObjectPreparation) -> ExistingLooseObjectProof | None:
        return verify_existing_loose_blob(self.workspace_root, preparation)


__all__=["LOOSE_OBJECT_TRANSACTION_CONTRACT","MAX_LOOSE_OBJECT_COMPRESSED_BYTES","PUBLISHED_ALREADY_PRESENT","PUBLISHED_CREATED","LooseObjectPublisher","GitLooseObjectPreparation","ExistingLooseObjectProof","PreAuthorityLooseObjectTransaction","prepare_loose_blob","verify_existing_loose_blob"]