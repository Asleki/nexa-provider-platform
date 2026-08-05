from fastapi import APIRouter, Request, Response, status
router=APIRouter(prefix="/health",tags=["health"] )
@router.get("/live")
def live(request:Request):
    return {"status":"alive","service":"nexa-infrastructure","correlationId":request.state.correlation_id}
@router.get("/ready")
def ready(request:Request,response:Response):
    state=request.app.state.infrastructure_state
    ok=bool(state.ready)
    if not ok: response.status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status":"ready" if ok else "not_ready","databaseReady":bool(state.database_ready),"correlationId":request.state.correlation_id}
