from registries.names import Surname,NameKind

def test_surname_enforces_kind_and_round_trip():
    n=Surname("surname:1","Ncube")
    assert n.name_kind is NameKind.SURNAME
    assert Surname.from_dict(n.to_dict())==n
