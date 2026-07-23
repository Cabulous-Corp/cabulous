"""Custom filter backends with OpenAPI schema support for DRF 3.16.

django-filter 26.1 removed the ``get_schema_operation_parameters`` method
that DRF's ``AutoSchema`` calls during schema generation. This module
provides a drop-in replacement that re-implements it.
"""

from __future__ import annotations

from typing import Any

from django_filters.rest_framework import DjangoFilterBackend as _DjangoFilterBackend


class DjangoFilterBackend(_DjangoFilterBackend):
    """DjangoFilterBackend with ``get_schema_operation_parameters`` support."""

    def get_schema_operation_parameters(self, view: Any) -> list[dict[str, Any]]:
        """Return OpenAPI parameters for the view's filterset fields."""
        filterset_class = self.get_filterset_class(view)
        if filterset_class is None:
            return []

        parameters: list[dict[str, Any]] = []
        for field_name, filter_field in filterset_class.base_filters.items():
            field = filter_field.field
            param: dict[str, Any] = {
                "name": field_name,
                "in": "query",
                "required": field.required,
                "schema": {"type": _map_field_type(field.__class__.__name__)},
            }
            if field.help_text:
                param["description"] = field.help_text
            parameters.append(param)

        return parameters


def _map_field_type(field_class_name: str) -> str:
    """Map a Django form field class name to an OpenAPI type string."""
    mapping = {
        "DateField": "string",
        "DateTimeField": "string",
        "UUIDField": "string",
        "CharField": "string",
        "IntegerField": "integer",
        "FloatField": "number",
        "BooleanField": "boolean",
        "ChoiceField": "string",
        "TypedChoiceField": "string",
        "NullBooleanField": "boolean",
        "DecimalField": "number",
    }
    return mapping.get(field_class_name, "string")
