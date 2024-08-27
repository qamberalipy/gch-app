import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.core.db.session import SessionLocal
from app.Exercise.service import (
    create_exercise, get_muscle, get_met, 
    get_category, exercise_update, delete_exercise,
    get_equipments, get_primary_joints, get_exercise
)
from app.Exercise.schema import ExerciseCreate, ExerciseUpdate
from app.Exercise.models import Exercise

client = TestClient(app)

# Fixture to initialize the database session
@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fixture to create sample exercise data in the database
@pytest.fixture
def sample_exercise(db: Session):
    exercise_data = ExerciseCreate(
        exercise_name="Push Up",
        visible_for=["public"],
        org_id=1,
        category_id=1,
        exercise_intensity="High",
        intensity_value=5,
        exercise_type="Strength",
        difficulty="Intermediate",
        sets=3,
        seconds_per_set=60,
        repetitions_per_set=15,
        rest_between_set=30,
        distance=0,
        speed=0,
        met_id=1,
        gif_url="http://example.com/pushup.gif",
        video_url_male="http://example.com/pushup_male.mp4",
        video_url_female="http://example.com/pushup_female.mp4",
        thumbnail_male="http://example.com/pushup_male_thumb.jpg",
        thumbnail_female="http://example.com/pushup_female_thumb.jpg",
        image_url_female="http://example.com/pushup_female_image.jpg",
        image_url_male="http://example.com/pushup_male_image.jpg"
    )
    exercise_id = create_exercise(db=db, exercise=exercise_data, user_id=1, user_type="admin")
    return {"id": exercise_id, **exercise_data.dict()}

# Test create exercise
def test_create_exercise(db: Session):
    exercise_data = ExerciseCreate(
        exercise_name="Squat",
        visible_for=["Everyone in My Gym"],  # Adjusted to expected values
        org_id=1,
        category_id=1,
        exercise_intensity="Max Intensity",  # Adjusted to expected values
        intensity_value=3,
        exercise_type="Repetition Based",  # Adjusted to expected values
        difficulty="Beginner",
        sets=4,
        seconds_per_set=45,
        repetitions_per_set=12,
        rest_between_set=20,
        distance=0,
        speed=0,
        met_id=2,
        gif_url="http://example.com/squat.gif",
        video_url_male="http://example.com/squat_male.mp4",
        video_url_female="http://example.com/squat_female.mp4",
        thumbnail_male="http://example.com/squat_male_thumb.jpg",
        thumbnail_female="http://example.com/squat_female_thumb.jpg",
        image_url_female="http://example.com/squat_female_image.jpg",
        image_url_male="http://example.com/squat_male_image.jpg"
    )
    response = client.post("/exercises/", json=exercise_data.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["exercise_name"] == exercise_data.exercise_name

# Test update exercise
def test_update_exercise(db: Session, sample_exercise):
    update_data = ExerciseUpdate(
        id=sample_exercise["id"],
        exercise_name="Modified Push Up",
        visible_for=["Everyone in My Gym"],
        org_id=1,
        category_id=1,
        exercise_intensity="Medium",
        intensity_value=4,
        exercise_type="Strength",
        difficulty="Advanced",
        sets=4,
        seconds_per_set=45,
        repetitions_per_set=12,
        rest_between_set=30,
        distance=0,
        speed=0,
        met_id=1,
        gif_url="http://example.com/modified_pushup.gif",
        video_url_male="http://example.com/modified_pushup_male.mp4",
        video_url_female="http://example.com/modified_pushup_female.mp4",
        thumbnail_male="http://example.com/modified_pushup_male_thumb.jpg",
        thumbnail_female="http://example.com/modified_pushup_female_thumb.jpg",
        image_url_female="http://example.com/modified_pushup_female_image.jpg",
        image_url_male="http://example.com/modified_pushup_male_image.jpg"
    )
    response = client.put(f"/exercises/{sample_exercise['id']}", json=update_data.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["exercise_name"] == update_data.exercise_name

    invalid_update = ExerciseUpdate(id=9999, exercise_name="Invalid Update")
    response = client.put(f"/exercises/{9999}", json=invalid_update.dict())
    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}

# Test delete exercise
def test_delete_exercise(db: Session, sample_exercise):
    response = client.delete(f"/exercises/{sample_exercise['id']}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Exercise deleted successfully"}

    get_response = client.get(f"/exercises/{sample_exercise['id']}")
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Exercise not found"}

    response = client.delete("/exercises/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}

# Test get equipments
def test_get_equipments(db: Session):
    response = client.get("/equipments/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test get primary joints
def test_get_primary_joints(db: Session):
    response = client.get("/primary-joints/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test get exercises with filters
def test_get_exercise(db: Session, sample_exercise):
    response = client.get("/exercises/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0

    response = client.get("/exercises/", params={"search_key": "Push Up"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert data["data"][0]["exercise_name"] == "Push Up"

    response = client.get("/exercises/", params={"search_key": "Nonexistent Exercise"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0
