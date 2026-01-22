# app/web/routers/invoice_views.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.db.session import SessionLocal
from app.model_invoice import schema, service
from app.user.models import User, UserRole
import app.user.user as _user_auth

# Imports for dependencies (Adjust based on your app/Shared/dependencies.py)
from app.Shared.dependencies import get_db
router = APIRouter(
    prefix="/invoices", 
    tags=["Model Invoicing"]
)

def get_admin_user(current_user: User = Depends(_user_auth.get_current_user)):
    """Ensure the user is an Admin."""
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
    """
    Admin: Add a new revenue record for a digital creator.
    """
    # Optional: Verify the target user exists and is a digital creator
    target_user = db.query(User).filter(User.id == invoice.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return service.create_invoice(db=db, invoice=invoice)

@router.get("/", response_model=List[schema.InvoiceResponse])
def read_invoices(
    user_id: Optional[int] = Query(None, description="Filter by Digital Creator ID"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Admin: Fetch invoices. Can filter by User, and Date Range (To/From).
    """
    return service.get_invoices(
        db=db, 
        user_id=user_id, 
        from_date=from_date, 
        to_date=to_date, 
        skip=skip, 
        limit=limit
    )

@router.put("/{invoice_id}", response_model=schema.InvoiceResponse)
def update_invoice(
    invoice_id: int, 
    invoice_update: schema.InvoiceUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Admin: Edit an existing invoice record.
    """
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
    """
    Admin: Delete an invoice record.
    """
    success = service.delete_invoice(db, invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice record not found")
    return None