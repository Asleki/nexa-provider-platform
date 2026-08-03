"""Named sequential catalogue qualification plans."""
from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class CataloguePlanStep:
    step_id:str; manifest_path:str; file_id:str; target_kind:str; classification:str
@dataclass(frozen=True,slots=True)
class CataloguePlan:
    plan_id:str; steps:tuple[CataloguePlanStep,...]
PLANS={
"native-core":CataloguePlan("native-core",(
CataloguePlanStep("native-first","database/seeds/name_catalogue/novegeo/manifest.json","file.novegeo.native.first_names.v001","first_name","native"),
CataloguePlanStep("native-middle","database/seeds/name_catalogue/novegeo/manifest.json","file.novegeo.native.second_names.v001","middle_name","native"),
CataloguePlanStep("native-surname","database/seeds/name_catalogue/novegeo/manifest.json","file.novegeo.native.surnames.v001","surname","native"),)),
"multicultural-core":CataloguePlan("multicultural-core",(
CataloguePlanStep("multi-first","database/seeds/name_catalogue/multicultural/manifest.json","file.novegeo.multicultural.first_names.v001","first_name","foreign"),
CataloguePlanStep("multi-surname","database/seeds/name_catalogue/multicultural/manifest.json","file.novegeo.multicultural.family_names.v001","surname","foreign"),)),
"multicultural-unicode":CataloguePlan("multicultural-unicode",(
CataloguePlanStep("accent-first","database/seeds/name_catalogue/multicultural/manifest.json","file.novegeo.multicultural.accented_first_names.v001","first_name","foreign"),
CataloguePlanStep("accent-surname","database/seeds/name_catalogue/multicultural/manifest.json","file.novegeo.multicultural.accented_family_names.v001","surname","foreign"),)),
}
def get_plan(plan_id):
    if plan_id not in PLANS: raise KeyError("catalogue plan was not found.")
    return PLANS[plan_id]
__all__=["CataloguePlanStep","CataloguePlan","PLANS","get_plan"]
