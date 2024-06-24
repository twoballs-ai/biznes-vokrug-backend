from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from madsoft import crud, schemas
from madsoft.database import SessionLocal, get_db
from madsoft.minio import delete_object, download_file, upload_image
import urllib.parse

router = APIRouter()

@router.get("/", response_model=List[schemas.Meme])
def read_memes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    memes = crud.get_memes(db, skip=skip, limit=limit)
    for meme in memes:
        if meme.image_url:
            meme.download_url = f"http://localhost:8001/memes/{meme.id}/download"
    return memes

@router.get("/{meme_id}", response_model=schemas.Meme)
def read_meme(meme_id: int, db: Session = Depends(get_db)):
    db_meme = crud.get_meme(db, meme_id=meme_id)
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Мем не найден")
    if db_meme.image_url:
        db_meme.download_url = f"http://localhost:8001/memes/{meme_id}/download"
    return db_meme

@router.post("/", response_model=schemas.Meme)
async def create_new_meme(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_data = await file.read()
    try:
        image_url = upload_image(file.filename, file_data, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    meme_data = schemas.MemeCreate(title=title, description=description, image_url=image_url)
    return crud.create_meme(db=db, meme=meme_data)

@router.put("/{meme_id}", response_model=schemas.Meme)
async def update_meme(
    meme_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    db_meme = crud.get_meme(db=db, meme_id=meme_id)
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Мем не найден")

    if title:
        db_meme.title = title
    if description:
        db_meme.description = description

    if file:
        try:
            file_data = await file.read()
            image_url = upload_image(file.filename, file_data, file.content_type)
            db_meme.image_url = image_url
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    db.refresh(db_meme)
    return db_meme

@router.delete("/{meme_id}", response_model=dict)
def delete_meme(meme_id: int, db: Session = Depends(get_db)):
    db_meme = crud.get_meme(db=db, meme_id=meme_id)
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Мем не найден")

    deleted_meme = crud.delete_meme(db=db, meme_id=meme_id)

    if db_meme.image_url:
        try:
            file_name = db_meme.image_url.split('/')[-1]
            delete_object(file_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

    return {"message": f"Мем с ID {meme_id} успешно удален"}

@router.get("/{meme_id}/download", response_class=Response)
def download_meme(meme_id: int, db: Session = Depends(get_db)):
    db_meme = crud.get_meme(db, meme_id=meme_id)
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Мем не найден")

    file_name = db_meme.image_url.split('/')[-1]
    file_data = download_file(file_name)
    
    encoded_file_name = urllib.parse.quote(file_name)

    response = StreamingResponse(
        iter([file_data.read()]), 
        media_type='application/octet-stream'
    )
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_file_name}"
    
    return response
