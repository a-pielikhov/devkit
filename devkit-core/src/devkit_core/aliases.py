from __future__ import annotations

# Alias table: {group_name: {alias: canonical}}
# Top-level aliases use group_name = "" (empty string)
ALIASES: dict[str, dict[str, str]] = {
    "": {
        "ls": "list",
        "enc": "encode",
        "dec": "decode",
    },
    "git": {
        "cb": "clean-branches",
        "lm": "list-merged",
        "sf": "sync-fork",
    },
}
