---
name: nix
description: How to get things done with Nix — look up packages/options, write and debug a flake, package an app, build a devshell. Use when building or packaging with Nix, writing or editing flake.nix / a derivation / a devShell, looking up a NixOS or home-manager option or a package name/version, pinning nixpkgs, or when a `nix build` / `nix develop` / `nix flake check` fails.
---

# Nix

This is a **process** skill. Nix is too large to memorise and its API surface moves; what
transfers is the loop — *look it up, evaluate it, build it, read the log, iterate* — and knowing
which lookup gets a trustworthy answer in one shot. Never write a derivation from memory of what
an attribute is called. Check it.

Two rules that prevent most wasted turns:

1. **Evaluation is cheap, building is expensive.** Push every mistake you can into `nix eval` /
   `nix flake check`, which take seconds, before you spend twenty minutes in `nix build`.
2. **The build sandbox has no network.** Anything fetched must be a fixed-output derivation with
   a hash you supply up front. If a build dies reaching the internet, the fix is never "let it
   reach the internet" — it is "declare the dependency."

## 1. The lookup ladder

Climb it in order. Stop at the first rung that answers the question.

**Rung 1 — the `nixos` MCP tools.** Fastest for "does a package/option exist and what is it
called". `mcp__nixos__nix` takes `action` (`search`|`info`|`stats`|`options`|`channels`) with
`type` (`packages`|`options`|`programs`) and `source` (`nixos`|`home-manager`|`darwin`|`flakes`|
`wiki`|`nix-dev`|`noogle`|`nixhub`). Options search is the strongest use — one call gets you the
option's type and description:

```
mcp__nixos__nix  action=search  type=options  query="services.openssh"
```

`mcp__nixos__nix_versions package=nodejs` is the tool with no CLI equivalent: it returns the
version history from NixHub **with the nixpkgs commit for each version**, which is exactly what
you need to pin an old version of something.

Its limits are real and you will hit them (all observed, not theoretical):
- Package *search* is fuzzy and ranks badly — `query="cargo-tauri"` returned five unrelated
  packages and not `cargo-tauri`.
- Package *info* is an index lookup that can miss packages that exist — `info cargo-tauri`
  answered `NOT_FOUND` while `nix eval nixpkgs#cargo-tauri.version` on the same machine answered
  `2.11.0`.
- The `home-manager` source returned nothing for any query tried. Do not trust its silence.

So: **a hit is useful, a miss proves nothing.** On a miss, drop to rung 2.

**Rung 2 — evaluate against your actual nixpkgs.** This is the authoritative answer, because it
asks the tree you will really build against:

```bash
nix eval nixpkgs#cargo-tauri.version           # exists? what version?
nix eval --json nixpkgs#hello.meta.license
nix eval .#default.drvPath                     # your own flake output
```

