from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Weather App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card {
            background: rgba(0,0,0,0.3);
            padding: 30px 40px;
            border-radius: 12px;
            width: 320px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        }
        h1 { margin-bottom: 10px; }
        .temp { font-size: 48px; font-weight: bold; }
        .desc { text-transform: capitalize; margin: 10px 0; }
        .small { font-size: 14px; opacity: 0.9; }
        button {
            margin-top: 15px;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🌦 Weather</h1>
        <div id="location">Loading...</div>
        <div class="temp" id="temp">--°C</div>
        <div class="desc" id="desc">---</div>
        <div class="small" id="details"></div>
        <button onclick="loadWeather()">Refresh</button>
    </div>

    <script>
        async function loadWeather() {
            document.getElementById("location").innerText = "Loading...";
            const res = await fetch("/weather");
            const data = await res.json();

            if (data.error) {
                document.getElementById("location").innerText = "Location not detected";
                return;
            }

            document.getElementById("location").innerText = data.location;
            document.getElementById("temp").innerText = data.weather.temperature + "°C";
            document.getElementById("desc").innerText = data.weather.description;
            document.getElementById("details").innerText =
                "Feels like: " + data.weather.feels_like + "°C | Humidity: " + data.weather.humidity + "% | Wind: " + data.weather.wind_kph + " km/h";
        }

        loadWeather();
    </script>
</body>
</html>
"""

def get_location_from_ip(ip):
    url = f"http://ip-api.com/json/{ip}"
    data = requests.get(url).json()
    if data["status"] == "success":
        return data["city"]
    return None


def get_weather(city):
    url = f"https://wttr.in/{city}?format=j1"
    data = requests.get(url).json()
    current = data["current_condition"][0]
    return {
        "temperature": current["temp_C"],
        "feels_like": current["FeelsLikeC"],
        "humidity": current["humidity"],
        "description": current["weatherDesc"][0]["value"],
        "wind_kph": current["windspeedKmph"]
    }


@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


@app.route("/weather")
def weather():
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    city = get_location_from_ip(user_ip)

    if not city:
        return jsonify({"error": "Location not detected"}), 400

    weather_data = get_weather(city)

    return jsonify({
        "location": city,
        "weather": weather_data
    })


if __name__ == "__main__":
    app.run(debug=True)
