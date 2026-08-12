# Agent notes

Read this file before changing the wrapper or debugging a console connection.

## Architecture

- `server/` is a vendored snapshot of `dreamworld-reawakened` plus its two
  submodules and four pre-patched SWFs. The image must not clone or download
  source at build or runtime.
- The Game Sync process listens on UDP 53 and TCP 80, 443, and 29900. The web
  process listens on 8080. `HOST_IP` is both the published LAN address and the
  DNS answer returned to the console.
- Both processes use `/opt/server/save_data`, backed by the named volume
  `dream-world-data`. Never delete that volume unless the user explicitly asks
  to erase progress. Use a separate, clearly named temporary volume for tests.
- On an empty volume, the entrypoint starts Game Sync first and waits for a
  complete player upload before starting `main.py`. Waiting is healthy and must
  not cause a restart loop.
- The desktop app is self-contained. It invokes Docker directly and cannot
  depend on the repository or `docker-compose.yml` at runtime.

## Flash projector

- Modern browsers and Ruffle do not run the restored site correctly. The
  supported client is the standalone Adobe Flash Player projector 32.0.0.465.
- The GUI copies this entry URL:
  `http://127.0.0.1:8080/src/swf/theme/assets/common/dream-world-projector-v25.swf`.
  The alias maps to the vendored `main.patched.swf` and redirects once to add
  the FlashVars normally supplied by the browser embed.
- A projector stuck at 0% was traced with the Adobe debug projector. Legacy
  SWFs request same-host assets with literal `..` path segments. Flash reports
  security sandbox violations before those requests complete. The canonical
  redirect in `server/api/server.py` removes dot segments and is required.
- A successful load requests the alert XML/SWF assets, then calls the
  `pgl.member.profile.pdw_login` and `pdw.home.pdw_timecheck` APIs. Verify those
  signals as well as the visible welcome screen.
- Projector FlashVars include private member data and a token in the redirected
  query. Port 8080 must remain bound to `127.0.0.1`, and redirect locations must
  never be copied into logs, docs, issues, or chat.
- Flash caches aggressively. If entry response behavior changes, bump the
  version in the projector alias and update both the GUI and docs.
- Do not re-import whole ActionScript classes with FFDEC. Tests of that approach
  produced invalid AVM2 verifier/runtime behavior. Preserve the vendored
  pre-patched SWFs and prefer an HTTP-layer compatibility fix.
- A bootstrap SWF, `crossdomain.xml`, `Security.loadPolicyFile`, and changing
  the SWF `useNetwork` flag did not fix this problem and are not required.

## Game Sync and saved data

- A new save may have no Friend Code. This server can create its first local
  WFC profile; it does not contact Kaeru while the console uses this host as
  Primary DNS.
- An existing save must use the 12-digit Friend Code from that exact save so
  the server can preserve its embedded GameSpy profile ID and avoid error
  60000.
- Error 52210 occurs before Friend Code login and usually means DNS, routing,
  firewall, VPN, or LAN-isolation trouble.
- The tucked-in Pokemon can wake and return with the save. The unfinished part
  is transferring newly befriended Dream World Pokemon to the Entralink or
  Entree Forest. Use a disposable Pokemon while testing.
- API requests and Game Sync records can contain private player identifiers.
  Do not paste raw logs into documentation, commits, issues, or chat. Never
  commit a user's LAN IP, Friend Code, profile ID, or player query parameters.

## Verification and releases

- Test first-run behavior with a fresh temporary volume without touching
  `dream-world-data`.
- Run `cargo fmt --all -- --check`, `cargo test`, and `cargo build --release`
  from `gui/`. Build the Docker image and verify its healthcheck separately.
- GUI tags trigger `.github/workflows/gui-release.yml`. A release is complete
  only when its workflow is green and all four macOS arm64, macOS x86-64,
  Windows x86-64, and Linux x86-64 binaries are attached.
