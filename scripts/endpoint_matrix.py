"""Endpoint matrix generator and security audit tool for Mediate backend."""

import inspect
import os
import re
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.routing import APIRoute
from app.main import app


def get_permission_code_from_dependant(dependant: Any) -> str | None:
    """Recursively search for require_permission in dependencies."""
    if not dependant:
        return None

    for dep in dependant.dependencies:
        call = getattr(dep, "call", None)
        if call:
            closure = getattr(call, "__closure__", None)
            if closure:
                for cell in closure:
                    try:
                        val = cell.cell_contents
                        if isinstance(val, str) and ":" in val:
                            return val
                    except Exception:
                        pass
        code = get_permission_code_from_dependant(dep)
        if code:
            return code
    return None


def is_auth_required(dependant: Any) -> bool:
    """Check if get_current_user or require_permission is in the dependency tree."""
    if not dependant:
        return False

    for dep in dependant.dependencies:
        call = getattr(dep, "call", None)
        if call:
            call_name = getattr(call, "__name__", "")
            call_module = getattr(call, "__module__", "")
            if "get_current_user" in call_name or "require_permission" in call_name or "_dependency" in call_name:
                return True
            if "dependencies" in call_module:
                return True
        if is_auth_required(dep):
            return True
    return False


def uses_scope_helper(endpoint: Any) -> bool:
    """Check if endpoint implementation or its service references core/scope.py."""
    try:
        source = inspect.getsource(endpoint)
        if "scope" in source or "get_accessible_user_ids" in source or "get_user_scope_context" in source:
            return True
    except Exception:
        pass

    try:
        mod = inspect.getmodule(endpoint)
        if mod and mod.__file__:
            service_path = Path(mod.__file__).parent / "service.py"
            if service_path.exists():
                srv_text = service_path.read_text(encoding="utf-8")
                endpoint_name = endpoint.__name__
                # Find endpoint call in service
                if "scope" in srv_text or "get_accessible_user_ids" in srv_text or "get_user_scope_context" in srv_text:
                    return True
    except Exception:
        pass

    return False


def is_paginated(route: APIRoute) -> bool:
    """Check if route accepts pagination params or returns a paginated schema."""
    param_names = [param.name for param in route.dependant.query_params]
    if "page" in param_names and ("page_size" in param_names or "limit" in param_names):
        return True
    if "skip" in param_names and "limit" in param_names:
        return True

    if route.response_model:
        model_name = getattr(route.response_model, "__name__", str(route.response_model))
        if "ListResponse" in model_name or "Page" in model_name:
            return True
    return False


def find_test_coverage(path: str, method: str, tests_dir: Path) -> list[str]:
    """Find which test files contain references to this path."""
    matching_tests = []
    # Search in all test_*.py files
    for test_file in tests_dir.glob("test_*.py"):
        try:
            content = test_file.read_text(encoding="utf-8")
            # Match path
            if path in content:
                matching_tests.append(test_file.name)
            else:
                # Try relative path e.g. without /api/v1
                stripped = path.replace("/api/v1", "")
                if stripped and stripped in content:
                    matching_tests.append(test_file.name)
        except Exception:
            pass
    return sorted(list(set(matching_tests)))


def collect_routes() -> list[tuple[str, APIRoute]]:
    """Recursively collect all APIRoutes with their prefixes."""
    collected = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            collected.append((r.path, r))
        elif hasattr(r, "original_router"):
            ctx = getattr(r, "include_context", None)
            prefix = ctx.prefix if ctx else ""
            for sub in r.original_router.routes:
                if isinstance(sub, APIRoute):
                    collected.append((prefix + sub.path, sub))
    return collected


def generate_matrix() -> list[dict[str, Any]]:
    """Generate the full endpoint matrix."""
    tests_dir = BASE_DIR / "tests"
    routes_list = collect_routes()

    routes_data = []

    for path, route in routes_list:
        methods = sorted(list(route.methods - {"HEAD", "OPTIONS"}))
        for method in methods:
            auth_req = is_auth_required(route.dependant)
            perm_code = get_permission_code_from_dependant(route.dependant)
            scope_used = uses_scope_helper(route.endpoint)
            paginated = is_paginated(route)
            resp_model = (
                getattr(route.response_model, "__name__", str(route.response_model))
                if route.response_model
                else "None"
            )
            tests = find_test_coverage(path, method, tests_dir)

            routes_data.append({
                "method": method,
                "path": path,
                "auth_required": auth_req,
                "permission_code": perm_code,
                "uses_scope": scope_used,
                "response_model": resp_model,
                "paginated": paginated,
                "has_tests": len(tests) > 0,
                "test_files": tests,
                "endpoint_name": route.endpoint.__name__,
            })

    # Sort routes by path then method
    routes_data.sort(key=lambda x: (x["path"], x["method"]))
    return routes_data


if __name__ == "__main__":
    matrix = generate_matrix()
    print(f"Total endpoints registered: {len(matrix)}")

    print("\n| Method | Path | Auth Req | Permission | Uses Scope | Response Model | Paginated | Tested | Test Files |")
    print("|---|---|:---:|---|:---:|---|:---:|:---:|---|")
    for r in matrix:
        perm = r["permission_code"] or "-"
        tests_str = ", ".join(r["test_files"]) if r["test_files"] else "-"
        print(
            f"| {r['method']} | `{r['path']}` | {'Yes' if r['auth_required'] else '**NO**'} | "
            f"`{perm}` | {'Yes' if r['uses_scope'] else 'No'} | `{r['response_model']}` | "
            f"{'Yes' if r['paginated'] else 'No'} | {'Yes' if r['has_tests'] else '**NO**'} | {tests_str} |"
        )

    # Security check: unauthenticated routes
    public_whitelist = {
        "/health",
        "/ready",
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/config",
    }

    print("\n--- CRITICAL P0: UNAUTHENTICATED ROUTES ---")
    for r in matrix:
        if not r["auth_required"]:
            if r["path"] not in public_whitelist:
                print(f"P0: Route `{r['method']} {r['path']}` has NO authentication!")

    print("\n--- P2: ROUTES MISSING RESPONSE_MODEL ---")
    for r in matrix:
        if r["response_model"] == "None":
            print(f"P2: Route `{r['method']} {r['path']}` has NO response_model!")

    print("\n--- UNTESTED ROUTES ---")
    untested = [r for r in matrix if not r["has_tests"]]
    print(f"Total untested routes: {len(untested)}")
    for r in untested:
        print(f"Untested: `{r['method']} {r['path']}`")
