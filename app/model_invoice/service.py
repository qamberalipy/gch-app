# app/invoice/service.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date
from typing import Optional, List
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
    limit: int = 100
):
    query = db.query(ModelInvoice)

    if user_id:
        query = query.filter(ModelInvoice.user_id == user_id)
    
    if from_date:
        query = query.filter(ModelInvoice.invoice_date >= from_date)
        
    if to_date:
        query = query.filter(ModelInvoice.invoice_date <= to_date)

    return query.order_by(desc(ModelInvoice.invoice_date)).offset(skip).limit(limit).all()

def get_invoice_by_id(db: Session, invoice_id: int):
    return db.query(ModelInvoice).filter(ModelInvoice.id == invoice_id).first()

def update_invoice(db: Session, invoice_id: int, invoice_update: InvoiceUpdate):
    db_invoice = get_invoice_by_id(db, invoice_id)
    if not db_invoice:
        return None
    
    update_data = invoice_update.dict(exclude_unset=True)
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