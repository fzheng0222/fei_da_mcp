"""
Shared BigQuery client for all domains.
"""

from google.cloud import bigquery

# Singleton BigQuery client - uses gcloud credentials automatically
_client = None

def get_client() -> bigquery.Client:
    """Get the shared BigQuery client."""
    global _client
    if _client is None:
        _client = bigquery.Client()
    return _client
