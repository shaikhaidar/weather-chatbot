"""
MCP Server — Standard MCP SDK server exposing weatherBOT tools.
Runs as a separate SSE/stdio process that can be consumed by any MCP client
(Claude Desktop, custom tooling, etc.)

Start this server with:
    python mcp_server.py
"""
from mcp.server.fastmcp import FastMCP
from services.iot_service import IoTService
from services.gnn_service import GNNService
from services.graph_service import GraphService
from services.nlg_service import NLGService
from engines.nlp_engine import NLPEngine
from engines.explainable_ai_engine import ExplainableAIEngine
from engines.recommendation_engine import RecommendationEngine
from utils.logger import logger
import json

# Create the MCP server
mcp = FastMCP("weatherBOT")


# ─── IoT Tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def get_iot_reading() -> str:
    """Get the current live sensor reading from the weather station (Raspberry Pi or simulator)."""
    reading = IoTService.get_reading()
    return NLGService.describe_iot_reading(reading)


@mcp.tool()
def get_iot_status() -> str:
    """Check the connection status of the IoT weather station."""
    status = IoTService.get_status()
    source = status.get("source", "simulator")
    connected = status.get("connected", False)
    return (
        f"Weather Station Status:\n"
        f"- Connected: {connected}\n"
        f"- Source: {source}\n"
        f"- Last reading at: {status.get('last_reading_at', 'N/A')}\n"
        f"- Serial available: {status.get('serial_available', False)}\n"
        f"- MQTT available: {status.get('mqtt_available', False)}"
    )


@mcp.tool()
def connect_raspberry_pi_serial(port: str = "COM3", baud_rate: int = 9600) -> str:
    """
    Connect to a Raspberry Pi weather station via USB serial/UART.
    Args:
        port: Serial port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)
        baud_rate: Baud rate (default 9600)
    """
    result = IoTService.connect_serial(port, baud_rate)
    return f"Serial connection: {result['status']} on {port} @ {baud_rate} baud"


@mcp.tool()
def connect_mqtt_broker(host: str = "192.168.1.100", port: int = 1883) -> str:
    """
    Connect to an MQTT broker for wireless sensor data from Raspberry Pi.
    Args:
        host: MQTT broker IP address (e.g., Raspberry Pi's IP)
        port: MQTT port (default 1883)
    """
    result = IoTService.connect_mqtt(host, port)
    return f"MQTT connection: {result['status']} to {host}:{port}"


# ─── GNN / Prediction Tools ───────────────────────────────────────────────────

@mcp.tool()
def run_gnn_spatial_prediction() -> str:
    """Run a Graph Neural Network prediction on current live sensor readings from all weather stations."""
    readings = IoTService.get_multi_node_readings(3)
    nodes = GNNService.build_nodes_from_iot(readings)
    edges = GNNService.build_edges(len(nodes))
    result = GNNService.predict(nodes, edges)
    return NLGService.describe_prediction(result)


# ─── Analysis Tools ───────────────────────────────────────────────────────────

@mcp.tool()
def analyze_text_intent(message: str) -> str:
    """
    Analyze a user message and classify its intent plus extract weather-related entities.
    Args:
        message: The user's natural language message
    """
    result = NLPEngine.process(message)
    entities = result.get("entities", {})
    return (
        f"Intent: {result['intent']}\n"
        f"Sensors mentioned: {entities.get('sensors', [])}\n"
        f"Metrics mentioned: {entities.get('metrics', [])}\n"
        f"Time range: {entities.get('time_range')}\n"
        f"Location: {entities.get('location')}"
    )


@mcp.tool()
def get_recommendations(intent: str = "GENERAL_CHAT") -> str:
    """
    Get follow-up query recommendations based on the current intent.
    Args:
        intent: Current NLP intent (GREETING, DATA_QUERY, PREDICTION_REQUEST, etc.)
    """
    recs = RecommendationEngine.get_recommendations(intent)
    return NLGService.describe_recommendations(recs)


# ─── Resource: Live Sensor Data ───────────────────────────────────────────────

@mcp.resource("weather://station/live")
def live_sensor_data() -> str:
    """Live sensor data resource from the weather station."""
    reading = IoTService.get_reading()
    return json.dumps(reading, indent=2)


@mcp.resource("weather://station/status")
def station_status() -> str:
    """Weather station connection status resource."""
    return json.dumps(IoTService.get_status(), indent=2)


# ─── Prompts ──────────────────────────────────────────────────────────────────

@mcp.prompt()
def weather_analysis_prompt(sensor: str = "temperature") -> str:
    """Generate a prompt for analyzing a specific weather sensor reading."""
    reading = IoTService.get_reading()
    val = reading.get(sensor, "N/A")
    return (
        f"Analyze the following {sensor} reading from the weather station: {val}. "
        f"Provide insights about whether this is within normal range, "
        f"possible causes, and recommended actions."
    )


if __name__ == "__main__":
    logger.info("Starting weatherBOT MCP Server (standard MCP SDK)...")
    mcp.run()
