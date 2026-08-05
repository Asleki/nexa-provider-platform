from fastapi import APIRouter, Header, HTTPException, Request, Response
from infrastructure.governance.publication import PublicationNotFound
router=APIRouter(prefix="/datasets",tags=["datasets"] )
@router.get("")
def list_datasets(request:Request):
    return {"items":[item.to_public_dict() for item in request.app.state.publication_service.list_public()],"count":len(request.app.state.publication_service.list_public())}
@router.get("/{publication_id}")
def get_dataset(publication_id:str,request:Request,response:Response,if_none_match:str|None=Header(default=None)):
    try: item=request.app.state.publication_service.get_public(publication_id)
    except PublicationNotFound as exc: raise HTTPException(status_code=404,detail={"code":"PUBLICATION_NOT_FOUND","message":str(exc)}) from exc
    response.headers["etag"]=item.etag
    response.headers["cache-control"]=item.cache_control
    if if_none_match==item.etag: response.status_code=304; return None
    return item.to_public_dict()
