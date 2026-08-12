# Dream World desktop GUI

This iced 0.13 app manages `ghcr.io/maxxu123456/dream-world:latest` through the
Docker CLI. It is self-contained and does not read repository files at runtime.

It manages the labeled `dream-world-gui` container, binds the DS ports to the
confirmed LAN IP, binds the site to `127.0.0.1:8080`, and stores data in
`dream-world-data`. New saves can create a local WFC profile. Existing saves can
provide a Pal Pad Friend Code to preserve their profile and avoid error 60000.

The UI displays the standalone Flash projector URL and never opens Dream World
in the default browser.

## Develop

```sh
cargo fmt --all -- --check
cargo test
cargo build --release
```

Tagged releases build Apple Silicon and Intel macOS, x86-64 Windows, and
x86-64 Linux binaries with `.github/workflows/gui-release.yml`.
