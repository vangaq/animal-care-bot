from datetime import datetime
from typing import Any, Dict

def make_response_ok(data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "data": data}

def make_response_error(error_msg: str) -> Dict[str, Any]:
    return {"status": "error", "data": {}, "error_msg": error_msg}

def now_iso() -> str:
    return datetime.utcnow().isoformat()
