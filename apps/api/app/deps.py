"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException

from app.models.schemas import ProjectOut
from app.services import storage


def get_project_or_404(project_id: str) -> ProjectOut:
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


ProjectDep = Annotated[ProjectOut, Depends(get_project_or_404)]
