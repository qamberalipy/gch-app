# app/model_invoice/model_invoice.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.model_invoice import schema, service
from app.user.models import User, UserRole
import app.user.user as _user_auth
from app.Shared.dependencies import get_db

router = APIRouter()

def get_admin_user(current_user: User = Depends(_user_auth.get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized. Admin access required."
        )
    return current_user

@router.post("/", response_model=schema.InvoiceResponse)
def create_invoice(
    invoice: schema.InvoiceCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new invoice record"""
    # Verify user exists
    target_user = db.query(User).filter(User.id == invoice.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return service.create_invoice(db=db, invoice=invoice)

@router.get("/", response_model=schema.InvoicePaginatedResponse)
def read_invoices(
    user_id: Optional[int] = Query(None, description="Filter by Creator ID"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Fetch paginated invoices"""
    skip = (page - 1) * size
    items, total = service.get_invoices(
        db=db, 
        user_id=user_id, 
        from_date=from_date, 
        to_date=to_date, 
        skip=skip, 
        limit=size
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@router.put("/{invoice_id}", response_model=schema.InvoiceResponse)
def update_invoice(
    invoice_id: int, 
    invoice_update: schema.InvoiceUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    updated_invoice = service.update_invoice(db, invoice_id, invoice_update)
    if not updated_invoice:
        raise HTTPException(status_code=404, detail="Invoice record not found")
    return updated_invoice

@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    success = service.delete_invoice(db, invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice record not found")
    return None