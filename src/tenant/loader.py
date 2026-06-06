"""Tenant configuration loader.

`load_tenant("hyperswitch")` returns a validated `TenantConfig`. Resolves
paths relative to the project root so callers don't have to.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from src.tenant.config import TenantConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TENANTS_ROOT = PROJECT_ROOT / "tenants"


def load_tenant(slug: str) -> TenantConfig:
    config_path = TENANTS_ROOT / slug / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"tenant '{slug}' has no config at {config_path}. "
            f"Available tenants: {sorted(p.name for p in TENANTS_ROOT.iterdir() if p.is_dir())}"
        )
    with config_path.open() as f:
        data = yaml.safe_load(f)
    return TenantConfig.model_validate(data)


def load_product_profile(tenant: TenantConfig) -> dict:
    path = PROJECT_ROOT / tenant.product_profile.path
    with path.open() as f:
        return yaml.safe_load(f)
