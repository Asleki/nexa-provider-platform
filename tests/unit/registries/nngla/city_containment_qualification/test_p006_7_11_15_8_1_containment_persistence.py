from registries.nngla.city_containment_qualification.persistence import PostgreSQLCityContainmentQualificationRepository


class Cursor:
    def __init__(self):
        self.calls=[]
        self.rows=[]
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self,sql,params=()): self.calls.append((sql,params))
    def fetchall(self): return list(self.rows)
    def fetchone(self): return self.rows[0] if self.rows else None


class LockedRepoStub:
    database_name="npp_dev"
    def __init__(self,*args,**kwargs): pass


class Connection:
    def __init__(self): self.cursor_ref=Cursor()
    def cursor(self): return self.cursor_ref


class Plan:
    qualification_id="city-containment:nngla:NG-ADM-000032:abc"
    city_id="NG-ADM-000032"
    parent_region_id="NG-ADM-000002"
    parent_region_geometry_id="region-geometry:nngla:NG-ADM-000002:v1"
    parent_region_geometry_sha256="a"*64
    source_record_id="NGP-000032"
    source_dataset_id="dataset:novegeo:administrative-boundaries"
    source_dataset_version="1"
    source_dataset_sha256="b"*64
    source_geometry_sha256="c"*64
    realization_method="PARENT_CONTAINED_NORMALIZATION"
    realization_version=1
    city_geometry_id="city-geometry:nngla:NG-ADM-000032:v1"
    geometry_sha256="d"*64
    source_valid=True
    source_non_empty=True
    source_geometry_type="POLYGON"
    source_strict_covered=False
    source_area_m2=100.0
    source_outside_parent_m2=0.000007
    source_outside_parent_ratio=7e-8
    normalized_valid=True
    normalized_non_empty=True
    normalized_geometry_type="POLYGON"
    normalized_strict_covered=False
    area_m2=99.999999
    normalized_outside_parent_m2=0.0
    normalized_outside_parent_ratio=0.0
    area_removed_m2=0.000001
    area_removed_ratio=1e-8
    label_point_covered=True
    qualification_basis_code="SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE"
    qualification_status="QUALIFIED"
    qualification_policy_version=1
    absolute_residue_max_m2=0.001
    ratio_residue_max=1e-12
    effective_date="2026-08-30"


def test_insert_qualification_persists_all_governed_measurements(monkeypatch):
    import registries.nngla.city_containment_qualification.persistence as module
    monkeypatch.setattr(module,"PostgreSQLCityRealizationRepository",LockedRepoStub)
    connection=Connection()
    repo=PostgreSQLCityContainmentQualificationRepository(connection,environment_name="dev")
    repo.insert_qualification(Plan())
    sql,params=connection.cursor_ref.calls[-1]
    assert "nngla_city_parent_containment_qualification" in sql
    assert sql.count("%s")==37
    assert len(params)==37
    assert Plan.normalized_outside_parent_m2 in params
    assert Plan.absolute_residue_max_m2 in params
    assert Plan.ratio_residue_max in params


class ReceiptPlan(Plan):
    fingerprint = "e" * 64
    database_name = "npp_dev"
    environment_name = "dev"
    publication_id = "city-publication:nngla:NG-ADM-000032:v1"
    repository_revision = "abc123"
    planned_action = "INSERT_AND_PUBLISH"


def test_execution_receipt_counts_selected_city_not_internal_rows(monkeypatch):
    import registries.nngla.city_containment_qualification.persistence as module
    monkeypatch.setattr(module, "PostgreSQLCityRealizationRepository", LockedRepoStub)
    connection = Connection()
    repo = PostgreSQLCityContainmentQualificationRepository(connection, environment_name="dev")
    repo.persist_execution(
        ReceiptPlan(),
        submitter_actor_id="npp-admin",
        approver_actor_id="asleki-admin",
        status="APPLIED",
        inserted_geometry_count=1,
        inserted_qualification_count=1,
        inserted_publication_count=1,
        reused_geometry_count=0,
    )
    receipt_sql, receipt_params = connection.cursor_ref.calls[-2]
    assert "nngla_execution_receipt" in receipt_sql
    assert receipt_params[9] == 1
    assert receipt_params[10] == 0
