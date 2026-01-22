# app/model_invoice/service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import date
from typing import Optional, Tuple, List
from .models import ModelInvoice
from .schema import InvoiceCreate, InvoiceUpdate

def create_invoice(db: Session, invoice: InvoiceCreate):
    db_invoice = ModelInvoice(
        user_id=invoice.user_id,
        invoice_date=invoice.invoice_date,
        subscription=invoice.subscription,
        tips=invoice.tips,
        posts=invoice.posts,
        messages=invoice.messages,
        referrals=invoice.referrals,
        streams=invoice.streams,
        others=invoice.others
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_invoices(
    db: Session, 
    user_id: Optional[int] = None, 
    from_date: Optional[date] = None, 
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[ModelInvoice], int]:
    
    query = db.query(ModelInvoice)

    if user_id:
        query = query.filter(ModelInvoice.user_id == user_id)
    
    if from_date:
        query = query.filter(ModelInvoice.invoice_date >= from_date)
        
    if to_date:
        query = query.filter(ModelInvoice.invoice_date <= to_date)

    # 1. Get Total Count
    total_count = query.count()

    # 2. Get Paginated Items (with eager loading for User to prevent lag)
    items = query.options(joinedload(ModelInvoice.user))\
                 .order_by(desc(ModelInvoice.invoice_date))\
                 .offset(skip)\
                 .limit(limit)\
                 .all()

    return items, total_count

def get_invoice_by_id(db: Session, invoice_id: int):
    return db.query(ModelInvoice).filter(ModelInvoice.id == invoice_id).first()

def update_invoice(db: Session, invoice_id: int, invoice_update: InvoiceUpdate):
    db_invoice = get_invoice_by_id(db, invoice_id)
    if not db_invoice:
        return None
    
    update_data = invoice_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_invoice, key, value)
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def delete_invoice(db: Session, invoice_id: int):
    db_invoice = get_invoice_by_id(db, invoice_id)
    if db_invoice:
        db.delete(db_invoice)
        db.commit()
        return True
    return False