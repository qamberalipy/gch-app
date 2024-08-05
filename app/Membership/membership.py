from typing import Annotated, List
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Membership.schema as _schemas
import sqlalchemy.orm as _orm
import app.Membership.models as _models
import app.Membership.service as _services
import app.core.db.session as _database
import pika
import logging
import datetime
import app.Shared.helpers as _helpers
router = APIRouter()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.post("/membership_plan", response_model=_schemas.MembershipPlanRead, tags=["Membership Plans"])
def create_membership_plan(membership_plan: _schemas.MembershipPlanCreate,db: _orm.Session = Depends(get_db)):

    return _services.create_membership_plan(membership_plan, db)

@router.put("/membership_plan", response_model=_schemas.MembershipPlanRead, tags=["Membership Plans"])
def update_membership_plan(membership_plan: _schemas.MembershipPlanUpdate, db: _orm.Session = Depends(get_db)):
    
    db_membership_plan = _services.update_membership_plan(membership_plan.id, membership_plan,db)
    if db_membership_plan is None:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    return db_membership_plan

@router.delete("/membership_plan/{id}", tags=["Membership Plans"])
def delete_membership_plan(id:int,db: _orm.Session = Depends(get_db)):
    
    db_membership_plan = _services.delete_membership_plan(id,db)
    if db_membership_plan is None:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    return {
        "status_code": 200,
        "detail": "Membership plan deleted successfully"
    }

@router.get("/membership_plan/{id}", response_model=_schemas.MembershipPlanResponse, tags=["Membership Plans"])
def get_membership_plan_by_id(id: int, db: _orm.Session = Depends(get_db)):
    
    db_membership_plan = _services.get_membership_plan_by_id(id,db)
    if db_membership_plan is None:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    return db_membership_plan

def get_membership_filters(
    
    search_key: Annotated[str | None, Query(title="Search Key")] = None,
    group_id: Annotated[int, Query(description="Coach ID")] = None,
    income_category_id: Annotated[int, Query(description="Coach ID")] = None,
    discount_percentage: Annotated[int, Query(description="Coach ID")] = None,
    tax_rate: Annotated[int, Query(description="Coach ID")] = None,
    total_amount: Annotated[int, Query(description="Membership ID")] = None,
    status: Annotated[str | None, Query(title="status")] = None,
    sort_order: Annotated[str,Query(title="Sorting Order")] = 'desc',
    limit: Annotated[int, Query(description="Pagination Limit")] = None,
    offset: Annotated[int, Query(description="Pagination offset")] = None
):
    return _schemas.MembershipFilterParams(
        search_key=search_key,
        group_id=group_id,
        income_category_id=income_category_id,
        discount_percentage=discount_percentage,
        tax_rate=tax_rate,
        total_amount=total_amount,
        status=status,
        sort_order = sort_order,
        limit=limit,
        offset = offset
    )
   
@router.get("/membership_plan", response_model=List[_schemas.MembershipPlanResponse], tags=["Membership Plans"])
def get_membership_plans_by_org_id(
    org_id: int,
    filters: Annotated[_schemas.MembershipFilterParams, Depends(get_membership_filters)] = None,
    db: _orm.Session = Depends(get_db)
):
    
    membership_plans = _services.get_membership_plans_by_org_id(
        db,org_id,filters
    )
    return membership_plans

    
