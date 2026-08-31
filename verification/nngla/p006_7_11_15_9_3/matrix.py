ENTITY="TOWN"; EXPECTED=120; PUBLIC_VIEW="geography.nngla_town_public_read_v1"
def matrix_row(count):
    count=int(count); return {"entity":ENTITY,"publicCount":count,"expectedCount":EXPECTED,"qualified":count==EXPECTED}
