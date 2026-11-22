---
created: 14.10.2026 19:22
type: architecture
status: living
tags:
  - architecture
  - deployment
---
# 7. Deployment view

> Living document.

## 7.1 The user's machine (the deliverable)

The intended deliverable below includes planned installer and packaging work, not
an assertion that these already ship.

- The REPL and an install script, with GGUF weights downloaded separately. No teacher,
  no training pipeline, no PyTorch.
- **Target packaging (planned, #48, #50):** The package contains every target's runtime
  files: `target.toml`, `model.toml`, `allowlist.toml`, `sensitive.toml`,
  `gate-vectors.toml` and `prompts/`. Build-time `harvest.toml` and `eval/` are not shipped.
- **Model integrity (planned):** Weights are not stored in git or the package;
  `model.toml` records each file's URL, size, SHA-256, base model/license, training run
  (pipeline commit and dataset hash), and quantization where offered. The installer
  downloads at install or explicit update into `$XDG_DATA_HOME/nl-shell/models/`,
  verifying SHA-256 against `model.toml` before use. The REPL must refuse to load
  weights on a hash mismatch with the active target's manifest. Downloads happen only at install or explicit update,
  never at runtime; offline operation is preserved. These checks are requirements
  awaiting implementation.
- **Personalization adapters (planned):** Stored per target and base-weight hash;
  the REPL must not load an adapter on different weights. Compatibility enforcement
  remains awaiting implementation.
- For `ubuntu-26.04`, one `llama-server` per user, run as the systemd user service `nl-shell-model.service` on
  a Unix socket, serving both the command model and the reader (ADR-0018).
- llama.cpp backend picked at install time (ADR-0019): CUDA on NVIDIA; Vulkan (Mesa RADV)
  by default on AMD, ROCm opt-in; CPU as the last resort.
- Local reference index harvested at install time from package-owned man pages (the target's package-owner query; `dpkg -S` on `ubuntu-26.04`) and an
  allowlist of `--help` outputs, without running arbitrary binaries (#23, #49).
- Files under the XDG base directories (ADR-0020): config and prompts in
  `~/.config/nl-shell/`, weights and the reference index in `~/.local/share/nl-shell/`,
  session logs in `~/.local/state/nl-shell/` (private to the user).

VRAM budget on a 16 GB card:

| Component | Target |
|---|---|
| Command model (1.5–3B, Q4_K_M–Q8) | 2–4 GB incl. KV cache |
| Quarantined reader | Same base weights + a runtime LoRA adapter, or the same weights with another prompt |
| Intent classifier | Tiny; runs on CPU |
| **Total** | **≤ 6 GB**; also runs CPU-only (slow but functional) |

## 7.2 Test matrix

| Vendor | Cards (16 GB) | Backend |
|---|---|---|
| NVIDIA | RTX 4060 Ti 16 GB, RTX 5060 Ti 16 GB, RTX 5070 Ti, RTX 5080 | CUDA |
| AMD | RX 7800 XT, RX 9060 XT 16 GB, RX 9070 / 9070 XT | ROCm, Vulkan fallback |
| Any | — | CPU-only smoke test |

## 7.3 Development hardware (build time only)

| Role | Machine | Notes |
|---|---|---|
| Teacher (data generation, dev fallback) | Framework Desktop, Ryzen AI Max+ 395, 128 GB unified | llama.cpp / vLLM, OpenAI-compatible endpoint on the LAN |
| Student training + inference | Desktop, NVIDIA 16 GB | Unsloth QLoRA |
| Reference system per target | VM for that target (initially Ubuntu 26.04) | Source of truth; harvest and execution sandbox with snapshots |

**[OPEN]** Weight URL host in `model.toml` (M5.4).

**[OPEN]** Package distribution channel (M5.4). The manifest decision resolves neither
this channel nor the weights' host.
