"""
IoT Service — Raspberry Pi Weather Station Interface
Supports:
  - Real serial/USB connection (pyserial) to a Raspberry Pi sensor board
  - MQTT subscription for wireless sensor networks
  - Realistic simulator fallback when hardware is not connected
"""
import math
import random
import time
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from utils.logger import logger

# ── Graceful optional imports (hardware deps) ────────────────────────────────
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logger.warning("pyserial not installed – serial connection disabled.")

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not installed – MQTT connection disabled.")


# ── In-memory sensor state ────────────────────────────────────────────────────
_sensor_state: Dict[str, Any] = {
    "temperature": 24.0,         # BME280 (°C)
    "humidity": 60.0,            # BME280 (%)
    "pressure": 1013.25,         # BME280 (hPa)
    "pm1_0": 5.0,                # SPS30 (µg/m³)
    "pm2_5": 12.0,               # SPS30 (µg/m³)
    "pm4_0": 18.0,               # SPS30 (µg/m³)
    "pm10": 25.0,                # SPS30 (µg/m³)
    "rain_presence": 0,          # YL-83 (0 = No Rain, 1 = Rain)
    "rainfall": 0.0,             # Tipping Bucket (mm)
    "wind_speed": 5.0,           # Anemometer (m/s)
    "wind_direction": "N",       # Wind Vane (Cardinal direction)
    "light_intensity": 800.0,    # BH1750 (Lux)
    "lux": 800.0,                # BH1750 (Lux - Alias)
    "timestamp": datetime.utcnow().isoformat(),
    "source": "simulator",      # "serial" | "mqtt" | "simulator"
    "connected": False,
}

_lock = threading.Lock()


