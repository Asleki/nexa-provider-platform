import hashlib,json
def catalogue_fingerprint(names,profiles,relationships):
    material={'names':sorted((x.name_id,x.runtime_mode,x.name_kind.value,x.search_value) for x in names),'profiles':sorted((x.name_id,x.structure_type.value,x.accented,x.tokens,x.separators) for x in profiles),'relationships':sorted((x.name_id,x.role.value,x.state.value,x.target_reference_id or '') for x in relationships)}
    return hashlib.sha256(json.dumps(material,sort_keys=True,ensure_ascii=False,default=list).encode()).hexdigest()
