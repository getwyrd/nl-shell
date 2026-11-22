"""Verify and export the pinned, local tldr source; no runtime imports required."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

REVISION = "eacda7020c4102729187c38c35ce28fac00365c9"
INVENTORY = "4ce7ecdff5a4da72bfef4378f027ad141b7daa28dc6b0a68f57905a6e080d960"
LICENSE_BLOB = "9b4ebcb9a886af3506c5d42f1dcf1253a520efbe"
REPOSITORY = "https://github.com/tldr-pages/tldr"
PREFIXES = ["pages/common/", "pages/linux/"]


def blob(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def verified_pages(root):
    metadata = json.loads((root / "source.json").read_text(encoding="utf-8"))
    if (metadata["repository"], metadata["revision"], metadata["prefixes"], metadata["language"]) != (
        REPOSITORY, REVISION, PREFIXES, "en"
    ):
        raise ValueError("source identity mismatch")
    if blob((root / "LICENSE.md").read_bytes()) != LICENSE_BLOB:
        raise ValueError("license mismatch")
    corpus = (root / "pages.jsonl").read_bytes()
    if hashlib.sha256(corpus).hexdigest() != metadata["corpus_sha256"]:
        raise ValueError("corpus digest mismatch")
    # Split only JSONL's LF delimiter, never Unicode separators inside strings.
    records = [json.loads(line) for line in corpus.decode("utf-8").split("\n") if line]
    manifest = []
    inventory = bytearray()
    total = 0
    previous = ""
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "content"} or any(type(v) is not str for v in record.values()):
            raise ValueError("invalid record schema")
        path = record["path"]
        if path <= previous or not any(path.startswith(p) for p in PREFIXES) or not path.endswith(".md"):
            raise ValueError("invalid, duplicate or unordered path")
        if len(Path(path).parts) != 3:
            raise ValueError("invalid page path")
        previous = path
        content = record["content"].encode("utf-8")
        identity = blob(content)
        manifest.append({"path": path, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(), "blob_sha1": identity})
        inventory.extend(f"{path}\000100644\0{identity}\n".encode("utf-8"))
        total += len(content)
    if manifest != metadata["pages"]:
        raise ValueError("page manifest mismatch")
    digest = hashlib.sha256(inventory).hexdigest()
    if len(records) != 6837 or total != 4050595 or digest != INVENTORY or metadata["inventory_sha256"] != INVENTORY:
        raise ValueError("pinned inventory mismatch")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["export"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1] / "data/tldr")
    args = parser.parse_args()
    try:
        records = verified_pages(args.root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"invalid tldr snapshot: {error}\n")
    for record in records:
        exported = {"path": record["path"], "content": record["content"], "revision": REVISION,
                    "language": "en", "provenance": "local-reference"}
        sys.stdout.buffer.write((json.dumps(exported, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
