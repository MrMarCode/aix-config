# Packaging a Tauri v2 app with Nix

A worked example, ground truth taken from `link-router` (Tauri v2, React frontend, Rust backend,
`flake.nix` + `nix/package.nix` + `nix/hm-module.nix`). Read the main
[SKILL.md](SKILL.md) first — this file assumes the lookup ladder and the iterate loop.

A Tauri app is two builds glued together: a JS frontend bundled by Vite, and a Rust binary that
**embeds** that bundle. Both must be fed dependencies offline, and the glue is where the traps
are.

## The trap, first, because it is silent

Tauri's own `build.rs` derives the `dev` compile-time cfg from a *cargo feature*
(`tauri-2.11.5/build.rs`, lines 256-262 of the vendored crate):

```rust
let custom_protocol = has_feature("custom-protocol");
let dev = !custom_protocol;
alias("custom_protocol", custom_protocol);
alias("dev", dev);
println!("cargo:dev={dev}");
```

`tauri-build` then reads that back through the cargo links mechanism —
`is_dev()` is `env::var_os("DEP_TAURI_DEV") == "true"` (`tauri-build-2.6.3/src/lib.rs:426`).
`generate_context!` branches on it: in "dev" it bakes **`build.devUrl`** (`http://localhost:1420`)
into the binary; otherwise it embeds `frontendDist`.

Nothing turns `custom-protocol` on except the Tauri CLI. So a derivation that runs **plain
`cargo build`** produces a binary that compiles, links, installs, passes `ldd`, launches — and
shows *"could not connect to localhost"*, because the frontend was never embedded. Worse, it
looks fine on the developer's machine if a stray `npm run tauri dev` is serving port 1420.

**The fix is to build through the Tauri CLI**, which nixpkgs packages as a setup hook.

## `cargo-tauri.hook`: read it before you use it

```bash
nix eval --raw nixpkgs#cargo-tauri.hook      # → /nix/store/…-tauri-hook
cat /nix/store/…-tauri-hook/nix-support/*
```

What that script actually does (verified by reading it — do this rather than guessing):

- Sets `dontCargoBuild=true` / `dontCargoInstall=true` and installs its own `buildPhase`
  (`tauriBuildHook`) and `installPhase` (`tauriInstallHook`), so it **replaces**
  `rustPlatform`'s build, it does not wrap it.
- Runs `cargo tauri build --bundles "${tauriBundleType:-deb}" --target <host> -- -j$NIX_BUILD_CORES
  --target <host> --offline`. Note `--offline`: cargo is already vendored, and the Tauri CLI runs
  `beforeBuildCommand` (`npm run build`) itself, which is why `node` and the npm deps must be
  present in the derivation.
