from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.jar import JarInfo
from app.services import jar_service

router = APIRouter(prefix="/jars", tags=["jars"])


@router.get("", response_model=list[JarInfo])
async def list_jars(_: User = Depends(get_current_user)):
    return jar_service.list_jars()


@router.post("/upload", response_model=JarInfo)
async def upload_jar(
    file: UploadFile = File(...),
    _: User = Depends(require_role("admin")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    try:
        return await jar_service.save_jar(file.filename, await file.read())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-batch", response_model=list[JarInfo])
async def upload_jars(
    files: list[UploadFile] = File(...),
    _: User = Depends(require_role("admin")),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files")

    uploaded: list[dict] = []
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        try:
            uploaded.append(await jar_service.save_jar(file.filename, await file.read()))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"{file.filename}: {e}") from e
    return uploaded


@router.delete("/{filename}")
async def delete_jar(
    filename: str,
    _: User = Depends(require_role("admin")),
):
    try:
        jar_service.delete_jar(filename)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
