from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(slots=True)
class ApplicationState:
    started_at:datetime|None=None
    ready:bool=False
    database_ready:bool=False
    def start(self): self.started_at=datetime.now(timezone.utc); self.ready=True
    def stop(self): self.ready=False
