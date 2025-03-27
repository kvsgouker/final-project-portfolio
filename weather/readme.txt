Project has 5 separate files:

(1) main - main driver creates objects OpenWeather, WeatherModel, and WeatherReportUI.
It also starts logging and starts UI.

(2) OpenWeather - connection with OpenWeather API. Separating allows another API to be plugged into system instead.
More info here: https://openweathermap.org/api/one-call-3

(3) WeatherModel - all the data-specific information is here.

(4) WeatherReportUI - all the user interface objects to show the weather data. Simple UI uses TKinter and grid layout.
More info here: https://www.pythontutorial.net/tkinter/

(5) Units - Shared data between modules moved to separate file to avoid recursive dependencies.

