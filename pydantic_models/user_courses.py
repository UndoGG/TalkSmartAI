from pydantic import BaseModel


class UserCourse(BaseModel):
    id: int
    user_id: int
    course_name: str


class UserCourseForm(BaseModel):
    user_id: int
    course_name: str
