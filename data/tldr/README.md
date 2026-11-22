# Pinned tldr reference source

This is the English common/Linux subset at upstream revision
`eacda7020c4102729187c38c35ce28fac00365c9`. All 6,837 pages (4,050,595 original
bytes) retain their upstream paths, text and placeholders in pages.jsonl.
LICENSE.md and NOTICE.md retain the upstream license and attribution; the page
data is CC BY 4.0, independently of nl-shell's code license.

From the repository root, consume the verified snapshot offline:

```sh
python3 scripts/tldr_snapshot.py export > tldr-export.jsonl
```

An optional `--root data/tldr` selects a snapshot directory. Validation completes
before any output. Each JSONL record contains `path`, `content`, the pinned
`revision`, `language: "en"` and `provenance: "local-reference"`. Ordering follows
full upstream paths. Only local files and Python's standard library are used.
Commands inside page text remain data; never execute them as part of conversion.

This source is input to the future install-time harvest (#23), not an index or
installer change. That harvest must select against the active target; this subset
does not promise that every example works on Ubuntu 26.04. Private history is
excluded from generic training (ADR-0010). Dataset/weights licensing remains #34.

## Rebuild

Acquisition is an explicit build-time network operation. In a working directory
containing this repository's data/tldr/, clone upstream into `tldr-upstream`:

```sh
git clone --no-checkout https://github.com/tldr-pages/tldr.git tldr-upstream
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess

revision = "eacda7020c4102729187c38c35ce28fac00365c9"
source = Path("tldr-upstream")
out = Path("data/tldr")

def git(*args):
    return subprocess.check_output(["git", "-C", str(source), *args])

def blob(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()

entries = git("ls-tree", "-r", revision, "pages/common/", "pages/linux/").decode("utf-8").split("\n")
pages = []
manifest = []
inventory = bytearray()
for entry in sorted(e for e in entries if e):
    identity, path = entry.split("\t", 1)
    mode, kind, sha = identity.split()
    assert mode == "100644" and kind == "blob" and path.endswith(".md")
    content = git("cat-file", "blob", sha)
    assert blob(content) == sha
    pages.append({"path": path, "content": content.decode("utf-8")})
    manifest.append({"path": path, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(), "blob_sha1": sha})
    inventory.extend(f"{path}\000100644\0{sha}\n".encode("utf-8"))
# Sort by full path, rather than the ls-tree mode/identity prefix.
pages.sort(key=lambda p: p["path"])
manifest.sort(key=lambda p: p["path"])
inventory = "".join(f'{p["path"]}\000100644\0{p["blob_sha1"]}\n' for p in manifest).encode("utf-8")
anchor = hashlib.sha256(inventory).hexdigest()
assert anchor == "4ce7ecdff5a4da72bfef4378f027ad141b7daa28dc6b0a68f57905a6e080d960"
assert len(pages) == 6837 and sum(p["bytes"] for p in manifest) == 4050595
corpus = "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in pages).encode("utf-8")
license_bytes = git("show", f"{revision}:LICENSE.md")
assert blob(license_bytes) == "9b4ebcb9a886af3506c5d42f1dcf1253a520efbe"
metadata = {"repository": "https://github.com/tldr-pages/tldr", "revision": revision,
            "prefixes": ["pages/common/", "pages/linux/"], "language": "en",
            "transformation": "Original UTF-8 page bytes repackaged as path/content JSONL, sorted by upstream path; no text changes.",
            "corpus_sha256": hashlib.sha256(corpus).hexdigest(), "inventory_sha256": anchor, "pages": manifest}
out.mkdir(parents=True, exist_ok=True)
(out / "pages.jsonl").write_bytes(corpus)
(out / "LICENSE.md").write_bytes(license_bytes)
(out / "source.json").write_bytes((json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
PY
```

The recipe reads Git tree modes (100644), not archive permission bits: stock
`git archive` may use 0664. It never executes upstream code. The independent
inventory SHA-256 is
`4ce7ecdff5a4da72bfef4378f027ad141b7daa28dc6b0a68f57905a6e080d960`.
The inventory hashes sorted `path + NUL + 100644 + NUL + Git-blob-SHA1 + LF`
records; source.json also records per-page SHA-256/byte counts and corpus SHA-256.

A future refresh must update the revision, inventory, count, byte-total and license
anchors in scripts/tldr_snapshot.py and tests/test_tldr_snapshot.py as well as
regenerating the data and revising attribution. This utility deliberately has no
network refresh command. Verify with `python3 -m pytest -q tests/test_tldr_snapshot.py`.
