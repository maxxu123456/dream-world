# Legal

This is a fan project for a service Nintendo shut down on January 20, 2014.

- Use your own legally owned game. No game ROMs are included or needed.
- This repository vendors the community-restored Global Link site and its assets
  under `server/` so the build is self-contained. Those files are the property of
  Nintendo, Game Freak, and Creatures. Making the Docker image or this repository
  public redistributes them, so that is your decision to make and your
  responsibility. Intended use is personal preservation.
- The wrapper code in this repository (Docker/Compose files, entrypoint,
  healthcheck, and docs) is MIT, see LICENSE. The vendored server keeps its own
  terms.
- Third party projects keep their own terms:
  - minibug1021/dreamworld-reawakened and its submodules (the server and assets)
  - kuroppoi/entralinked, MIT (the Game Sync method the server is based on)
  - JPEXS Free Flash Decompiler (used upstream to produce the pre-patched SWFs)
- Pokemon, Dream World, Global Link, Nintendo DS, and DSi are trademarks of their
  owners. This project is unofficial and unaffiliated.
