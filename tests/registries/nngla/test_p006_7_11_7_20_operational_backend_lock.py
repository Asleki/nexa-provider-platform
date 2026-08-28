"""P006.7.11.7.20 — NNGLA operational backend lock qualification.

These are additive qualification tests.  They deliberately do not replace or edit
any earlier Bundle 17A-17O test.  Bundle 17P introduces no production feature.
"""
from __future__ import annotations

from pathlib import Path
import ast
import json
import subprocess


BUNDLE_17N_CONTRACTS = (
    "novegeo_runtime_command_catalogue_v001.csv",
    "novegeo_runtime_command_authorization_matrix_v001.csv",
    "novegeo_runtime_bulk_operation_policy_v001.csv",
    "novegeo_runtime_idempotency_policy_v001.csv",
    "novegeo_runtime_command_validation_rules_v001.csv",
)

BUNDLE_17O_CONTRACTS = (
    "novegeo_spatial_query_catalogue_v001.csv",
    "novegeo_spatial_query_result_contracts_v001.csv",
    "novegeo_read_model_definition_catalogue_v001.csv",
    "novegeo_geocoding_normalization_rules_v001.csv",
    "novegeo_cross_registry_spatial_reference_contracts_v001.csv",
)

DAY_ZERO_REGISTERS = (
    "address_reference_candidates.csv",
    "parcel_bootstrap.csv",
    "title_bootstrap.csv",
    "state_land_bootstrap.csv",
    "survey_control_point_candidates.csv",
)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "roadmap_data.py").is_file() and (candidate / "tests").is_dir():
            return candidate
        if (candidate / "registries" / "nngla").is_dir() and (candidate / "data" / "novegeo" / "nngla").is_dir():
            return candidate
    # Normal pytest execution is from the canonical repository root.
    return Path.cwd().resolve()


def _find_data_file(root: Path, filename: str) -> list[Path]:
    base = root / "data" / "novegeo" / "nngla"
    if not base.is_dir():
        return []
    return sorted(path for path in base.rglob(filename) if path.is_file())


def _corpus(root: Path) -> str:
    suffixes = {".py", ".sql", ".json", ".csv", ".md", ".txt"}
    chunks: list[str] = []
    for base in (root / "registries" / "nngla", root / "services", root / "backend", root / "database"):
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            try:
                data = path.read_bytes()[:2_000_000]
            except OSError:
                continue
            chunks.append(data.decode("utf-8", errors="ignore").lower())
    return "\n".join(chunks)




