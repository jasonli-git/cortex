"""AI extraction: turning chunked resources into knowledge objects.

Heavy-tier models run here, at ingestion time, so that retrieval and chat can
stay fast and cheap later (spec principle 8: expensive reasoning happens once).
"""

from pks.extraction.stages import register_stages

__all__ = ["register_stages"]
