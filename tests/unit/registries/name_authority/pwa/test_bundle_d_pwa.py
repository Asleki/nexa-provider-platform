from registries.name_authority.pwa import NameAuthorityPwaRuntimeConfig

def test_public_pwa_configuration_is_https_and_contains_no_database_material():
    c=NameAuthorityPwaRuntimeConfig("https://api.nexilabs.online")
    d=c.as_public_dict(); assert d["apiBaseUrl"].startswith("https://") and "postgres" not in str(d).lower()

def test_database_connection_material_is_rejected():
    for value in ("postgresql://user:pass@host/db","https://npp.rds.amazonaws.com:5432"):
        try: NameAuthorityPwaRuntimeConfig(value)
        except ValueError: pass
        else: raise AssertionError("unsafe public config accepted")