- Honours `buildAndTestSubdir`, `cargoBuildType`, `cargoBuildFeatures`, `cargoBuildFlags`, and
  appends `build.target-dir` to `config.toml` because
  [Tauri ignores `$CARGO_TARGET_DIR`](https://github.com/tauri-apps/tauri/issues/10190).
- **`tauriInstallHook` installs by unpacking the `.deb` bundle**:
  `mv target/<host>/<profile>/bundle/deb/*/data/usr/* $out/`. So `$out` gets whatever the Tauri
  bundler generated — including a `.desktop` file you probably did not write.
- Adds a `preFixup` hook that extends `gappsWrapperArgs` (webkit `asset` protocol, gstreamer
  plugin path, `__NV_DISABLE_EXPLICIT_SYNC`). It expects `wrapGAppsHook4` to be present.

## The derivation

```nix
{ lib, rustPlatform, cargo-tauri, importNpmLock, nodejs_22, pkg-config, wrapGAppsHook4,
  makeDesktopItem, webkitgtk_4_1, gtk3, libsoup_3, glib, glib-networking, cairo, pango,
  openssl, librsvg }:

let
  packageJSON = lib.importJSON ../package.json;

  desktopItem = makeDesktopItem {
    name = "link-router";
    desktopName = "Link Router";
    exec = "link-router %u";          # %u — the clicked URL is passed as an argument
    icon = "link-router";
    terminal = false;
    categories = [ "Utility" "Network" ];
    mimeTypes = [ "x-scheme-handler/linkrouter" ];   # this is what makes it a scheme handler
    startupWMClass = "Link Router";
  };
in
rustPlatform.buildRustPackage {
  pname = "link-router";
  version = packageJSON.version;

  # Only what the build reads: keeps node_modules/ and target/ out of the input hash.
  src = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../index.html ../package.json ../package-lock.json ../vite.config.ts ../src
      ../src-tauri/build.rs ../src-tauri/Cargo.toml ../src-tauri/Cargo.lock
      ../src-tauri/src ../src-tauri/capabilities ../src-tauri/icons
      ../src-tauri/tauri.conf.json
    ];
  };

  cargoRoot          = "src-tauri";     # where Cargo.toml lives
  buildAndTestSubdir = "src-tauri";     # where cargo is invoked
  cargoLock.lockFile = ../src-tauri/Cargo.lock;   # no cargoHash to maintain

  # cargo test would rebuild the tree without the tauri feature flags; the suite is vitest.
  doCheck = false;

  # No npmDepsHash to maintain either. The Tauri CLI runs `npm run build` itself.
  npmDeps = importNpmLock {
    package     = packageJSON;
    packageLock = lib.importJSON ../package-lock.json;
  };

  nativeBuildInputs = [
    cargo-tauri.hook               # replaces buildPhase/installPhase — see above
    nodejs_22                      # beforeBuildCommand needs it
    importNpmLock.npmConfigHook    # must match importNpmLock, not buildNpmPackage's hook
    pkg-config
    wrapGAppsHook4
  ];

  buildInputs = [
    webkitgtk_4_1 gtk3 libsoup_3 glib glib-networking cairo pango openssl librsvg
  ];

  env.OPENSSL_NO_VENDOR = 1;         # link nixpkgs' openssl, don't compile a vendored copy
}
```

Points worth internalising:

- **`cargoRoot` vs `buildAndTestSubdir`** — the first tells `rustPlatform` where to vendor from,
  the second where to `cd` before building. For a Tauri layout both are `src-tauri`.
- **Match the npm hook to the npm deps.** `importNpmLock.npmConfigHook` goes with
  `importNpmLock`; `buildNpmPackage`'s own `npmConfigHook` expects an `npmDepsHash`-style
  fetch and will not find the deps.
- **`OPENSSL_NO_VENDOR = 1`** — without it the `openssl` crate tries to compile OpenSSL from a
  vendored tarball, which needs network. This is the sandbox rule from §3 of the main skill in
  its most common concrete form.
- An older, simpler-looking variant of this file built the frontend as a separate
  `buildNpmPackage`, `cp`'d it to `dist/` in `postPatch`, and ran plain `cargo build`. It builds
  cleanly and produces the broken app described above. **Simpler is not correct here.**

## Desktop file and scheme handler

The hook installs the bundler's generated `.desktop`, which is wrong for a URL handler on two
counts: its `Exec` has no `%u` (so the clicked URL never reaches the app) and it is a bare
command name (so it resolves against the *launching* app's `PATH` — a portal or browser, which
may not have the installing profile on it). Replace it and absolutise `Exec`:

```nix
postInstall = ''
  rm -f "$out/share/applications/Link Router.desktop"
  install -Dm644 ${desktopItem}/share/applications/link-router.desktop \
    "$out/share/applications/link-router.desktop"
  substituteInPlace "$out/share/applications/link-router.desktop" \
    --replace-fail "Exec=link-router" "Exec=$out/bin/link-router"
'';
```

`--replace-fail` (not `--replace`) so the build breaks if the string ever moves, rather than
silently producing a file with the wrong `Exec`.

## Guard the trap with an install check

The whole point of the `cargo-tauri.hook` switch is invisible at build time, so assert it:

```nix
doInstallCheck = true;
installCheckPhase = ''
  runHook preInstallCheck
  binary="$out/bin/.link-router-wrapped"        # wrapGAppsHook4 renames the real ELF
  [ -f "$binary" ] || binary="$out/bin/link-router"
  if ! grep -qa -- "/assets/index-" "$binary"; then
    echo "ERROR link-router binary embeds no frontend assets — built without tauri/custom-protocol?" >&2
    exit 1
  fi
  runHook postInstallCheck
'';
```

Two details that matter:

- **Check for the assets, not for the dev URL.** `localhost:1420` is present in a *correctly*
  built binary too (it is part of the serialised Tauri config) — confirmed by `grep -a` against a
  known-good build. Only the presence of Vite's hashed `/assets/index-*.js` and `.css` names
  distinguishes an embedded frontend from a missing one.
- **Look for the dotfile.** `wrapGAppsHook4` leaves `bin/link-router` as a ~16 KB wrapper script
  and the real 13 MB ELF as `bin/.link-router-wrapped`.

## home-manager module

Ship the module from the same flake so consumers get the package *and* the desktop wiring
together. Take `self` as the first argument so the module can default `package` to the flake's
own output:

```nix
self:
{ config, lib, pkgs, ... }:
let
  cfg = config.programs.link-router;
  desktopFile = "link-router.desktop";
in {
  options.programs.link-router = {
    enable = lib.mkEnableOption "the Link Router deep-link handler";

    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.stdenv.hostPlatform.system}.link-router;
      defaultText = lib.literalExpression "inputs.link-router.packages.\${system}.link-router";
    };

    # Opt-out, because enabling xdg.mimeApps makes home-manager own ~/.config/mimeapps.list.
    setAsDefaultHandler = lib.mkOption { type = lib.types.bool; default = true; };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [ cfg.package ];
    xdg.mimeApps = lib.mkIf cfg.setAsDefaultHandler {
      enable = true;
      defaultApplications."x-scheme-handler/linkrouter" = desktopFile;
      associations.added."x-scheme-handler/linkrouter"  = desktopFile;
    };
  };
}
```

Exposed as `homeManagerModules.default = import ./nix/hm-module.nix self;` and consumed as
`imports = [ inputs.link-router.homeManagerModules.default ];`.

Give any option that seizes ownership of a user-managed file (here `mimeapps.list`) an escape
hatch, and say so in its `description`.

## Matching devShell

Mirror the derivation's dependencies so `nix develop` can run `npm run tauri dev`:

```nix
devShells.default = pkgs.mkShell {
  packages = [ pkgs.nodejs_22 pkgs.cargo pkgs.rustc pkgs.rust-analyzer pkgs.cargo-tauri ];
  nativeBuildInputs = [ pkgs.pkg-config pkgs.wrapGAppsHook4 ];
  buildInputs = [ pkgs.webkitgtk_4_1 pkgs.gtk3 pkgs.libsoup_3 pkgs.glib pkgs.glib-networking
                  pkgs.cairo pkgs.pango pkgs.openssl pkgs.librsvg ];
  env.OPENSSL_NO_VENDOR = 1;

  # Required on Wayland so GTK reports the correct display scale.
  # https://wiki.nixos.org/wiki/Tauri
  shellHook = ''export XDG_DATA_DIRS="$GSETTINGS_SCHEMAS_PATH"'';
};
```

## Budget

This build is heavy: the resulting closure is **1.2 GiB** (`nix path-info -Sh`) and a cold Rust
release build of the webkit/GTK crate tree needs many gigabytes of scratch space in `/nix`. Check
`df -h /nix` before starting — out-of-space presents as SIGSEGVs and LLVM IO errors from random
crates, not as a clear disk error. See the lessons-learned section of the main skill.
