const searchForm = document.querySelector("#weather-search-form");
const cityInput = document.querySelector("#city-input");
const getWeatherButton = document.querySelector("#get-weather-button");
const statusMessage = document.querySelector("#status-message");
const emptyState = document.querySelector("#empty-state");
const weatherResults = document.querySelector("#weather-results");
const locationName = document.querySelector("#location-name");
const lastUpdated = document.querySelector("#last-updated");
const currentCondition = document.querySelector("#current-condition");
const currentTemperature = document.querySelector("#current-temperature");
const currentFeelsLike = document.querySelector("#current-feels-like");
const currentWeatherIcon = document.querySelector("#current-weather-icon");
const humidityValue = document.querySelector("#humidity-value");
const windValue = document.querySelector("#wind-value");
const precipitationValue = document.querySelector("#precipitation-value");
const forecastList = document.querySelector("#forecast-list");

let activeRequest;
let requestVersion = 0;

function setStatus(message, state = "info") {
    statusMessage.textContent = message;
    statusMessage.dataset.state = state;
    statusMessage.hidden = !message;
}

function setLoading(isLoading) {
    getWeatherButton.disabled = isLoading;
    getWeatherButton.textContent = isLoading ? "Checking..." : "Check weather";
    cityInput.disabled = isLoading;
}

function formatDate(dateValue) {
    const date = new Date(`${dateValue}T12:00:00`);

    if (Number.isNaN(date.getTime())) {
        return dateValue;
    }

    return new Intl.DateTimeFormat(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric",
    }).format(date);
}

function formatNumber(value, suffix = "") {
    if (value === null || value === undefined || value === "") {
        return "-";
    }

    return `${Math.round(Number(value))}${suffix}`;
}

function getLocationLabel(location) {
    if (typeof location === "string") {
        return location;
    }

    const parts = [location?.name, location?.country].filter(Boolean);
    return parts.join(", ") || "Selected location";
}

function getWeatherTheme(current) {
    const text = `${current?.theme || ""} ${current?.condition || ""}`.toLowerCase();

    if (text.includes("storm") || text.includes("thunder")) {
        return "storm";
    }

    if (text.includes("snow") || text.includes("sleet") || text.includes("ice")) {
        return "snow";
    }

    if (text.includes("rain") || text.includes("drizzle")) {
        return "rain";
    }

    if (text.includes("cloud") || text.includes("overcast")) {
        return "cloudy";
    }

    return "clear";
}

function renderForecast(forecast = []) {
    forecastList.replaceChildren();

    forecast.forEach((day) => {
        const card = document.createElement("article");
        card.className = "forecast-card";

        const dayName = document.createElement("span");
        dayName.className = "forecast-day";
        dayName.textContent = formatDate(day.date);

        const condition = document.createElement("span");
        condition.className = "forecast-condition";
        condition.textContent = `${day.icon || ""} ${day.condition || "Unknown conditions"}`.trim();

        const temperature = document.createElement("span");
        temperature.className = "forecast-temperature";
        temperature.textContent = `${formatNumber(day.min_temperature ?? day.min, "°")} / ${formatNumber(day.max_temperature ?? day.max, "°")}`;

        card.append(dayName, condition, temperature);
        forecastList.append(card);
    });
}

function renderWeather(weather) {
    const current = weather.current || {};
    const location = weather.location || weather.city || {};

    locationName.textContent = getLocationLabel(location);
    currentCondition.textContent = current.condition || "Current conditions";
    currentTemperature.textContent = formatNumber(current.temperature);
    currentFeelsLike.textContent = current.feels_like === undefined
        ? ""
        : `Feels like ${formatNumber(current.feels_like, "°C")}`;
    currentWeatherIcon.textContent = current.icon || "--";
    humidityValue.textContent = formatNumber(current.humidity, "%");
    windValue.textContent = formatNumber(current.wind_speed, " km/h");
    precipitationValue.textContent = formatNumber(current.precipitation, " mm");
    lastUpdated.textContent = weather.updated_at
        ? `Updated ${new Date(weather.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
        : "";

    document.body.dataset.weather = getWeatherTheme(current);
    renderForecast(weather.forecast || weather.daily || []);
    emptyState.hidden = true;
    weatherResults.hidden = false;
}

async function fetchWeather(city) {
    if (activeRequest) {
        activeRequest.abort();
    }

    activeRequest = new AbortController();
    const query = encodeURIComponent(city);
    const response = await fetch(`/weather?city=${query}`, {
        headers: { Accept: "application/json" },
        signal: activeRequest.signal,
    });

    let payload;
    try {
        payload = await response.json();
    } catch {
        throw new Error("The weather service returned an invalid response.");
    }

    if (!response.ok) {
        throw new Error(payload.error || "Weather data could not be loaded.");
    }

    return payload;
}

searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const city = cityInput.value.trim();
    if (!city) {
        setStatus("Enter a city name to search.", "error");
        cityInput.focus();
        return;
    }

    const currentRequestVersion = ++requestVersion;
    setLoading(true);
    setStatus("Finding the latest weather...", "loading");

    try {
        const weather = await fetchWeather(city);
        renderWeather(weather);
        setStatus("");
    } catch (error) {
        if (error.name === "AbortError" || currentRequestVersion !== requestVersion) {
            return;
        }

        setStatus(error.message || "Weather data could not be loaded. Try again.", "error");
        weatherResults.hidden = true;
        emptyState.hidden = false;
    } finally {
        if (currentRequestVersion === requestVersion) {
            setLoading(false);
        }
    }
});