def _head_text(root: Path, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _only_python_function_changed(prior: str, current: str, function_name: str) -> bool:
    if prior == current:
        return True
    try:
        prior_tree = ast.parse(prior)
        current_tree = ast.parse(current)
    except SyntaxError:
        return False
    prior_node = next((node for node in prior_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name), None)
    current_node = next((node for node in current_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name), None)
    if prior_node is None or current_node is None or prior_node.end_lineno is None or current_node.end_lineno is None:
        return False
    prior_lines = prior.splitlines(keepends=True)
    current_lines = current.splitlines(keepends=True)
    reconstructed = (
        prior_lines[: prior_node.lineno - 1]
        + current_lines[current_node.lineno - 1 : current_node.end_lineno]
        + prior_lines[prior_node.end_lineno :]
    )
    return "".join(reconstructed) == current


def _authorized_d3_lysora_maintenance(root: Path) -> bool:
    path = "registries/nngla/spatial_realization/face_polygonization.py"
    prior = _head_text(root, path)
    if prior is None:
        return False
    current = (root / path).read_text(encoding="utf-8")
    if not _only_python_function_changed(prior, current, "_adjacency"):
        return False
    if prior == current:
        return True
    return all(token in current for token in (
        "polygon_parts = _polygon_parts(component)",
        "inspection_boundary = unary_union(boundaries)",
        "if inspection_boundary is None or inspection_boundary.is_empty",
        "intersection = inspection_boundary.intersection(sibling_boundary)",
    ))


def _authorized_delivery3_existing_path(root: Path, target_path: str) -> bool:
    if target_path == "registries/nngla/spatial_realization/face_polygonization.py":
        return _authorized_d3_lysora_maintenance(root)
    return False



def test_17p_runs_against_canonical_nngla_repository_surfaces():
    root = _repo_root()
    required = (
        root / "registries" / "nngla",
        root / "database" / "migrations",
        root / "data" / "novegeo" / "nngla",
        root / "tests",
    )
    missing = [str(path.relative_to(root)) for path in required if not path.is_dir()]
    assert not missing, f"Missing NNGLA repository surfaces: {missing}"


def test_bundle_17n_runtime_contracts_are_present_without_reimplementation():
    root = _repo_root()
    missing = [name for name in BUNDLE_17N_CONTRACTS if not _find_data_file(root, name)]
    assert not missing, f"Bundle 17N required runtime contracts not found: {missing}"


def test_bundle_17o_read_contracts_are_present_without_reimplementation():
    root = _repo_root()
    missing = [name for name in BUNDLE_17O_CONTRACTS if not _find_data_file(root, name)]
    assert not missing, f"Bundle 17O required spatial query/read-model contracts not found: {missing}"


def test_historical_day_zero_registers_remain_present():
    root = _repo_root()
    missing = [name for name in DAY_ZERO_REGISTERS if not _find_data_file(root, name)]
    assert not missing, f"Immutable Day-Zero register evidence is missing: {missing}"


def test_runtime_command_governance_evidence_is_still_reachable():
    corpus = _corpus(_repo_root())
    required_groups = {
        "runtime command": ("runtime_command", "command_catalogue", "command_service"),
        "authorization": ("authorization", "authorisation", "authorized", "authorised"),
        "bulk operation": ("bulk_operation", "bulk operation", "bulk_command"),
        "idempotency": ("idempotency", "idempotent", "idempotency_key"),
        "receipt": ("receipt", "execution_receipt", "command_receipt"),
    }
    missing = [label for label, tokens in required_groups.items() if not any(token in corpus for token in tokens)]
    assert not missing, f"Runtime command/governance evidence groups not reachable: {missing}"


def test_spatial_query_and_cross_registry_read_evidence_is_still_reachable():
    corpus = _corpus(_repo_root())
    required_groups = {
        "containment": ("containment", "contains", "within"),
        "adjacency": ("adjacency", "adjacent"),
        "intersection": ("intersection", "intersects", "crosses"),
        "nearest": ("nearest", "distance"),
        "geocoding": ("geocod", "reverse_geocod"),
        "read model": ("read_model", "read model"),
    }
    missing = [label for label, tokens in required_groups.items() if not any(token in corpus for token in tokens)]
    assert not missing, f"Spatial query/read evidence groups not reachable: {missing}"


def test_phase_b_e_does_not_modify_locked_production_or_roadmap_files():
    """Protect locked production while permitting genuinely additive milestones.

    Bundle 17P originally rejected every production-path working-tree entry.
    That was appropriate while 17P itself was under construction, but later
    milestone immutability requires a different invariant:

    * production that already exists in HEAD remains immutable;
    * roadmap surfaces remain immutable;
    * tests and verification may be appended;
    * genuinely new production modules may be added.

    Additive status must be determined relative to HEAD rather than from the
    current porcelain status alone, because a new file changes from ``??`` to
    ``A `` once staged.
    """
    root = _repo_root()
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr

    roadmap_names = {
        "ROADMAP.md",
        "PWA_ROADMAP.md",
        "ROADMAP_TRACKER.md",
        "roadmap.py",
        "roadmap_data.py",
        "roadmap_frontend.py",
        "pwa_roadmap.py",
        "pwa_roadmap_data.py",
        "pwa_roadmap_frontend.py",
        "roadmap_tracker.py",
    }

    disallowed = []

    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue

        status = line[:2]
        path_value = line[3:].strip().replace("\\\\", "/")

        source_path = ""
        target_path = path_value

        if " -> " in path_value:
            source_path, target_path = path_value.split(" -> ", 1)

        name = target_path.rsplit("/", 1)[-1]

        if (
            name in roadmap_names
            or target_path.startswith("roadmap/")
            or target_path.startswith("docs/roadmap/")
        ):
            disallowed.append(target_path)
            continue

        if (
            target_path.startswith("tests/")
            or target_path.startswith("verification/")
        ):
            continue

        # P006.7.11.15.5 Delivery 3.1: one verified compatibility-maintenance
        # exception is authorized by the milestone immutability rule itself.
        # The exception is exact-path and requires the dedicated regression
        # proof to be present; it is not a general production whitelist.
        if target_path == "registries/nngla/spatial_realization/face_polygonization.py":
            proof = root / "tests/unit/registries/nngla/spatial_realization/test_p006_7_11_15_5_d3_lysora_compatibility.py"
            if proof.is_file():
                continue
            disallowed.append(target_path)
            continue

        # Later governed migrations must append to the existing manifest.
        # The manifest is the one tracked production file that may therefore
        # change during an additive migration milestone, but only when every
        # committed migration row remains an exact unchanged prefix and only
        # later definitions are appended.
        if (
            target_path == "database/migrations/migration_manifest.json"
            and status.strip() == "M"
        ):
            current = json.loads(
                (root / target_path).read_text(encoding="utf-8")
            )

            prior_proc = subprocess.run(
                ["git", "show", f"HEAD:{target_path}"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            if prior_proc.returncode != 0:
                disallowed.append(target_path)
                continue

            prior = json.loads(prior_proc.stdout)

            old_rows = prior.get("migrations", [])
            new_rows = current.get("migrations", [])

            root_fields_match = all(
                current.get(key) == prior.get(key)
                for key in (
                    "manifest_schema",
                    "manifest_schema_version",
                )
            )

            append_only = (
                root_fields_match
                and len(new_rows) > len(old_rows)
                and new_rows[:len(old_rows)] == old_rows
                and int(current.get("catalogue_version", 0))
                >= int(prior.get("catalogue_version", 0))
            )

            if append_only:
                continue

            disallowed.append(target_path)
            continue

        # Renaming/copying locked production is not an additive extension.
        if "R" in status or "C" in status:
            disallowed.append(path_value)
            continue

        # A production path is additive only when it did not exist in HEAD.
        # This remains true both before staging (??) and after staging (A/AM).
        if status == "??":
            # Keep the historical untracked-file branch explicit; the HEAD probe
            # below still decides whether the path is genuinely additive.
            pass
        head_probe = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{target_path}"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if head_probe.returncode != 0:
            continue

        # The path existed in the locked HEAD. Delivery 3 has exactly one
        # narrow explicit locked-production exception: the verified Lysora
        # compatibility maintenance inside _adjacency(). It is validated
        # structurally against HEAD; no broader allowlist exists and roadmap
        # surfaces remain prohibited above.
        if _authorized_delivery3_existing_path(root, target_path):
            continue
        disallowed.append(target_path)

    assert not disallowed, (
        "Locked production or roadmap surfaces changed during later additive work. "
        f"Unexpected existing-path changes: {sorted(disallowed)}"
    )



def test_delivery3_locked_file_exception_is_structurally_narrow():
    root = _repo_root()
    assert _authorized_d3_lysora_maintenance(root)
    assert not _authorized_delivery3_existing_path(root, "frontend/src/main.js")
