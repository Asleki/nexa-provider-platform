ENTITY="CITY_DISTRICT"; EXPECTED=64; PUBLIC_VIEW="geography.nngla_city_district_public_read_v1"
def matrix_row(count):
    count=int(count); return {"entity":ENTITY,"publicCount":count,"expectedCount":EXPECTED,"qualified":count==EXPECTED}