# ── Simulator ─────────────────────────────────────────────────────────────────
class WeatherSimulator:
    """
    Generates realistic weather readings using sinusoidal diurnal cycles
    plus configurable Gaussian noise — mirrors what a real RPi sensor board
    would stream over serial/MQTT.
    """
    _noise_level: float = 0.5   # σ multiplier (0 = perfect, 1 = noisy)
    _tick: int = 0

    @classmethod
    def configure(cls, noise_level: float) -> None:
        cls._noise_level = max(0.0, min(2.0, noise_level))

    @classmethod
    def next_reading(cls) -> Dict[str, Any]:
        cls._tick += 1
        t = cls._tick
        n = cls._noise_level

        base_temp = 22.0 + 6.0 * math.sin(t / 60.0)           # ~24-hr cycle
        temp = round(base_temp + random.gauss(0, 0.3 * n), 2)

        humidity = round(max(20, min(100, 58.0 - 0.4 * temp + random.gauss(0, 1.0 * n))), 2)
        pressure = round(1013.0 + 3.0 * math.sin(t / 120.0) + random.gauss(0, 0.5 * n), 2)
        wind_speed = round(max(0, abs(5.0 + 3.0 * math.sin(t / 30.0) + random.gauss(0, 0.5 * n))), 2)
        rainfall = round(max(0.0, random.gauss(0, 0.1 * n) if random.random() > 0.85 else 0.0), 3)
        light = round(max(0, 750.0 + 250.0 * math.sin(t / 50.0) + random.gauss(0, 20.0 * n)), 1)
        
        # New sensor metrics from the RPi project specs
        # Air Quality (SPS30) PM concentration
        base_pm25 = max(1.0, 12.0 + 5.0 * math.sin(t / 80.0) + random.gauss(0, 2.0 * n))
        pm2_5 = round(base_pm25, 2)
        pm1_0 = round(base_pm25 * 0.6 + random.uniform(0, 0.5), 2)
        pm4_0 = round(base_pm25 * 1.4 + random.uniform(0, 1.0), 2)
        pm10 = round(base_pm25 * 2.0 + random.uniform(0, 2.0), 2)
        
        # Rain Presence (YL-83 qualitative, 0 = No Rain, 1 = Rain)
        rain_presence = 1 if rainfall > 0 else 0
        
        # Wind Direction (Wind Vane Cardinal)
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        dir_idx = int((t // 5) % 8)
        wind_direction = directions[dir_idx]

        return {
            "temperature": temp,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "rainfall": rainfall,
            "light_intensity": light,
            "lux": light,
            "pm1_0": pm1_0,
            "pm2_5": pm2_5,
            "pm4_0": pm4_0,
            "pm10": pm10,
            "rain_presence": rain_presence,
            "wind_direction": wind_direction,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulator",
            "connected": False,
        }


# ── Serial (Raspberry Pi USB/UART) ────────────────────────────────────────────
class SerialWeatherReader:
    """
    Reads JSON lines from a Raspberry Pi over USB serial (e.g. /dev/ttyUSB0 or COM3).
    Expected payload format (sent by RPi):
        {"temperature": 23.1, "humidity": 61.2, "pressure": 1012.8,
         "wind_speed": 4.3, "rainfall": 0.0, "light_intensity": 720.0}
    """
    _serial: Optional[Any] = None
    _thread: Optional[threading.Thread] = None
    _running: bool = False

    @classmethod
    def connect(cls, port: str = "COM3", baud: int = 9600) -> bool:
        if not SERIAL_AVAILABLE:
            logger.error("pyserial not available.")
            return False
        try:
            cls._serial = serial.Serial(port, baud, timeout=2)
            cls._running = True
            cls._thread = threading.Thread(target=cls._read_loop, daemon=True)
            cls._thread.start()
            logger.info(f"Serial connected to {port} @ {baud} baud")
            return True
        except Exception as e:
            logger.error(f"Serial connection failed: {e}")
            return False

    @classmethod
    def _read_loop(cls) -> None:
        import json
        while cls._running and cls._serial and cls._serial.is_open:
            try:
                line = cls._serial.readline().decode("utf-8").strip()
                if line:
                    data = json.loads(line)
                    with _lock:
                        _sensor_state.update(data)
                        _sensor_state["source"] = "serial"
                        _sensor_state["connected"] = True
                        _sensor_state["timestamp"] = datetime.utcnow().isoformat()
            except Exception as e:
                logger.warning(f"Serial read error: {e}")
                time.sleep(0.5)

    @classmethod
    def disconnect(cls) -> None:
        cls._running = False
        if cls._serial and cls._serial.is_open:
            cls._serial.close()
        logger.info("Serial disconnected.")


# ── MQTT (Wireless sensor network) ───────────────────────────────────────────
class MQTTWeatherReader:
    """
    Subscribes to an MQTT broker (e.g. Mosquitto on the Pi) for sensor telemetry.
    Topic: weatherbot/station/sensors
    """
    _client: Optional[Any] = None

    @classmethod
    def connect(cls, host: str = "192.168.1.100", port: int = 1883,
                topic: str = "weatherbot/station/sensors") -> bool:
        if not MQTT_AVAILABLE:
            logger.error("paho-mqtt not available.")
            return False
        try:
            import json
            cls._client = mqtt.Client()

            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    client.subscribe(topic)
                    logger.info(f"MQTT connected to {host}:{port}, subscribed to {topic}")
                else:
                    logger.error(f"MQTT connection refused: rc={rc}")

            def on_message(client, userdata, msg):
                try:
                    data = json.loads(msg.payload.decode())
                    with _lock:
                        _sensor_state.update(data)
                        _sensor_state["source"] = "mqtt"
                        _sensor_state["connected"] = True
                        _sensor_state["timestamp"] = datetime.utcnow().isoformat()
                except Exception as e:
                    logger.warning(f"MQTT parse error: {e}")

            cls._client.on_connect = on_connect
            cls._client.on_message = on_message
            cls._client.connect_async(host, port, 60)
            cls._client.loop_start()
            return True
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False

    @classmethod
    def disconnect(cls) -> None:
        if cls._client:
            cls._client.loop_stop()
            cls._client.disconnect()
        logger.info("MQTT disconnected.")


# ── Public IoT Service API ────────────────────────────────────────────────────
class IoTService:
    """High-level service used by routers and MCP router."""

    @staticmethod
    def is_hardware_connected() -> bool:
        with _lock:
            return _sensor_state["connected"]

    @staticmethod
    def get_reading() -> Dict[str, Any]:
        """Return the latest sensor reading (real or simulated)."""
        with _lock:
            if _sensor_state["connected"]:
                return dict(_sensor_state)
        # Fallback: if disconnected, do not simulate fake data.
        reading = {
            "temperature": 0.0,
            "humidity": 0.0,
            "pressure": 0.0,
            "wind_speed": 0.0,
            "rainfall": 0.0,
            "light_intensity": 0.0,
            "lux": 0.0,
            "pm1_0": 0.0,
            "pm2_5": 0.0,
            "pm4_0": 0.0,
            "pm10": 0.0,
            "rain_presence": 0,
            "wind_direction": "N/A",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "disconnected",
            "connected": False,
        }
        with _lock:
            _sensor_state.update(reading)
        return reading

    @staticmethod
    def get_multi_node_readings(n_nodes: int = 3) -> List[Dict[str, Any]]:
        """Return readings for n simulated spatial nodes (for GNN input)."""
        base = IoTService.get_reading()
        nodes = []
        for i in range(n_nodes):
            node = {
                "node_id": i,
                "temperature": round(base["temperature"] + random.gauss(0, 0.5), 2),
                "humidity": round(base["humidity"] + random.gauss(0, 1.0), 2),
                "pressure": round(base["pressure"] + random.gauss(0, 0.2), 2),
                "wind_speed": round(max(0, base["wind_speed"] + random.gauss(0, 0.3)), 2),
                "pm2_5": round(max(0.1, base["pm2_5"] + random.gauss(0, 1.0)), 2),
                "light_intensity": round(max(0, base["light_intensity"] + random.gauss(0, 10.0)), 1),
            }
            nodes.append(node)
        return nodes

    @staticmethod
    def connect_serial(port: str = "COM3", baud: int = 9600) -> Dict[str, str]:
        success = SerialWeatherReader.connect(port, baud)
        return {"status": "connected" if success else "failed", "transport": "serial", "port": port}

    @staticmethod
    def connect_mqtt(host: str = "192.168.1.100", port: int = 1883) -> Dict[str, str]:
        success = MQTTWeatherReader.connect(host, port)
        return {"status": "connected" if success else "failed", "transport": "mqtt", "broker": host}

    @staticmethod
    def disconnect_all() -> None:
        SerialWeatherReader.disconnect()
        MQTTWeatherReader.disconnect()
        with _lock:
            _sensor_state["connected"] = False
            _sensor_state["source"] = "simulator"

    @staticmethod
    def configure_simulator(noise_level: float) -> None:
        WeatherSimulator.configure(noise_level)

    @staticmethod
    def get_status() -> Dict[str, Any]:
        with _lock:
            return {
                "connected": _sensor_state["connected"],
                "source": _sensor_state["source"],
                "last_reading_at": _sensor_state["timestamp"],
                "serial_available": SERIAL_AVAILABLE,
                "mqtt_available": MQTT_AVAILABLE,
            }
