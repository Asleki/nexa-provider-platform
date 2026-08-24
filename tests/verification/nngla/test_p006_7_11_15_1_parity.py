import json
from pathlib import Path

from verification.nngla.p006_7_11_15_1.parity import Bundle22BParityVerifier, EXPECTED_LIVE_BASELINE


def _manifest():
    migrations=[]
    for i in range(1,21):
        mid=f"migration-{i}"
        if i==19: mid="m006_07_11_nngla_road_network_construction"
        if i==20: mid="m006_07_11_nngla_governed_spatial_publication"
        migrations.append({"migration_id":mid,"sequence_number":i,"forward_sha256":f"{i:064x}","expected_objects":{"tables":[],"indexes":[]}})
    migrations[18]["expected_objects"]={"tables":["geography.nngla_road_network_node","geography.nngla_road_segment_topology","geography.nngla_road_network_connection","geography.nngla_spatial_relationship_evidence"],"indexes":["ix_nngla_road_network_node_place"]}
    migrations[19]["expected_objects"]={"tables":["geography.nngla_publication_record"],"indexes":["ux_nngla_publication_active_subject_runtime"]}
    return {"migrations":migrations}


class Cursor:
    def __init__(self,manifest,*,applied_count=18,realized=(0,0,0),projection=(0,0),late_objects=False):
        self.manifest=manifest; self.applied_count=applied_count; self.realized=realized; self.projection=projection; self.late_objects=late_objects; self.sql=""; self.params=()
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def execute(self,sql,params=()): self.sql=" ".join(sql.split()); self.params=params
    def fetchall(self):
        if "FROM platform.schema_migration" in self.sql:
            return [(m["migration_id"],m["sequence_number"],m["forward_sha256"],"APPLIED") for m in self.manifest["migrations"][:self.applied_count]]
        return []
    def fetchone(self):
        s=self.sql
        if s=="SELECT current_database()": return ("npp_dev",)
        if "to_regclass" in s:
            rel=str(self.params[0])
            late={"geography.nngla_road_network_node","geography.nngla_road_segment_topology","geography.nngla_road_network_connection","geography.nngla_spatial_relationship_evidence","geography.nngla_publication_record"}
            return (self.late_objects or rel not in late,)
        if "FROM pg_indexes" in s: return (self.late_objects,)
        if "geometry_role_code='SPATIAL_REFERENCE_POINT'" in s: return (2411,)
        if "geometry_role_code=%s" in s: return (0,)
        if "nngla_place_reference" in s and "geometry_reference IS NOT NULL" in s: return (self.realized[0],)
        if "nngla_administrative_area" in s and "geometry_reference IS NOT NULL" in s: return (self.realized[1],)
        if "nngla_road" in s and "geometry_id IS NOT NULL" in s: return (self.realized[2],)
        if "FROM geography.nngla_address" in s: return (0,)
        if "FROM geography.nngla_place_reference" in s: return (700,)
        if "FROM geography.nngla_administrative_area" in s: return (192,)
        if "FROM geography.nngla_road" in s and "network" not in s and "segment" not in s: return (350,)
        if "FROM geography.nngla_canonical_crosswalk" in s: return (21,)
        if "nngla_spatial_read_projection_v1" in s: return self.projection
        if "SELECT COUNT(*)::bigint FROM geography.nngla_publication_record" in s: return (0,)
        if "nngla_road_segment_topology" in s: return (0,)
        if "nngla_road_network_node" in s: return (0,)
        if "nngla_road_network_connection" in s: return (0,)
        if "nngla_spatial_relationship_evidence" in s: return (0,)
        raise AssertionError(s)


class Connection:
    def __init__(self,manifest,**kwargs): self.manifest=manifest; self.kwargs=kwargs
    def cursor(self): return Cursor(self.manifest,**self.kwargs)
class Ctx:
    def __init__(self,conn): self.conn=conn
    def __enter__(self): return self.conn
    def __exit__(self,*a): return False
class Pool:
    def __init__(self,manifest,**kwargs): self.manifest=manifest; self.kwargs=kwargs; self.read_only=[]
    def connection(self,read_only=False): self.read_only.append(read_only); return Ctx(Connection(self.manifest,**self.kwargs))


def _write_manifest(tmp_path:Path,manifest):
    path=tmp_path/"database/migrations"; path.mkdir(parents=True); (path/"migration_manifest.json").write_text(json.dumps(manifest))


def test_verified_18_migration_foundation_with_zero_realization_is_pass_not_failure(tmp_path:Path):
    manifest=_manifest(); _write_manifest(tmp_path,manifest); pool=Pool(manifest,applied_count=18,late_objects=False)
    report=Bundle22BParityVerifier(pool,repository_root=tmp_path).qualify(repository_revision="dd3973c")
    assert report["overallStatus"]=="PASS"
    assert report["foundationSchema"]["foundationAppliedCount"]==18
    assert report["laterCapabilities"]["m006_07_11_nngla_road_network_construction"]["state"]=="DEFERRED_NOT_INSTALLED"
    assert report["laterCapabilities"]["m006_07_11_nngla_governed_spatial_publication"]["state"]=="DEFERRED_NOT_INSTALLED"
    assert report["realizationState"]["places"]=={"canonical":700,"spatiallyAssociated":0,"remaining":700}
    assert report["realizationState"]["administrativeAreas"]["boundariesAssociated"]==0
    assert report["realizationState"]["roads"]["geometryAssociated"]==0
    assert report["realizationState"]["addressesIssued"]==0
    assert report["publicReadState"]["publicProjection"]==0
    assert all(pool.read_only)


def test_realization_progress_and_nonzero_public_projection_do_not_make_readiness_fail(tmp_path:Path):
    manifest=_manifest(); _write_manifest(tmp_path,manifest); pool=Pool(manifest,applied_count=18,realized=(1,1,0),projection=(1,1),late_objects=False)
    report=Bundle22BParityVerifier(pool,repository_root=tmp_path).qualify()
    assert report["overallStatus"]=="PASS"
    assert report["realizationState"]["places"]["spatiallyAssociated"]==1
    assert report["publicReadState"]["mapRenderable"]==1


def test_applied_later_capabilities_are_allowed_when_their_objects_exist(tmp_path:Path):
    manifest=_manifest(); _write_manifest(tmp_path,manifest); pool=Pool(manifest,applied_count=20,late_objects=True)
    report=Bundle22BParityVerifier(pool,repository_root=tmp_path).qualify()
    assert report["overallStatus"]=="PASS"
    assert all(item["state"]=="INSTALLED" for item in report["laterCapabilities"].values())


def test_missing_foundation_migration_remains_a_failure(tmp_path:Path):
    manifest=_manifest(); _write_manifest(tmp_path,manifest); pool=Pool(manifest,applied_count=17,late_objects=False)
    report=Bundle22BParityVerifier(pool,repository_root=tmp_path).qualify()
    assert report["overallStatus"]=="FAIL"
    assert any(f["code"]=="FOUNDATION_MIGRATIONS_NOT_APPLIED" for f in report["findings"])


def test_feature_21_20_1_contract_remains_explicit():
    assert EXPECTED_LIVE_BASELINE["canonical"]["GEOGRAPHIC_FEATURE"]==21
    assert EXPECTED_LIVE_BASELINE["featurePublicationCandidates"]==20
    assert EXPECTED_LIVE_BASELINE["sovereignMainlandSpecialCases"]==1
