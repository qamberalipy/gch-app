import pytest
from app.MealPlan.service import (
    create_meal_plan,
    get_meal_plan_by_id,
    get_meal_plans_by_org_id,
    update_meal_plan,
    delete_meal_plan,
    create_member_meal_plan,
    get_meal,
    create_meal,
    delete_meal
)
from app.MealPlan.schema import CreateMealPlan, UpdateMealPlan, MealPlanFilterParams, CreateMeal
from sqlalchemy.orm import Session
from app.MealPlan.models import MealPlan, Meal, MemberMealPlan
from app.Client.client import get_db

# Helper function to get a database session
def get_test_db():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_create_meal_plan():
    db = next(get_test_db())
    meal_plan_data = CreateMealPlan(
        name="Test Meal Plan",
        profile_img="test.jpg",
        visible_for="Staff of my gym",
        description="A test meal plan",
        meals=
        [
            {
            "meal_time": "breakfast",
            "food_id": 1,
            "quantity": 1
            }
        ],
        member_id= [50,51,51],
        org_id=9,
        carbs=100,
        protein=50,
        fats=20
    )
    user_id = 1
    persona = "staff"
    result = await create_meal_plan(meal_plan_data, user_id, persona, db)
    assert result is not None
    assert result.name == "Test Meal Plan"

@pytest.mark.asyncio
async def test_get_meal_plan_by_id():
    db = next(get_test_db())
    meal_plan_id = 4  # Make sure this ID exists in your test database
    result = await get_meal_plan_by_id(meal_plan_id, db)
    assert result is not None
    assert result.meal_plan_id == meal_plan_id

@pytest.mark.asyncio
async def test_get_meal_plans_by_org_id():
    db = next(get_test_db())
    org_id = 1  # Ensure this ID exists
    persona = "example_persona"
    params = MealPlanFilterParams(
        search_key="Test",
        visible_for="Members of my gym",
        created_by_me=1,
        food_id=[1],
        meal_time="breakfast",
        sort_key="created_at",
        sort_order="desc",
        offset=0,
        limit=10
    )
    result = await get_meal_plans_by_org_id(org_id, db, persona, params)
    assert result is not None
    assert "data" in result

@pytest.mark.asyncio
async def test_update_meal_plan():
    db = next(get_test_db())
    meal_plan_id = 1  # Ensure this ID exists
    user_id = 1
    update_data = UpdateMealPlan(
        name="Updated Meal Plan",
        description="Updated description",
        visible_for="Staff of my gym"
    )
    result = await update_meal_plan(meal_plan_id, user_id, update_data, db)
    assert result is not None
    assert result.name == "Updated Meal Plan"

@pytest.mark.asyncio
async def test_delete_meal_plan():
    db = next(get_test_db())
    meal_plan_id = 35 # Ensure this ID exists
    user_id = 1
    result = await delete_meal_plan(meal_plan_id, user_id, db)
    assert result is not None
    assert result.is_deleted == True

@pytest.mark.asyncio
async def test_create_member_meal_plan():
    db = next(get_test_db())
    meal_plan_id = 35  # Ensure this ID exists
    member_ids = [50, 51]  # Ensure these IDs exist
    result = await create_member_meal_plan(meal_plan_id, member_ids, db)
    assert result is not None
    assert len(result) == len(member_ids)

@pytest.mark.asyncio
async def test_get_meal():
    db = next(get_test_db())
    meal_id = 36  # Ensure this ID exists
    result = await get_meal(meal_id, db)
    assert result is not None
    assert result.id == meal_id

@pytest.mark.asyncio
async def test_create_meal():
    db = next(get_test_db())
    meal_plan_id = 35  # Ensure this ID exists
    meals = [
        CreateMeal(
            meal_time="breakfast",
            food_id=1,
            quantity=2
        )
    ]
    result = await create_meal(meal_plan_id, meals, db)
    assert result is not None
    assert len(result) == len(meals)

@pytest.mark.asyncio
async def test_delete_meal():
    db = next(get_test_db())
    meal_id = 36  # Ensure this ID exists
    result = await delete_meal(meal_id, db)
    assert result is not None
    assert result.is_deleted == True
