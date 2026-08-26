"""Read-only Delivery-2 candidate-package preview CLI; performs no database writes."""
from __future__ import annotations
import argparse, json
from pathlib import Path

from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from registries.nngla.spatial_realization.shared_face_preview import build_read_only_shared_face_preview


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--runtime-mode',choices=('simulation','production'),default='production')
    parser.add_argument('--author-actor-id',default='candidate-preview')
    parser.add_argument('--material-rule',action='append',default=[])
    parser.add_argument('--output')
    args=parser.parse_args(argv)
    preview=build_read_only_shared_face_preview(args.root,material_rule_codes=tuple(args.material_rule))
    package=build_candidate_package(preview,runtime_mode=args.runtime_mode,author_actor_id=args.author_actor_id)
    payload={
        'delivery':'P006.7.11.15.5-DELIVERY2-GOVERNED-CANDIDATE-LIFECYCLE',
        'fabricRunId':package.fabric_run_id,
        'packageSha256':package.package_sha256,
        'status':package.lifecycle_status.value,
        'rootPlaceId':package.requested_root_place_id,
        'parentAdministrativeAreaId':package.parent_administrative_area_id,
        'scopeFingerprint':package.scope_fingerprint,
        'edgeGraphSha256':package.edge_graph_sha256,
        'faceSetSha256':package.face_set_sha256,
        'candidateCount':len(package.sibling_candidates),
        'canonicalDatabaseMutation':False,
        'writeCapability':'CANDIDATE_TABLES_ONLY_NOT_USED_BY_THIS_PREVIEW',
    }
    text=json.dumps(payload,indent=2,sort_keys=True)
    if args.output: Path(args.output).write_text(text+'\n',encoding='utf-8')
    print(text)
    return 0

if __name__=='__main__': raise SystemExit(main())
