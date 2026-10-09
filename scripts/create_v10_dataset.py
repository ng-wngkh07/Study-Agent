"""Compatibility entry point for the durable, selectively reviewed curator.

The original proposals and builder are preserved in the takeover snapshot and
source audit. Releases require exact content-review proofs; no MLX is imported.
"""
from curate_v10 import main

if __name__ == "__main__":
    main()
