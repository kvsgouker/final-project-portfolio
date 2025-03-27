from datetime import timezone
import datetime
import Units


class WeatherModel:

    def __init__(self):
        # dictionary for api calls
        self.weather_data = {}
        self.geocode_data = {}
        self.icon = None
        self.temp = None
        self.feels_like = None
        self.temp_min = None
        self.temp_max = None
        self.pressure = None
        self.humidity = None

        # default times - sunrise at 6 am, sunset at 6 pm. This is just for color

        right_now = datetime.datetime.now(timezone.utc)
        dt_fake_sunrise = datetime.datetime(right_now.year, right_now.month, right_now.day, 6, 0, 0, 0)
        # utc_time = dt_fake_sunrise.replace(tzinfo=timezone.utc)
        utc_timestamp = dt_fake_sunrise.timestamp()
        self.sunrise = utc_timestamp

        dt_fake_sunset = datetime.datetime(right_now.year, right_now.month, right_now.day, 18, 0, 0, 0)
        # utc_time = dt_fake_sunset.replace(tzinfo=timezone.utc)
        utc_timestamp = dt_fake_sunset.timestamp()
        self.sunset = utc_timestamp

        dt = datetime.datetime.now(timezone.utc)
        utc_time = dt.replace(tzinfo=timezone.utc)
        utc_timestamp = utc_time.timestamp()
        self.now = utc_timestamp

        self.speed = None
        self.deg = None
        self.rain = None
        self.visibility = None
        self.general_weather = ""
        self.specific_weather_description = ""

    def get_weather_data(self):
        return self.weather_data

    def get_geocode_data(self):
        return self.geocode_data

    def set_weather_data(self, weather_data):
        self.weather_data = weather_data

    def set_geocode_data(self, geocode_data):
        self.geocode_data = geocode_data

    def interpret_data(self):
        # process weather
        general_weather_data = self.weather_data.get("weather")
        general_weather_description = general_weather_data[0]
        self.general_weather = general_weather_description.get("main")
        self.specific_weather_description = general_weather_description.get("description")
        self.icon = general_weather_description.get("icon")
        main_data = self.weather_data.get("main")
        self.temp = main_data.get("temp")
        self.feels_like = main_data.get("feels_like")
        self.temp_min = main_data.get("temp_min")
        self.temp_max = main_data.get("temp_max")
        self.pressure = main_data.get("pressure")
        self.humidity = main_data.get("humidity")
        sys_data = self.weather_data.get("sys")
        self.sunrise = sys_data.get("sunrise")
        self.sunset = sys_data.get("sunset")
        self.now = self.weather_data.get("dt")
        wind_data = self.weather_data.get("wind")
        self.speed = wind_data.get("speed")
        self.deg = wind_data.get("deg")
        self.rain = self.weather_data.get("rain")
        self.visibility = self.weather_data.get("visibility")

    @staticmethod
    def convert_temperature(temp, unit_choice):
        if unit_choice == Units.CELSIUS_OPTION:
            temp = temp - 273.15
        elif unit_choice == Units.FAHRENHEIT_OPTION:
            temp = (temp - 273.15) * 9.0 / 5.0 + 32.0
        return WeatherModel.format_as_two_decimal_float(temp)

    @staticmethod
    def convert_wind_speed(speed, unit_choice):
        if unit_choice == Units.FAHRENHEIT_OPTION:
            speed = speed / 1.609344
        return WeatherModel.format_as_two_decimal_float(speed)

    @staticmethod
    def format_as_two_decimal_float(value):
        return "{:,.2f}".format(value)

    @staticmethod
    def convert_datetime(time_to_convert):
        time = datetime.datetime.fromtimestamp(time_to_convert)
        return time.strftime("%H:%M:%S")

    def convert_rainfall(self, unit_choice):
        if self.rain is None:
            rainfall = 0
        else:
            rainfall = self.rain.get("1h")
        if unit_choice == Units.FAHRENHEIT_OPTION:
            rainfall = rainfall / 2.54
        return self.format_as_two_decimal_float(rainfall)

    def get_latitude(self):
        return self.geocode_data["lat"]

    def get_longitude(self):
        return self.geocode_data["lon"]

    def get_temperature(self):
        return self.temp

    def get_feels_like(self):
        return self.feels_like

    def get_minimum_temperature(self):
        return self.temp_min

    def get_maximum_temperature(self):
        return self.temp_max

    def get_pressure(self):
        return self.pressure

    def get_humidity(self):
        return self.humidity

    def get_sunrise(self):
        return self.sunrise

    def get_sunset(self):
        return self.sunset

    def get_now(self):
        return self.now

    def get_wind_speed(self):
        return self.speed

    def get_wind_direction(self):
        return self.deg

    def get_rain(self):
        return self.rain

    def get_visibility(self):
        return self.visibility

    def get_icon(self):
        return self.icon

    def get_general_weather(self):
        return self.general_weather

    def get_specific_weather(self):
        return self.specific_weather_description
