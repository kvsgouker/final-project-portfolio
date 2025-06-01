# Weather App: Python + OpenWeatherMap

This simple PyCharm project accesses OpenWeather api.

Project has 5 separate files:

(1) main - main driver creates objects OpenWeather, WeatherModel, and WeatherReportUI.
It also starts logging and starts UI.

(2) OpenWeather - connection with OpenWeather API. Separating allows another API to be plugged into system instead.
More info here: https://openweathermap.org/api/one-call-3

(3) WeatherModel - all the data-specific information is here.

(4) WeatherReportUI - all the user interface objects to show the weather data. Simple UI uses TKinter and grid layout.
More info here: https://www.pythontutorial.net/tkinter/

(5) Units - Shared data between modules moved to separate file to avoid recursive dependencies.

![weather-day-cloudy-tokyo](https://github.com/user-attachments/assets/a2d9caeb-21c2-4cef-81e9-bad2ae1ab588)
![weather-day-sunny-singapore](https://github.com/user-attachments/assets/7c96a2bd-4101-4a0f-b9b5-2de5af144d3e)
![weather-night-rio](https://github.com/user-attachments/assets/54a12874-60cc-47ec-b934-8b3d7e7fc040)
![weather-night-32708-zip-code](https://github.com/user-attachments/assets/a6e0adc2-c04f-4734-9fcb-a38c991af553)
