from .common import connect_postgresql,write_json
def main():
    c=connect_postgresql()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT count(*),count(DISTINCT parent_place_id),bool_and(source_qualification_status='QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY'),bool_and(legal_boundary_status='NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY'),bool_and(qualification_status='QUALIFIED'),bool_and(publication_status='PUBLISHED') FROM geography.nngla_town_public_read_v1")
            row=cur.fetchone()
        if row is None or (int(row[0]),int(row[1]),bool(row[2]),bool(row[3]),bool(row[4]),bool(row[5])) != (120,24,True,True,True,True): raise SystemExit("TOWN public verification failed")
        write_json({"entity":"TOWN","publicCount":120,"parentMunicipalityPlaceCount":24,"status":"PASS"}); return 0
    finally: c.close()
if __name__=="__main__": raise SystemExit(main())
