from pathlib import Path
import pytest

from registries.nngla.spatial_realization.orchestration import GovernedSpatialBatchEngine
from registries.nngla.spatial_realization.persistence import MemorySpatialRealizationRepository
from registries.nngla.spatial_realization.topology import PassThroughTopologyEngine
from verification.nngla.p006_7_11_15_5.common import effective_date,preview_payload,repair_mode,selected_roots
from verification.nngla.p006_7_11_15_5.execute import parser as execute_parser
from verification.nngla.p006_7_11_15_5.preview import parser as preview_parser


def test_phase_f_root_selection_and_repair_mode_are_fail_closed():
    assert len(selected_roots(roots=None,all_cities=True))==8
    with pytest.raises(ValueError):selected_roots(roots=['NG-PLC-000001'],all_cities=True)
    assert repair_mode('safe-automatic').value=='SAFE_AUTOMATIC'
    assert repair_mode('governed-structural').value=='GOVERNED_STRUCTURAL'
    assert effective_date('2026-08-25')=='2026-08-25'
    with pytest.raises(ValueError): effective_date('25/08/2026')


def test_preview_report_exposes_governance_and_supporting_spatial_reference():
    engine=GovernedSpatialBatchEngine(MemorySpatialRealizationRepository(),PassThroughTopologyEngine(),repository_revision='rev')
    report=preview_payload(engine.preview(['NG-PLC-000001']))
    assert report['executionReady'] is True
    assert report['repairMode']=='TEST_PASSTHROUGH'
    assert report['effectiveDate']
    assert report['assessments'][0]['supportingSpatialPointId']=='NG-SPT-000629'
    assert report['confirmationToken'].startswith('REALIZE-NNGLA-CITIES::memory_novegeo::')


def test_phase_f_cli_requires_explicit_selection_and_execute_acknowledgement_contract():
    preview_args=preview_parser().parse_args(['--roots','NG-PLC-000001'])
    assert preview_args.roots==['NG-PLC-000001'] and not preview_args.all_cities
    execute_args=execute_parser().parse_args([
        '--roots','NG-PLC-000001','--effective-date','2026-08-25','--approved-fingerprint','a'*64,'--confirmation','token',
        '--submitter','s','--approver','a','--execute',
    ])
    assert execute_args.execute is True and execute_args.effective_date=='2026-08-25'


def test_phase_f_tools_do_not_embed_credentials_or_roadmap_mutation():
    root=Path('verification/nngla/p006_7_11_15_5')
    text='\n'.join(path.read_text() for path in root.glob('*.py'))
    assert 'roadmap_frontend' not in text
    assert 'PGPASSWORD=' not in text
    assert 'getpass' in text
    assert '--execute' in text
