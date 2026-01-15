import datetime
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List, Optional

import app.signature.models as _models
import app.user.models as _user_models
import app.signature.schema as _schemas

# --- Utility: Get Request or 404 ---
def get_signature_request_or_404(db: Session, request_id: int):
    req = db.query(_models.SignatureRequest).options(
        joinedload(_models.SignatureRequest.requester),
        joinedload(_models.SignatureRequest.signer)
    ).filter(_models.SignatureRequest.id == request_id).first()
    
    if not req:
        raise HTTPException(status_code=404, detail=f"Signature request {request_id} not found")
    return req

# --- 1. Create Signature Request ---
def create_signature_request(db: Session, request_in: _schemas.SignatureCreate, current_user: _user_models.User):
    signer = db.query(_user_models.User).filter(
        _user_models.User.id == request_in.signer_id,
        _user_models.User.role == _user_models.UserRole.digital_creator,
        _user_models.User.is_deleted == False
    ).first()
    
    if not signer:
        raise HTTPException(status_code=400, detail="Invalid or Deleted Digital Creator.")

    # RBAC Hierarchy Check
    if current_user.role != _user_models.UserRole.admin:
        if current_user.role == _user_models.UserRole.team_member:
            if current_user.assigned_model_id != signer.id:
                raise HTTPException(status_code=403, detail="You can only request signatures from your assigned Digital Creator.")
        elif current_user.role == _user_models.UserRole.manager:
            if signer.manager_id != current_user.id:
                raise HTTPException(status_code=403, detail="You can only request signatures from creators in your team.")
        elif current_user.role == _user_models.UserRole.digital_creator:
             raise HTTPException(status_code=403, detail="Digital Creators cannot create signature requests.")

    try:
        new_request = _models.SignatureRequest(
            requester_id=current_user.id,
            signer_id=request_in.signer_id,
            title=request_in.title,
            description=request_in.description,
            document_url=request_in.document_url,
            deadline=request_in.deadline,
            status=_models.SignatureStatus.pending.value
        )

        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        return new_request

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# --- 2. List Signature Requests (UPDATED) ---
def get_all_signature_requests(
    db: Session, 
    current_user: _user_models.User, 
    skip: int = 0, 
    limit: int = 10, 
    status: Optional[str] = None,
    search: Optional[str] = None
):
    try:
        query = db.query(_models.SignatureRequest).options(
            joinedload(_models.SignatureRequest.requester),
            joinedload(_models.SignatureRequest.signer)
        )

        # RBAC Filtering
        if current_user.role == _user_models.UserRole.digital_creator:
            query = query.filter(_models.SignatureRequest.signer_id == current_user.id)
        
        elif current_user.role == _user_models.UserRole.manager:
            SignerUser = aliased(_user_models.User)
            query = query.join(SignerUser, _models.SignatureRequest.signer).filter(
                SignerUser.manager_id == current_user.id
            )
        
        elif current_user.role == _user_models.UserRole.team_member:
            if current_user.assigned_model_id:
                query = query.filter(_models.SignatureRequest.signer_id == current_user.assigned_model_id)
            else:
                return {"total": 0, "skip": skip, "limit": limit, "data": []}

        # Filtering & Search
        if status:
            query = query.filter(_models.SignatureRequest.status == status)
        
        if search:
            search_term = f"%{search}%"
            query = query.join(_models.SignatureRequest.signer).filter(
                or_(
                    _models.SignatureRequest.title.ilike(search_term),
                    _user_models.User.full_name.ilike(search_term)
                )
            )

        total_records = query.count()
        
        # Use skip/limit directly
        data = query.order_by(desc(_models.SignatureRequest.created_at))\
                    .offset(skip)\
                    .limit(limit)\
                    .all()

        return {
            "total": total_records,
            "skip": skip,
            "limit": limit,
            "data": data 
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# --- 3. Get Single Request ---
def get_signature_request(db: Session, request_id: int, current_user: _user_models.User):
    req = get_signature_request_or_404(db, request_id)

    is_admin = current_user.role == _user_models.UserRole.admin
    is_requester = req.requester_id == current_user.id
    is_signer = req.signer_id == current_user.id
    
    has_hierarchy_access = False
    if current_user.role == _user_models.UserRole.manager and req.signer.manager_id == current_user.id:
        has_hierarchy_access = True
    if current_user.role == _user_models.UserRole.team_member and current_user.assigned_model_id == req.signer_id:
        has_hierarchy_access = True

    if not (is_admin or is_requester or is_signer or has_hierarchy_access):
        raise HTTPException(status_code=403, detail="Not authorized to view this document.")
    
    return req

# --- 4. Sign Document ---
def sign_document(db: Session, request_id: int, sign_in: _schemas.SignatureSign, current_user: _user_models.User, ip_address: str):
    req = get_signature_request_or_404(db, request_id)

    if req.signer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned Digital Creator can sign this document.")

    if req.status != _models.SignatureStatus.pending.value:
        raise HTTPException(status_code=400, detail="Document is already processed or expired.")

    try:
        req.signed_legal_name = sign_in.legal_name
        req.signed_at = datetime.datetime.utcnow()
        req.signer_ip_address = ip_address
        req.status = _models.SignatureStatus.signed.value

        db.commit()
        db.refresh(req)
        return req
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Signing failed: {str(e)}")

# --- 5. Update Request ---
def update_signature_request(db: Session, request_id: int, updates: _schemas.SignatureUpdate, current_user: _user_models.User):
    req = get_signature_request_or_404(db, request_id)
    
    if current_user.role != _user_models.UserRole.admin and req.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot edit this request.")

    if req.status == _models.SignatureStatus.signed.value:
         raise HTTPException(status_code=400, detail="Cannot edit a document that has already been signed.")

    try:
        update_data = updates.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(req, key, value)
        
        db.commit()
        db.refresh(req)
        return req
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

# --- 6. Delete Request ---
def delete_signature_request(db: Session, request_id: int, current_user: _user_models.User):
    req = get_signature_request_or_404(db, request_id)
    
    if current_user.role != _user_models.UserRole.admin and req.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot delete this request.")
            
    if req.status == _models.SignatureStatus.signed.value:
         raise HTTPException(status_code=400, detail="Cannot delete a signed legal document.")

    try:
        db.delete(req)
        db.commit()
        return {"message": "Request deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")