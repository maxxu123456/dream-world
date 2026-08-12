# Dream World desktop GUI

This standalone iced 0.13 desktop app manages the public
`ghcr.io/maxxu123456/dream-world:latest` image through the Docker CLI. It does
not read the repository's Compose file or any other repository file at runtime.

It owns a labeled container named `dream-world-gui`, publishes the DS ports to
the confirmed LAN IP, publishes the website only to `127.0.0.1:8080`, and uses
the shared `dream-world-data` volume. An unrelated container with the same name
is never modified.

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
