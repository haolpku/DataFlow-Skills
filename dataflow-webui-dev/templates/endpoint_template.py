"""
DataFlow WebUI 后端端点模板
用法：复制此文件到 backend/app/api/v1/endpoints/{feature}.py，替换 Feature/feature 占位符
"""
import copy
import os
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.core.container import container
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

from app.schemas.feature import (
    FeatureSchema,
    FeatureCreateSchema,
    FeatureUpdateSchema,
)

router = APIRouter(tags=["feature"])


# ─── LIST ────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=ApiResponse[List[FeatureSchema]],
    operation_id="list_features",
    summary="获取所有 Feature 实例"
)
def list_features():
    try:
        all_items = container.feature_registry._get_all() or {}
        result = []
        for k, v in all_items.items():
            v_copy = copy.deepcopy(v)
            v_copy["id"] = k
            result.append(v_copy)
        return ok(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET BY ID ───────────────────────────────────────────────────────────────

@router.get(
    "/{id}",
    response_model=ApiResponse[FeatureSchema],
    operation_id="get_feature",
    summary="获取指定 Feature 实例"
)
def get_feature(id: str):
    try:
        item = container.feature_registry._get(id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Feature {id} not found")
        return ok(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── CREATE ──────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ApiResponse[Dict[str, str]],
    operation_id="create_feature",
    summary="创建新 Feature 实例"
)
def create_feature(body: FeatureCreateSchema):
    try:
        new_id = container.feature_registry._set(
            name=body.name,
            # ...其他字段
        )
        return ok({"id": new_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── UPDATE ──────────────────────────────────────────────────────────────────

@router.put(
    "/{id}",
    response_model=ApiResponse[Dict[str, str]],
    operation_id="update_feature",
    summary="更新 Feature 实例"
)
def update_feature(id: str, body: FeatureUpdateSchema):
    try:
        success = container.feature_registry._update(id, **body.model_dump(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail=f"Feature {id} not found")
        return ok({"id": id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── DELETE ──────────────────────────────────────────────────────────────────

@router.delete(
    "/{id}",
    response_model=ApiResponse[Dict[str, str]],
    operation_id="delete_feature",
    summary="删除 Feature 实例"
)
def delete_feature(id: str):
    try:
        success = container.feature_registry._delete(id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Feature {id} not found")
        return ok({"id": id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
