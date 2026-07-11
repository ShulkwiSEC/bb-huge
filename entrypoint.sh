#!/bin/bash
set -e

INSTALL_SCRIPT="/app/assets/scripts/bb-install-tools.sh"
MARKER="$HOME/.local/.bb-tools-installed"
INSTALL_LOG="$HOME/.local/bb-install-tools.log"

if [ ! -f "$MARKER" ]; then
    echo "[entrypoint] Recon toolkit not found — installing in the background (log: $INSTALL_LOG)."
    echo "[entrypoint] Starting the portal now; no need to wait for the install to finish."
    # Backgrounded so a slow/flaky tool build (nuclei, amass) never blocks the
    # portal from starting. `|| true` (and the fact this is a pipeline, whose
    # exit status is tee's, not the installer's) means a non-zero exit from
    # bb-install-tools.sh — which it deliberately returns whenever ANY single
    # tool fails — can never kill this script via `set -e`. The marker is
    # always written once the run finishes, success or not, so a flaky tool
    # doesn't force a full reinstall loop on every container restart; re-run
    # `docker compose exec bb-huge bash assets/scripts/bb-install-tools.sh`
    # by hand any time to retry just the tools that failed.
    # Capped at 2 build workers (not full nproc) + lowest CPU/IO scheduling
    # priority — verified live that an uncapped `go install` (nuclei/amass
    # especially) can burn 1000%+ CPU and starve the portal's own Python
    # startup for tens of seconds. This keeps the toolkit install from
    # fighting the app for the CPU it needs to actually come up promptly.
    (
        GOMAXPROCS=2 nice -n 19 ionice -c3 bash "$INSTALL_SCRIPT" 2>&1 | tee "$INSTALL_LOG"
        install_status="${PIPESTATUS[0]}"
        touch "$MARKER"
        if [ "$install_status" -eq 0 ]; then
            echo "[entrypoint] Recon toolkit installed successfully."
        else
            echo "[entrypoint] Recon toolkit install finished with some tools failing (exit $install_status) — see $INSTALL_LOG."
            echo "[entrypoint] Re-run any time: docker compose exec bb-huge bash assets/scripts/bb-install-tools.sh"
        fi
    ) &
else
    echo "[entrypoint] Recon toolkit already installed, skipping."
fi

exec "$@"