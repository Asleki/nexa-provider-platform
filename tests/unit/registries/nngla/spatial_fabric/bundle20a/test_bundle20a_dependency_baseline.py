from pathlib import Path
import registries.nngla.spatial_fabric.bundle20a as bundle20a
import registries.nngla.spatial_fabric.bundle20b as bundle20b


def test_bundle20_has_no_undeclared_shapely_runtime_dependency():
    roots = [Path(bundle20a.__file__).parent, Path(bundle20b.__file__).parent]
    offenders = []
    for root in roots:
        for path in root.glob('*.py'):
            text = path.read_text(encoding='utf-8')
            if 'from shapely' in text or 'import shapely' in text:
                offenders.append(str(path))
    assert offenders == []
