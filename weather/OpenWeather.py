import json
import requests as requests


class OpenWeather:
    OPEN_WEATHER_API_KEY = "00c3ab391941deae3a9558840495d1de"
    OPEN_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
    # OpenWeather requires a http and not an https url.
    OPEN_WEATHER_GEOCODE_ENDPOINT = "http://api.openweathermap.org/geo/1.0/direct?q="
    OPEN_WEATHER_ICON_LOCATION_1 = "http://openweathermap.org/img/wn/"
    OPEN_WEATHER_ICON_LOCATION_2 = "@2x.png"

    API_LIMIT = "1"

    def __init__(self, weather_model):
        self.weather_model = weather_model
        self.last_error = ""

    def call_open_weather(self, city, state, country, code):
        # default to United States
        if len(country) == 0:
            country = "US"
        if len(code) != 0:
            try:
                response = requests.get(self.get_weather_from_postal_code(code, country))
                if response.status_code == 200:
                    self.weather_model.set_weather_data(json.loads(response.content.decode()))
                    self.weather_model.interpret_data()
                    return True
                else:
                    self.process_call_failure(response)
            except requests.exceptions.RequestException:
                self.last_error = "Request Exception for Postal Code " + str(code) + " " + country
        if len(city) != 0:
            try:
                response = requests.get(self.get_geocode_info_from_city_state(city, state, country))
                if response.status_code == 200:
                    geocode_info = json.loads(response.content.decode())
                    # if location is valid, geocode_info has elements
                    if len(geocode_info) > 0:
                        self.weather_model.set_geocode_data(geocode_info[0])
                        latitude = self.weather_model.get_latitude()
                        longitude = self.weather_model.get_longitude()
                        response = requests.get(self.get_weather_from_lat_long(latitude, longitude))
                        if response.status_code == 200:
                            self.weather_model.weather_data = json.loads(response.content.decode())
                            self.weather_model.interpret_data()
                            return True
                        else:
                            self.process_call_failure(response)
                    else:
                        self.last_error = "Location Error for City=[" + city + "] State=[" + state + "] country=[" +\
                            country + "]"
                else:
                    self.process_call_failure(response)
            except requests.exceptions.RequestException:
                self.last_error = "Request Error for City=[" + city + "] State=[" + state + "] country=[" + country +\
                                  "]"
        return False

    def get_geocode_info_from_city_state(self, city, state, country):
        if len(country) == 0:
            country = "US"
        return (self.OPEN_WEATHER_GEOCODE_ENDPOINT + city + "," + state + "," + country + "&limit=" + self.API_LIMIT
                + "&apikey=" + self.OPEN_WEATHER_API_KEY)
        # [{"name":"Oviedo","lat":28.6702526,"lon":-81.2084941,"country":"US","state":"Florida"}]

    def get_weather_from_lat_long(self, latitude, longitude):
        return (self.OPEN_WEATHER_URL + "?lat=" + str(latitude) + "&lon=" + str(longitude) + "&appid="
                + self.OPEN_WEATHER_API_KEY)
        # https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}

    def get_weather_from_postal_code(self, code, country):
        if len(country) == 0:
            country = "US"
        return (self.OPEN_WEATHER_URL + "?zip=" + code + "," + country + "&apikey="
                + self.OPEN_WEATHER_API_KEY)

    def get_weather_icon(self, icon):
        icon_url = self.OPEN_WEATHER_ICON_LOCATION_1 + icon + self.OPEN_WEATHER_ICON_LOCATION_2
        response = requests.get(icon_url)
        img_data = response.content
        return img_data

    def process_call_failure(self, response):
        site_response = json.loads(response.content.decode())
        self.last_error = "Status Code: {0}. Message: {1}".format(response.status_code,
                                                                  site_response.get("message"))

    def get_error_message(self):
        return self.last_error
