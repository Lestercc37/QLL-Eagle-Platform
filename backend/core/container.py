from __future__ import annotations

from dataclasses import dataclass

from backend.core.settings import Settings, get_settings


@dataclass(frozen=True)
class Container:
    """Application dependency container.

    The container is intentionally minimal in this stage and only exposes
    infrastructure-level dependencies required to boot the API.
    """

    settings: Settings


def build_container() -> Container:
    return Container(settings=get_settings())
