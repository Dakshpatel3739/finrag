"""
config — runtime-tunable system configuration.

All retrieval/generation tuning parameters live in the `system_config` table
so they can be changed without a redeploy. Secrets and infra settings come from
env vars (pydantic-settings). Typed accessors via get_config().
"""

from config.settings import Settings, get_settings
from config.system_config import ConfigKey, get_config, set_config

__all__ = ["ConfigKey", "Settings", "get_config", "get_settings", "set_config"]
