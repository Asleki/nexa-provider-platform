"""Read-only verification for catalogue-plan results."""
class CataloguePlanVerificationService:
    def __init__(self,preview_service,name_repository,context_repository): self.previews=preview_service; self.names=name_repository; self.contexts=context_repository
    def verify(self,request,*,database_name,environment):
        preview=self.previews.preview(request,database_name=database_name,environment=environment); records=self.names.list_all(); scoped=[x for x in records if x.metadata.runtime_mode==request.runtime_mode]
        missing_profiles=[x.name_id for x in scoped if self.contexts.get_profile_by_name(x.name_id) is None]
        return {"plan_id":request.plan_id,"runtime_mode":request.runtime_mode,"plan_fingerprint":preview.plan_fingerprint,"canonical_name_count":len(scoped),"missing_orthography_profiles":missing_profiles,"passed":not missing_profiles}
__all__=["CataloguePlanVerificationService"]
