"""Governed CSV bootstrap for tribe, language and origin references."""
from __future__ import annotations
import csv
from pathlib import Path
from registries.reference_authority import ReferenceAuthoringRequest,ReferenceType,OriginType
class GovernedReferenceBootstrap:
    def __init__(self,service,seed_root): self.service=service; self.seed_root=Path(seed_root)
    def bootstrap(self,submitter,approver):
        made=[]
        tribes=self.seed_root/'name_catalogue/novegeo/references/novegeo_tribes.csv'
        with tribes.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                made.append(self.service.author(ReferenceAuthoringRequest(ReferenceType.TRIBE,row['tribe_name'],submitter,approver,'file.novegeo.native.tribes.v001',requested_code=row['id'],attributes={'language_label':row['language'],'tribe_identity':row['tribe_identity']})))
                made.append(self.service.author(ReferenceAuthoringRequest(ReferenceType.LANGUAGE,row['language'],submitter,approver,'file.novegeo.native.tribes.v001')))
        for rel in ('name_catalogue/multicultural/multicultural_first_names.csv','name_catalogue/multicultural/accented_multicultural_first_names.csv','name_catalogue/multicultural/multicultural_second_names.csv','name_catalogue/multicultural/multicultural_accented_second_names.csv','name_catalogue/immigration/global_paired_names.csv'):
            p=self.seed_root/rel
            with p.open(encoding='utf-8-sig',newline='') as f:
                for row in csv.DictReader(f):
                    origin=row.get('origin') or row.get('Origin')
                    language=row.get('language') or row.get('Language')
                    if origin:
                        for label in (x.strip() for x in origin.split('/') if x.strip()): made.append(self.service.author(ReferenceAuthoringRequest(ReferenceType.ORIGIN,label,submitter,approver,rel,origin_type=OriginType.SOURCE_DECLARED_ORIGIN)))
                    if language:
                        for label in (x.strip() for x in language.split('/') if x.strip()): made.append(self.service.author(ReferenceAuthoringRequest(ReferenceType.LANGUAGE,label,submitter,approver,rel)))
        return tuple(made)
