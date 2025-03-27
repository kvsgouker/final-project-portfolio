import _tkinter
import io
import logging
import tkinter as tk
from datetime import timezone
import datetime
from PIL import Image, ImageTk
import Units

# Class constants for defining user interface.
FRAME_WIDTH = 1000
FRAME_HEIGHT = 600
# Rows of User Interface
CITY_ZIP_HEADER_ROW = 1
CITY_ZIP_ENTRY_ROW = 2
ERROR_REPORT_ROW = 3
PAD1_ROW = 4
REQUEST_BUTTON_ROW = 5
RADIO_ROW = 6
PAD2_ROW = 7
DISPLAY_TIME_ROW = 8
DISPLAY_INFO_ROW = 9
DISPLAY_TEMPERATURE_ROW = 10
DISPLAY_RAINFALL_ROW = 11
DISPLAY_WIND_SPEED_ROW = 12
DISPLAY_PRESSURE_ROW = 13
# Columns
LEFT_COLUMN = 0
REPORT_COLUMN = 1
MIDDLE_COLUMN = 2
PENULTIMATE_COLUMN = 3
RIGHT_COLUMN = 4
# Colors of User Interface
DAYTIME_FOREGROUND_COLOR = '#000000'
DAYTIME_BACKGROUND_COLOR = '#1991d1'
NIGHT_FOREGROUND_COLOR = '#7f7f7f'
NIGHT_BACKGROUND_COLOR = '#2a1642'


