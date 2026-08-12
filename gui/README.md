# Dream World desktop GUI

This standalone iced 0.13 desktop app manages the public
`ghcr.io/maxxu123456/dream-world:latest` image through the Docker CLI. It does
not read the repository's Compose file or any other repository file at runtime.

It owns a labeled container named `dream-world-gui`, publishes the DS ports to
the confirmed LAN IP, publishes the website only to `127.0.0.1:8080`, and uses
the shared `dream-world-data` volume. Before Start, it requires and persists the
Pal Pad Friend Code for the connecting save; that code is passed to the image so
GameSpy preserves the cartridge's profile ID and avoids error 60000. An
unrelated container with the same name is never modified.

## Develop

Install a current stable Rust toolchain, then run from this directory:

```sh
cargo fmt --all -- --check
cargo test
cargo run
```

Create a release build with:

```sh
cargo build --release
```

Tagged releases are built by `.github/workflows/gui-release.yml` for Apple
Silicon and Intel macOS, x86-64 Windows, and x86-64 Linux.
