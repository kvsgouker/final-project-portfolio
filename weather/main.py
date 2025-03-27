from OpenWeather import OpenWeather
from WeatherModel import WeatherModel
from WeatherReportUI import WeatherReportUI
import logging


def main():
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    logging.info('Started')
    weather_model = WeatherModel()
    open_weather = OpenWeather(weather_model)
    weather_report = WeatherReportUI(weather_model, open_weather)
    weather_report.layout()
    weather_report.run_forever()
    logging.info("That's all she wrote!")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
