from flask import Flask, jsonify, request

from weather_service import LocationNotFoundError, WeatherServiceError, get_weather


app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.get("/")
def index():
	return app.send_static_file("index.html")


@app.get("/weather")
def weather():
	city = request.args.get("city", "").strip()

	if not city:
		return jsonify({"error": "Enter a city name to search."}), 400

	try:
		return jsonify(get_weather(city))
	except LocationNotFoundError as error:
		return jsonify({"error": str(error)}), 404
	except WeatherServiceError as error:
		return jsonify({"error": str(error)}), 502


if __name__ == "__main__":
	app.run(debug=True)