Avoid `nix search nixpkgs <term>` unless you must — it evaluates the whole package set and
crawls (it prints thousands of `evaluating 'legacyPackages.x86_64-linux.…'` lines first).
[search.nixos.org](https://search.nixos.org/packages) is the same index, instant, in a browser.

**Rung 3 — read the source.** Once you know the attribute name, the definition is the real
documentation, and it is on your disk:

```bash
nix edit nixpkgs#cargo-tauri        # opens the package.nix in $EDITOR
nix eval --raw nixpkgs#cargo-tauri.hook   # store path of a setup hook — then `cat` its files
```

Setup hooks are shell scripts in `<store-path>/nix-support/`. Reading one tells you precisely
which phases it overrides and which variables it honours — far better than guessing. See §5 for
what reading `cargo-tauri.hook` this way revealed.

**Rung 4 — prose docs**, when you need the concept rather than the name:
[nix.dev](https://nix.dev/) for tutorials, the
[Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/) for language ecosystems
(`#rust`, `#javascript`), the [Nix manual](https://nix.dev/manual/nix/latest/) for CLI, and the
[NixOS Wiki](https://wiki.nixos.org/) for platform gotchas (its
[Tauri page](https://wiki.nixos.org/wiki/Tauri) is the source of the `XDG_DATA_DIRS` shellHook in
the example project below).

**Introspecting interactively.** When you need to poke at more than one attribute, `nix repl`
beats a run of `nix eval` calls:

```
nix repl nixpkgs
nix-repl> cargo-tauri.version
nix-repl> lib.attrNames rustPlatform
nix-repl> :b hello            # build an expression from the repl
```

`nix repl .` loads your own flake; `outputs.packages.x86_64-linux.default` is then reachable and
tab-completable, which is the quickest way to find out why an override did not take.

## 2. The iterate loop

```
edit  →  nix flake check   (seconds; catches eval errors)
      →  nix build .#x -L  (minutes; read the log)
      →  inspect result/
```

**Always pass `-L`.** Without it Nix hides the build log behind a progress bar and shows you only
the last 25 lines on failure — which for a big compile is almost always noise from a *parallel*
crate rather than the real cause.

Reach for these when `-L` is not enough:

| Need | Command |
|---|---|
| Re-read the log of a build that already ran | `nix log /nix/store/….drv` |
| Keep the build tree around to inspect | `nix build -L --keep-failed` (aka `-K`) — leaves `/tmp/nix-build-*` |
| Reproduce the build env by hand | `nix develop .#default` then run the phases (`unpackPhase`, `buildPhase`, …) |
| Enter the env of an arbitrary derivation | `nix develop nixpkgs#hello` |
| Where did this output path come from | `nix path-info --derivation /nix/store/…` |
| Compare two derivations (why did it rebuild?) | `nix derivation show <drvA> <drvB>` and diff the `env` blocks |
| Closure size | `nix path-info -Sh .#default` |
| Prove it is not a cache artefact | `nix build --rebuild` |

The `nix derivation show` diff is the underused one. When a rebuild surprises you, dumping both
`.drv` files as JSON and diffing their `env` maps names the exact attribute that changed — no
guessing.

**Do not pipe `nix build` to `tail`.** Shell pipelines report the *last* command's status, so a
failed build reads as `EXIT=0`. Redirect instead (`nix build … &> build.log`) and read the file.
This bit during the verification for this skill; see §6.

## 3. Sandbox and hashes

Builds run with no network. The only way in is a **fixed-output derivation** — one that declares
the hash of what it will fetch, so Nix can verify it. Every dependency fetcher is one.

The consequence in practice: language package managers must run in a separate, hash-pinned fetch
step, and the build step runs `--offline`. When a build fails with a DNS or registry error, you
have a missing or stale dependency hash, not a networking problem.

**Getting a hash: lie, then copy.** Put a deliberately wrong hash in, build, and read the correct
one out of the error. `lib.fakeHash` exists for exactly this — the
[Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/#sec-source-hash-update) calls it the
"fake hash method":

```nix
cargoHash = lib.fakeHash;   # or npmDepsHash = lib.fakeHash;
```

```
error: hash mismatch in fixed-output derivation '…':
         specified: sha256-AAAA…
            got:    sha256-tJ8W…
```

Paste the `got:` value back. Repeat after any dependency change — the hash covers the whole
resolved dependency set, so *any* lockfile edit invalidates it.

**Better: avoid the hash entirely.** Both major ecosystems have a lockfile-driven mode that
derives everything from the lockfile already in your repo, so there is no hash to drift:

- Rust — `cargoLock.lockFile = ../src-tauri/Cargo.lock;` instead of `cargoHash`.
- Node — `importNpmLock` instead of `npmDepsHash`:

```nix
npmDeps = importNpmLock {
  package     = lib.importJSON ../package.json;
  packageLock = lib.importJSON ../package-lock.json;
};
# and use its matching hook, not buildNpmPackage's:
nativeBuildInputs = [ importNpmLock.npmConfigHook ];
```

Prefer these. A hash you never have to update is a hash that is never wrong.

**Impurity escape hatches**, in increasing order of how much they should worry you:
`--impure` (allows reading mutable paths — fine for a quick `nix eval --impure --expr`),
`__noChroot = true` (disables the sandbox for one derivation; needs `sandbox = relaxed` in
`nix.conf` and makes the build non-reproducible). If you find yourself wanting the second one,
the derivation is wrong.

## 4. Flake shape

A flake is `inputs` (pinned in `flake.lock`) plus `outputs`. The outputs an agent writes are
almost always these four, and the multi-system boilerplate is the `genAttrs` helper:

```nix
{
  # Pin to a commit, not a branch, when the closure must match a specific host.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/95ca1e203c0750115fd4a6f17d5a245dfe6b1edd";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (s: f nixpkgs.legacyPackages.${s});
    in {
      packages   = forAllSystems (pkgs: rec {
        my-app  = pkgs.callPackage ./nix/package.nix { };
        default = my-app;
      });
      devShells  = forAllSystems (pkgs: { default = pkgs.mkShell { /* … */ }; });
      overlays.default = final: _prev: { my-app = final.callPackage ./nix/package.nix { }; };
      homeManagerModules.default = import ./nix/hm-module.nix self;
    };
}
```

Things that catch people out:

- **Untracked files are invisible.** A flake in a git repo sees only what git tracks. A new
  `nix/package.nix` you have not `git add`ed produces "file not found" — `git add -N` is enough.
- `nix flake update` bumps every input; `nix flake update <input>` bumps one. Commit the
  resulting `flake.lock`.
- **Keep the derivation out of `flake.nix`.** Put it in `nix/package.nix` taking its dependencies
  as function arguments, and wire it up with `callPackage`. That one file then works unchanged
  from the flake, from an overlay, and from plain `nix-build`.
- **Scope `src` with `lib.fileset`.** The default is the whole directory, so a touched
  `node_modules` or `target/` changes the input hash and forces a full rebuild:

```nix
src = lib.fileset.toSource {
  root = ../.;
  fileset = lib.fileset.unions [ ../package.json ../src ../src-tauri/src /* … */ ];
};
```

**devShells.** `pkgs.mkShell` distinguishes `packages` (tools on `PATH`), `nativeBuildInputs`
(build-time tools whose setup hooks should run, e.g. `pkg-config`, `wrapGAppsHook4`) and
`buildInputs` (libraries to link against). Put `env.FOO = …` for environment variables and
`shellHook` for anything that must run at shell entry. Mirror it against whatever your project's
non-Nix path is (devbox, direnv) so the two toolchains cannot drift.

## 5. Packaging walkthrough

For a full worked example — packaging a Tauri v2 desktop app (`importNpmLock` frontend +
`rustPlatform.buildRustPackage` with `cargo-tauri.hook`), the `custom-protocol` / `devUrl` trap
that silently ships a broken app, desktop-file and URL-scheme-handler registration, and the
home-manager module that installs it — read **[TAURI.md](TAURI.md)**.

The transferable shape of that example, which applies to packaging most GUI or multi-language
apps:

1. Find out whether nixpkgs already has a **setup hook** for your build tool (`nix eval --raw
   nixpkgs#<tool>.hook`, then read the scripts in its `nix-support/`). Using the ecosystem's real
   CLI via its hook beats hand-rolling `buildPhase`, because the CLI sets feature flags and
   environment the raw compiler invocation does not.
2. Feed each language's dependencies in through its lockfile importer.
3. Let `wrapGAppsHook4` handle GTK/webkit wrapping — it produces a `bin/.foo-wrapped` binary plus
   a `bin/foo` wrapper script; scripts that inspect "the binary" must look for both.
4. Add a **`doInstallCheck` that asserts the property you actually care about**, so a silent
   misbuild fails the build instead of shipping.

## 6. Lessons learned

Recorded from real runs; each is a thing that cost time.

- **A pipeline hides build failure.** `nix build … 2>&1 | tail -60` reported `EXIT=0` for a build
  that had failed, because `$?` is `tail`'s status. Redirect to a file, or check
  `${PIPESTATUS[0]}`.
- **A stale `result` symlink looks like success.** After the failure above, `result/` still
  existed and still contained a working binary — from an *earlier* build. `readlink -f result`
  gave `/nix/store/l7g4…`, while the derivation just attempted was `…-out /nix/store/9wm4…`.
  Always compare `readlink -f result` against `nix path-info --derivation .#default` before
  claiming a build passed.
- **`ls -l result/bin/` hides the real binary.** `wrapGAppsHook4` names it `.foo-wrapped`, a
  dotfile. The visible `foo` was 16 KB (the wrapper); the real one was 13 MB. Use `ls -la`.
- **Disk exhaustion masquerades as a compiler bug.** A Tauri release build failed with
  `could not compile 'glib' … (signal: 11, SIGSEGV)` and `rustc-LLVM ERROR: IO failure on output
  stream`. The actual cause was on the last line: `No space left on device`. Nix prints
  `note: build failure may have been caused by lack of free disk space` — read it. Check `df -h
  /nix` *first*; a Rust GUI closure here was 1.2 GiB and the build tree many times that.
- **Only the last 25 log lines are shown by default, and they lie.** With a parallel cargo build,
  those lines belong to whichever crate happened to fail last. Use `-L`, or `nix log <drv>`.
- **`nix eval` disagreeing with the MCP index means the MCP index is wrong.** `cargo-tauri` was
  `NOT_FOUND` via `mcp__nixos__nix info` and `2.11.0` via `nix eval`. The local evaluation wins.
- **Verify the property, not a proxy for it.** For the Tauri app, "is `localhost:1420` in the
  binary?" is *not* a test for the misbuild — the dev URL is embedded in the serialised config in
  both the good and the bad binary (confirmed with `grep -a` on a known-good build). Only
  "are `/assets/index-*` strings present?" distinguishes them. Before writing an install check,
  confirm your predicate actually differs between pass and fail.
- **A dirty git tree warns but still builds.** `warning: Git tree '…' is dirty` is informational;
  uncommitted (but tracked) changes are included. Untracked ones are not — see §4.
