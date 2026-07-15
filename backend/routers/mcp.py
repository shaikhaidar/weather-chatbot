"""
MCP Router endpoint — /api/mcp/...
Exposes the MCP Service Router via HTTP REST for the frontend.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any, Dict
from database import get_db
from services.mcp_router import MCPRouter

router = APIRouter()


@router.post("/route")
def route_request(request: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Route a request through the MCP Service Router.
    Body: {"service": "iot|gnn|csv|graph|history|nlp|xai|research|model|dataset",
           "action": "<action>", "params": {...}}
    """
    return MCPRouter.route(request, db)


@router.get("/tools")
def list_tools() -> Dict[str, Any]:
    """List all available MCP tools/services and their actions."""
    tools = MCPRouter.list_tools()
    return {
        "mcp_version": "1.28.1",
        "server": "weatherBOT MCP Server",
        "description": "Edge AI Weather Intelligence Platform — MCP Service Router",
        "services": tools,
        "total_tools": sum(len(v) for v in tools.values()),
    }


@router.get("/iot/status")
def iot_status() -> Dict[str, Any]:
    """Quick shortcut: current IoT weather station status."""
    from services.iot_service import IoTService
    return IoTService.get_status()


@router.get("/iot/reading")
def iot_reading() -> Dict[str, Any]:
    """Quick shortcut: current sensor reading."""
    from services.iot_service import IoTService
    return IoTService.get_reading()


@router.post("/iot/connect/serial")
def connect_serial(port: str = "COM3", baud: int = 9600) -> Dict[str, Any]:
    """Connect to Raspberry Pi via USB serial."""
    from services.iot_service import IoTService
    return IoTService.connect_serial(port, baud)


@router.post("/iot/connect/mqtt")
def connect_mqtt(host: str = "192.168.1.100", port: int = 1883) -> Dict[str, Any]:
    """Connect to Raspberry Pi via MQTT broker."""
    from services.iot_service import IoTService
    return IoTService.connect_mqtt(host, port)
