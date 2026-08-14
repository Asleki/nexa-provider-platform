"""Infrastructure API adapter for P006.7.9 NNGLA read models."""
from registries.nngla.read_service import NNGLAReadService


def build_default_nngla_read_service() -> NNGLAReadService:
    return NNGLAReadService()


__all__ = ["build_default_nngla_read_service", "NNGLAReadService"]
