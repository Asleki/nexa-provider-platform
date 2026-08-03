def verify_readiness(names,context_repository):
    missing=[]
    for n in names:
        p=context_repository.get_profile_by_name(n.name_id); rel=context_repository.list_relationships(n.name_id)
        if p is None or not rel: missing.append(n.name_id)
    return {'total':len(names),'ready':len(names)-len(missing),'missing':tuple(missing),'passed':not missing}