@router.post("/facilities", response_model=_schemas.FacilityRead, tags=["Facility APIs"])
def create_facility(facility: _schemas.FacilityCreate, db: _orm.Session = Depends(get_db)):
    try:    
        return _services.create_facility(facility, db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.put("/facilities", response_model=_schemas.FacilityRead, tags=["Facility APIs"])
def update_facility(facility: _schemas.FacilityUpdate, db: _orm.Session = Depends(get_db)):
    try:    
        db_facility = _services.update_facility(facility, db)
        if db_facility is None:
            raise HTTPException(status_code=404, detail="Facility not found")
        return db_facility
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.delete("/facilities/{id}", response_model=_schemas.FacilityRead, tags=["Facility APIs"])
def delete_facility(id:int, db: _orm.Session = Depends(get_db)):
    try:    
        db_facility = _services.delete_facility(id, db)
        if db_facility is None:
            raise HTTPException(status_code=404, detail="Facility not found")
        return db_facility
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

def get_filters(

    search_key: Annotated[str | None, Query(title="Search Key")] = None,
    sort_order: Annotated[str,Query(title="Sorting Order")] = 'desc',
    limit: Annotated[int, Query(description="Pagination Limit")] = None,
    offset: Annotated[int, Query(description="Pagination offset")] = None
):
    return _schemas.FacilityFilterParams(
        search_key=search_key,
        sort_order=sort_order,
        limit=limit,
        offset = offset
    )

@router.get("/facilities", response_model=List[_schemas.FacilityRead], tags=["Facility APIs"])
def get_facilitys_by_org_id(
    org_id: int,
    request: Request,
    filters: Annotated[_schemas.FacilityFilterParams, Depends(get_filters)], 
    db: _orm.Session = Depends(get_db)):
    try:    
        get_facility = _services.get_facility_by_org_id(org_id, filters, db)
        return get_facility
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
@router.get("/facilities/{id}", response_model=_schemas.FacilityRead, tags=["Facility APIs"])
def get_facility_by_id(id: int, db: _orm.Session = Depends(get_db)):
    try:    
        db_facility = _services.get_facility_by_id(id, db)
        if db_facility is None:
            raise HTTPException(status_code=404, detail="Facility not found")
        return db_facility
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
@router.post("/income_category", response_model=_schemas.IncomeCategoryRead, tags=["Income Category APIs"])
def create_income_category(income_category: _schemas.IncomeCategoryCreate, db: _orm.Session = Depends(get_db)):
    try:    
        return _services.create_income_category(income_category=income_category, db=db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
@router.get("/income_category", response_model=List[_schemas.IncomeCategoryRead], tags=["Income Category APIs"])
def get_all_income_categories(org_id: int, request: Request, db: _orm.Session = Depends(get_db)):
    try:    
        params = {
             "org_id": org_id,
            "search_key": request.query_params.get("search_key"),
            "sort_order": request.query_params.get("sort_order", "desc"),
            "limit": request.query_params.get("limit", 10),
            "offset": request.query_params.get("offset", 0)
        }
        
        income_categories = _services.get_all_income_categories_by_org_id(db, _schemas.StandardParams(**params))
        return income_categories
    
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.get("/income_category/{id}", response_model=_schemas.IncomeCategoryRead, tags=["Income Category APIs"])
def get_income_category(id: int, db: _orm.Session = Depends(get_db)):
    try:    
        db_income_category = _services.get_income_category_by_id(income_category_id=id, db=db)
        if db_income_category is None:
            raise HTTPException(status_code=404, detail="Income category not found")
        return db_income_category
    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.put("/income_category", response_model=_schemas.IncomeCategoryRead, tags=["Income Category APIs"])
def update_income_category(income_category: _schemas.IncomeCategoryUpdate, db: _orm.Session = Depends(get_db)):
    try:    
        db_income_category = _services.update_income_category(income_category=income_category, db=db)
        if db_income_category is None:
            raise HTTPException(status_code=404, detail="Income category not found")
        return db_income_category
    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.delete("/income_category/{id}", response_model=_schemas.IncomeCategoryRead, tags=["Income Category APIs"])
def delete_income_category(id:int, db: _orm.Session = Depends(get_db)):
    try:    
        db_income_category = _services.delete_income_category(income_category_id=id, db=db)
        if db_income_category is None:
            raise HTTPException(status_code=404, detail="Income category not found")
        return db_income_category  
    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
    
@router.post("/sale_taxes", response_model=_schemas.SaleTaxRead, tags=["Sale_tax APIs"])
def create_sale_tax(sale_tax: _schemas.SaleTaxCreate, db: _orm.Session = Depends(get_db)):
    try:    
        return _services.create_sale_tax(sale_tax=sale_tax,db=db)
    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    

@router.get("/sale_taxes", response_model=List[_schemas.SaleTaxRead], tags=["Sale_tax APIs"])
def get_all_sale_taxes(org_id: int, request: Request, db: _orm.Session = Depends(get_db)):
    try:    
        params = {
             "org_id": org_id,
            "search_key": request.query_params.get("search_key"),
            "sort_order": request.query_params.get("sort_order", "desc"),
            "limit": request.query_params.get("limit", 10),
            "offset": request.query_params.get("offset", 0)
        }
        
        sale_taxes = _services.get_all_sale_taxes_by_org_id(db, _schemas.StandardParams(**params))
        return sale_taxes
    
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


       

@router.get("/sale_taxes/{id}", response_model=_schemas.SaleTaxRead, tags=["Sale_tax APIs"])
def get_sale_tax(id: int, db: _orm.Session = Depends(get_db)):
    try:    
        db_sale_tax = _services.get_sale_tax_by_id(db=db, sale_tax_id=id)
        if db_sale_tax is None:
            raise HTTPException(status_code=404, detail="Sale tax not found")
        return db_sale_tax
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
    

@router.put("/sale_taxes", response_model=_schemas.SaleTaxRead, tags=["Sale_tax APIs"])
def update_sale_tax(sale_tax: _schemas.SaleTaxUpdate, db: _orm.Session = Depends(get_db)):
    
    try:    
        db_sale_tax = _services.update_sale_tax(sale_tax=sale_tax,db=db)
        if db_sale_tax is None:
            raise HTTPException(status_code=404, detail="Sale tax not found")
        return db_sale_tax
    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.delete("/sale_taxes/{id}", response_model=_schemas.SaleTaxRead, tags=["Sale_tax APIs"])
def delete_sale_tax(id:int, db: _orm.Session = Depends(get_db)):
    try:    
        db_sale_tax = _services.delete_sale_tax(sale_tax_id=id,db=db)
        if db_sale_tax is None:
            raise HTTPException(status_code=404, detail="Sale tax not found")
        return db_sale_tax
    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.post("/group",response_model=_schemas.GroupRead, tags=["Group API"])
def create_group(group:_schemas.GroupCreate,db: _orm.Session = Depends(get_db)): 
    try:    
        return _services.create_group(group=group,db=db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    


@router.get("/group/{id}",response_model=_schemas.GroupRead, tags=["Group API"])
def get_group(id:int,db: _orm.Session = Depends(get_db)):

    try:    
        return _services.get_group_by_id(id,db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
     

@router.get("/group", response_model=List[_schemas.GroupRead], tags=["Group API"])
def get_group(org_id: int, request: Request, db: _orm.Session = Depends(get_db)):
    try:    
        params = {
             "org_id": org_id,
            "search_key": request.query_params.get("search_key"),
            "sort_order": request.query_params.get("sort_order", "desc"),
            "limit": request.query_params.get("limit", 10),
            "offset": request.query_params.get("offset", 0)
        }
        
        groups = _services.get_all_groups_by_org_id(db, _schemas.StandardParams(**params))
        return groups
    
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.put("/group",response_model=_schemas.GroupRead, tags=["Group API"])
def update_group(group:_schemas.GroupUpdate,db: _orm.Session = Depends(get_db)):
    
    try:    
        db_group=_services.update_group(group,db)
        if db_group is None:
            raise HTTPException(status_code=404, detail="Group not found")
        return db_group    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.delete("/group/{id}",tags=["Group API"])
async def delete_group(id:int, db: _orm.Session = Depends(get_db)):
    db_group = await _services.delete_group(id,db)
    return db_group   