class WeatherReportUI:

    def __init__(self, weather_model, open_weather):
        self.weather_model = weather_model
        self.open_weather = open_weather
        # create root by invoking Tk.
        self.root = tk.Tk()
        # create several variables for cross field communication.
        self.city = tk.StringVar()
        self.state = tk.StringVar()
        self.country = tk.StringVar()
        self.zipcode = tk.StringVar()
        self.unit_choice = tk.IntVar()
        self.unit_choice.set(Units.CELSIUS[0])
        # create several other fields - these will be set in layout
        self.frm = None
        # pad field for entry row, column 4
        self.pad_field = None
        # fields where the report appears.
        self.wind_speed_label = None
        self.precipitation_label = None
        self.temperature_label = None
        self.minimum_temperature_label = None
        self.maximum_temperature_label = None
        self.feels_like_label = None
        self.pressure_label = None
        # headers for above fields should appear only if they are set
        self.temperature_header = None
        self.precipitation_header = None
        self.wind_speed_header = None
        self.pressure_header = None
        # defines unit choice
        self.kelvin_radio = None
        self.celsius_radio = None
        self.fahrenheit_radio = None
        # executes weather request
        self.weather_button = None
        # for error messages on input.
        self.invalid_zip_label = None
        self.error_message_label = None
        # Time labels
        self.sunrise_label = None
        self.now_label = None
        self.sunset_label = None
        # Image of weather
        self.weather_image_label = None
        self.weather_image = None

    def change_colors(self, foreground_color, background_color):
        children = self.frm.winfo_children()
        self.frm.config(background=background_color)
        for child in children:
            try:
                child.config(background=background_color, foreground=foreground_color)
            except _tkinter.TclError:
                # this is ok for children without text.
                continue

    def color_for_time(self, time):
        if time < self.weather_model.get_sunrise() or time > self.weather_model.get_sunset():
            background_color = NIGHT_BACKGROUND_COLOR
            foreground_color = NIGHT_FOREGROUND_COLOR
        else:
            background_color = DAYTIME_BACKGROUND_COLOR
            foreground_color = DAYTIME_FOREGROUND_COLOR
        return [foreground_color, background_color]

    def place_image(self, icon):
        self.weather_image = ImageTk.PhotoImage(Image.open(io.BytesIO(self.open_weather.get_weather_icon(icon))))
        self.weather_image_label = tk.Label(self.frm, image=self.weather_image, name='icon',
                                            background=self.color_for_time(self.weather_model.get_now())[1])
        self.weather_image_label.grid(column=MIDDLE_COLUMN, row=PAD2_ROW)

    def weather_report(self):
        # """ callback when the weather button or radio button clicked
        #   """
        # Gets city and zip from the UI
        city_value = self.city.get()
        state_value = self.state.get()
        zip_value = self.zipcode.get()
        country_value = self.country.get()

        # Invoke OpenWeather API.
        if self.open_weather.call_open_weather(city_value, state_value, country_value, zip_value):
            self.clear_error()
            logging.info("OpenWeather API success for city='{0}' state='{1}' country='{2}' zip='{3}'".format(
                city_value, state_value, country_value, zip_value))
            # change colors
            colors = self.color_for_time(self.weather_model.get_now())
            self.change_colors(colors[0], colors[1])
            # update report headers
            self.temperature_header.config(text="Temperature")
            self.precipitation_header.config(text="Precipitation")
            self.wind_speed_header.config(text="Wind Speed")
            self.pressure_header.config(text="Pressure")
            # Update the UI with the information fetched from OpenWeather API.
            self.show_time_data()
            self.show_weather_data()
        else:
            self.show_error()

    def show_error(self):
        error_message = self.open_weather.get_error_message()
        # update error labels on bad input.
        self.error_message_label.config(text=error_message)
        logging.error(error_message)

    def clear_error(self):
        self.error_message_label.config(text=" " * 60)

    def show_time_data(self):
        # Format times for display
        sunrise_out = self.weather_model.convert_datetime(self.weather_model.get_sunrise())
        sunset_out = self.weather_model.convert_datetime(self.weather_model.get_sunset())
        now_out = self.weather_model.convert_datetime(self.weather_model.get_now())
        self.sunrise_label.config(text="Sunrise: " + sunrise_out)
        self.now_label.config(text="Now: " + now_out)
        self.sunset_label.config(text="Sunset: " + sunset_out)

    def show_weather_data(self):
        # unit stuff
        unit_selected = Units.units[self.unit_choice.get()]
        temperature_unit = str(unit_selected[2])
        rainfall_unit = unit_selected[3]
        wind_speed_unit = unit_selected[4]

        # update report labels
        temp_out = self.weather_model.convert_temperature(self.weather_model.get_temperature(), self.unit_choice.get())
        feels_like_out = self.weather_model.convert_temperature(self.weather_model.get_feels_like(),
                                                                self.unit_choice.get())
        min_out = self.weather_model.convert_temperature(self.weather_model.get_minimum_temperature(),
                                                         self.unit_choice.get())
        max_out = self.weather_model.convert_temperature(self.weather_model.get_maximum_temperature(),
                                                         self.unit_choice.get())
        rain_out = self.weather_model.convert_rainfall(self.unit_choice.get())
        speed_out = self.weather_model.convert_wind_speed(self.weather_model.get_wind_speed(), self.unit_choice.get())

        self.temperature_label.config(text="Current = " + temp_out + " " + temperature_unit)
        self.minimum_temperature_label.config(text="Min = " + min_out + " " + temperature_unit)
        self.maximum_temperature_label.config(text="Max = " + max_out + " " + temperature_unit)
        self.feels_like_label.config(text="Feels Like = " + feels_like_out + " " + temperature_unit)
        self.precipitation_label.config(text=rain_out + " " + rainfall_unit)
        self.wind_speed_label.config(text=speed_out + " " + wind_speed_unit)
        self.pressure_label.config(text=str(self.weather_model.get_pressure()))
        self.place_image(self.weather_model.get_icon())

    def layout(self):
        # set up initial default colors, which are set after all the widgets are added.
        dt = datetime.datetime.now(timezone.utc)
        utc_time = dt.replace(tzinfo=timezone.utc)
        utc_timestamp = utc_time.timestamp()
        default_colors = self.color_for_time(utc_timestamp)
        # set up title, size, resizability, and padding of frame in root.
        self.root.title("Weather Report")
        geometry_size = str(FRAME_WIDTH) + "x" + str(FRAME_HEIGHT)
        self.root.geometry(geometry_size)
        self.root.resizable(True, True)
        # ok, make a frame.
        self.frm = tk.Frame(self.root)
        # use a grid layout because it's easy and scales well.
        self.frm.grid()
        # header for city & zip
        tk.Label(self.frm, text="City").grid(column=LEFT_COLUMN, row=CITY_ZIP_HEADER_ROW)
        tk.Label(self.frm, text="State").grid(column=REPORT_COLUMN, row=CITY_ZIP_HEADER_ROW)
        tk.Label(self.frm, text="Country").grid(column=MIDDLE_COLUMN, row=CITY_ZIP_HEADER_ROW)
        tk.Label(self.frm, text=" "*30).grid(column=PENULTIMATE_COLUMN, row=CITY_ZIP_HEADER_ROW, padx=5)
        tk.Label(self.frm, text="Zip").grid(column=RIGHT_COLUMN, row=CITY_ZIP_HEADER_ROW)
        # entry fields for city & zip
        tk.Entry(self.frm, textvariable=self.city).grid(column=LEFT_COLUMN, row=CITY_ZIP_ENTRY_ROW, padx=5)
        tk.Entry(self.frm, textvariable=self.state).grid(column=REPORT_COLUMN, row=CITY_ZIP_ENTRY_ROW, padx=5)
        tk.Entry(self.frm, textvariable=self.country).grid(column=MIDDLE_COLUMN, row=CITY_ZIP_ENTRY_ROW, padx=5)
        tk.Entry(self.frm, textvariable=self.zipcode).grid(column=RIGHT_COLUMN, row=CITY_ZIP_ENTRY_ROW, padx=5)
        # errors in input row
        self.error_message_label = tk.Label(self.frm, text=" ")
        self.error_message_label.grid(column=LEFT_COLUMN, row=ERROR_REPORT_ROW, columnspan=3)
        # spacer of 1 line
        tk.Label(self.frm, text=" ").grid(column=LEFT_COLUMN, row=PAD1_ROW)
        # button executes weather report. All buttons (radio too) do the same thing.
        self.weather_button = tk.Button(self.frm, text="Get Weather", command=self.weather_report)
        self.weather_button.grid(column=MIDDLE_COLUMN, row=REQUEST_BUTTON_ROW, pady=10)
        # radio button for unit choice.
        self.celsius_radio = tk.Radiobutton(self.frm, text=Units.CELSIUS[1], variable=self.unit_choice,
                                            value=Units.CELSIUS[0],
                                            command=self.weather_report)
        self.celsius_radio.grid(column=REPORT_COLUMN, row=RADIO_ROW)
        self.fahrenheit_radio = tk.Radiobutton(self.frm, text=Units.FAHRENHEIT[1], variable=self.unit_choice,
                                               value=Units.FAHRENHEIT[0],
                                               command=self.weather_report)
        self.fahrenheit_radio.grid(column=MIDDLE_COLUMN, row=RADIO_ROW)
        self.kelvin_radio = tk.Radiobutton(self.frm, text=Units.KELVIN[1], variable=self.unit_choice,
                                           value=Units.KELVIN[0],
                                           command=self.weather_report)
        self.kelvin_radio.grid(column=PENULTIMATE_COLUMN, row=RADIO_ROW)
        # spacer of 1 line
        tk.Label(self.frm, text=" ").grid(column=LEFT_COLUMN, row=PAD2_ROW)
        self.sunrise_label = tk.Label(self.frm)
        self.sunrise_label.grid(column=LEFT_COLUMN, row=DISPLAY_TIME_ROW)
        self.now_label = tk.Label(self.frm)
        self.now_label.grid(column=MIDDLE_COLUMN, row=DISPLAY_TIME_ROW)
        self.sunset_label = tk.Label(self.frm)
        self.sunset_label.grid(column=RIGHT_COLUMN, row=DISPLAY_TIME_ROW)
        # header for temperature, precipitation, & wind speed.
        self.temperature_header = tk.Label(self.frm, text="")
        self.temperature_header.grid(column=LEFT_COLUMN, row=DISPLAY_TEMPERATURE_ROW)
        self.precipitation_header = tk.Label(self.frm, text="")
        self.precipitation_header.grid(column=LEFT_COLUMN, row=DISPLAY_RAINFALL_ROW)
        self.wind_speed_header = tk.Label(self.frm, text="")
        self.wind_speed_header.grid(column=LEFT_COLUMN, row=DISPLAY_WIND_SPEED_ROW)
        self.pressure_header = tk.Label(self.frm, text="")
        self.pressure_header.grid(column=LEFT_COLUMN, row=DISPLAY_PRESSURE_ROW)
        # create fields for weather information
        # reserve some space for temperature label
        self.temperature_label = tk.Label(self.frm, text="")
        self.temperature_label.grid(column=REPORT_COLUMN, row=DISPLAY_TEMPERATURE_ROW)
        self.minimum_temperature_label = tk.Label(self.frm, text="")
        self.minimum_temperature_label.grid(column=MIDDLE_COLUMN, row=DISPLAY_TEMPERATURE_ROW)
        self.maximum_temperature_label = tk.Label(self.frm, text="")
        self.maximum_temperature_label.grid(column=PENULTIMATE_COLUMN, row=DISPLAY_TEMPERATURE_ROW)
        self.feels_like_label = tk.Label(self.frm, text="")
        self.feels_like_label.grid(column=RIGHT_COLUMN, row=DISPLAY_TEMPERATURE_ROW)
        self.precipitation_label = tk.Label(self.frm)
        self.precipitation_label.grid(column=REPORT_COLUMN, row=DISPLAY_RAINFALL_ROW)
        self.wind_speed_label = tk.Label(self.frm)
        self.wind_speed_label.grid(column=REPORT_COLUMN, row=DISPLAY_WIND_SPEED_ROW)
        self.pressure_label = tk.Label(self.frm)
        self.pressure_label.grid(column=REPORT_COLUMN, row=DISPLAY_PRESSURE_ROW)
        # time sensitive colors.
        self.change_colors(default_colors[0], default_colors[1])
        self.frm.pack(anchor='nw', fill='both', expand=True)

    def run_forever(self):
        # run the user interface forever
        self.root.mainloop()
