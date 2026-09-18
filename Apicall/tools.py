import os
import requests
import json

# WMO Weather interpretation codes (WW) mapping
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog and depositing rime fog",
    48: "Depositing rime fog",
    51: "Drizzle: Light intensity",
    53: "Drizzle: Moderate intensity",
    55: "Drizzle: Dense intensity",
    56: "Freezing Drizzle: Light intensity",
    57: "Freezing Drizzle: Dense intensity",
    61: "Rain: Slight intensity",
    63: "Rain: Moderate intensity",
    65: "Rain: Heavy intensity",
    66: "Freezing Rain: Light intensity",
    67: "Freezing Rain: Heavy intensity",
    71: "Snow fall: Slight intensity",
    73: "Snow fall: Moderate intensity",
    75: "Snow fall: Heavy intensity",
    77: "Snow grains",
    80: "Rain showers: Slight",
    81: "Rain showers: Moderate",
    82: "Rain showers: Violent",
    85: "Snow showers: Slight",
    86: "Snow showers: Heavy",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

def get_weather_data(city: str) -> dict:
    """
    Fetch current weather conditions for a given city using Open-Meteo's open-source API.
    
    Args:
        city (str): Name of the city (e.g., 'London', 'Tokyo', 'New York', 'Mumbai').
        
    Returns:
        dict: Weather information including temperature, windspeed, weather condition, etc.
    """
    try:
        # Step 1: Geocoding - Convert city name to latitude and longitude
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return {"error": f"City '{city}' not found."}

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        city_name = location["name"]
        country = location.get("country", "")

        # Step 2: Fetch weather forecast data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_response = requests.get(weather_url, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        current = weather_data.get("current_weather", {})
        weather_code = current.get("weathercode", 0)
        condition = WMO_WEATHER_CODES.get(weather_code, "Unknown weather condition")

        return {
            "city": city_name,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "temperature_celsius": current.get("temperature"),
            "windspeed_kmh": current.get("windspeed"),
            "wind_direction_degrees": current.get("winddirection"),
            "weather_condition": condition,
            "is_day": "Yes" if current.get("is_day") == 1 else "No"
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


def create_directory(directory_path: str) -> dict:
    """
    Creates a new directory (folder) at the specified path on the local filesystem.
    
    Args:
        directory_path (str): Relative or absolute path of the directory to create.
        
    Returns:
        dict: Result status and path details.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return {
            "status": "success",
            "message": f"Directory '{directory_path}' created successfully.",
            "directory_path": os.path.abspath(directory_path)
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to create directory: {str(e)}"}


def create_file(file_path: str, content: str = "") -> dict:
    """
    Creates a new file at the specified path on the local filesystem with optional content.
    
    Args:
        file_path (str): Relative or absolute file path to create.
        content (str): Text content to write into the file.
        
    Returns:
        dict: Result status and file details.
    """
    try:
        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "status": "success",
            "message": f"File '{file_path}' created successfully.",
            "file_path": os.path.abspath(file_path),
            "bytes_written": len(content.encode("utf-8"))
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to create file: {str(e)}"}


# OpenAI Function Calling Specifications

WEATHER_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "get_weather_data",
        "description": "Get current weather conditions for any city globally using an open-source weather API.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The name of the city for which to retrieve weather data (e.g. 'London', 'Tokyo', 'Mumbai', 'New York')."
                }
            },
            "required": ["city"]
        }
    }
}

CREATE_DIRECTORY_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "create_directory",
        "description": "Create a new directory (folder) at the specified path on the local filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Relative or absolute path of the directory/folder to create (e.g., 'logs' or 'output/reports')."
                }
            },
            "required": ["directory_path"]
        }
    }
}

CREATE_FILE_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "create_file",
        "description": "Create a new file at the specified path on the local filesystem with optional initial content.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative or absolute file path to create (e.g., 'notes.txt' or 'data/sample.json')."
                },
                "content": {
                    "type": "string",
                    "description": "Initial text content to write into the file. Default is empty."
                }
            },
            "required": ["file_path"]
        }
    }
}

# Exported tools array for OpenAI API calls
AVAILABLE_TOOLS = [
    WEATHER_TOOL_SPEC,
    CREATE_DIRECTORY_TOOL_SPEC,
    CREATE_FILE_TOOL_SPEC
]

# Map tool names to python function references
TOOL_MAPPING = {
    "get_weather_data": get_weather_data,
    "create_directory": create_directory,
    "create_file": create_file
}

def execute_tool(tool_name: str, arguments: dict):
    """
    Executes a tool function dynamically based on tool_name and arguments.
    """
    if tool_name in TOOL_MAPPING:
        return TOOL_MAPPING[tool_name](**arguments)
    else:
        return {"error": f"Tool '{tool_name}' is not recognized."}
