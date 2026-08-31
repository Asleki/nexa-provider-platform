from .common import connect_postgresql,write_json
def main():
    c=connect_postgresql()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT count(*),count(DISTINCT parent_city_id),bool_and(partition_status='COMPLETE'),bool_and(publication_status='PUBLISHED') FROM geography.nngla_city_district_public_read_v1")
            row=cur.fetchone()
        if row is None or (int(row[0]),int(row[1]),bool(row[2]),bool(row[3])) != (64,8,True,True): raise SystemExit("CITY_DISTRICT public verification failed")
        write_json({"entity":"CITY_DISTRICT","publicCount":64,"parentCityCount":8,"status":"PASS"}); return 0
    finally: c.close()
if __name__=="__main__": raise SystemExit(main())
