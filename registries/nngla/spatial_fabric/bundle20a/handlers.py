"""Pure command handlers for Bundle 20A orchestration."""
from .materialize import materialize
from .qualification import qualify_bundle

def handle_preview(): return {"qualification_findings": qualify_bundle()}
def handle_materialize(): return materialize()
