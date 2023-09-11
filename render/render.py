"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot.

This might sound like a convoluted way to generate the calendar, but I'm doing so mainly because (i) it's easier to
format the calendar exactly the way I want it using HTML/CSS, and (ii) I can delink the generation of the
calendar and refreshing of the eInk display.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from datetime import timedelta
import pathlib
import string
from PIL import Image
import logging
from selenium.webdriver.common.by import By
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


class RenderHelper:

    def __init__(self, width, height, angle):
        self.logger = logging.getLogger('maginkdash')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = 'file://' + self.currPath + '/dashboard.html'
        self.imageWidth = width
        self.imageHeight = height
        self.rotateAngle = angle

    def set_viewport_size(self, driver):

        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html = driver.find_element(By.TAG_NAME,'html')
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = self.imageWidth + (current_window_size["width"] - inner_width)
        target_height = self.imageHeight + (current_window_size["height"] - inner_height)

        driver.set_window_rect(
            width=target_width,
            height=target_height)

    def get_screenshot(self, path_to_server_image):
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars");
        opts.add_argument('--force-device-scale-factor=1')
        driver = webdriver.Chrome(options=opts)
        self.set_viewport_size(driver)
        driver.get(self.htmlFile)
        sleep(1)
        driver.get_screenshot_as_file(self.currPath + '/dashboard.png')
        driver.get_screenshot_as_file(path_to_server_image)
        self.logger.info('Screenshot captured and saved to file.')

    def get_short_time(self, datetimeObj, is24hour=False):
        datetime_str = ''
        if is24hour:
            datetime_str = '{}:{:02d}'.format(datetimeObj.hour, datetimeObj.minute)
        else:
            if datetimeObj.minute > 0:
                datetime_str = '.{:02d}'.format(datetimeObj.minute)

            if datetimeObj.hour == 0:
                datetime_str = '12{}am'.format(datetime_str)
            elif datetimeObj.hour == 12:
                datetime_str = '12{}pm'.format(datetime_str)
            elif datetimeObj.hour > 12:
                datetime_str = '{}{}pm'.format(str(datetimeObj.hour % 12), datetime_str)
            else:
                datetime_str = '{}{}am'.format(str(datetimeObj.hour), datetime_str)
        return datetime_str
      
    def process_inputs(self, current_date, daily_forecast, event_list, path_to_server_image,birthday_list,task_list,now_weather):
        # Read html template
        with open(self.currPath + '/dashboard_template.html', 'r') as file:
            dashboard_template = file.read()
        # Populate the date and events
        cal_events_list = []
        cal_events_list=["","","","","","","","","",""]
            
        for x in range(0,9):
            cal_events_text = ""
            if(x<len(event_list)):
                cal_events_text += '<div class="event">'
                cal_events_text += '<span class="event-time">' + event_list[x] + '</span> '
                cal_events_text += '</div>\n'           
            cal_events_list[x]=cal_events_text  
            
        birthday_events_list = []
        birthday_events_list=["","","","",""]           
        for y in range(0,5):
            birthday_events_text = ""
            if(y<len(birthday_list)):
                birthday_events_text += '<div class="event">'
                birthday_events_text += '<span class="event-time">' + birthday_list[y] + '</span> '
                birthday_events_text += '</div>\n'           
            birthday_events_list[y]=birthday_events_text  
        task_events_list = []
        task_events_list=["","","","","",""] 
        for z in range(0,5):
            task_events_text = ""
            if(z<len(task_list)):
                task_events_text += '<div class="event">'
                task_events_text += '<span class="event-time">' + task_list[z] + '</span> '
                task_events_text += '</div>\n'           
            task_events_list[z]=task_events_text  
        # Append the bottom and write the file
        htmlFile = open(self.currPath + '/dashboard.html', "w")
        htmlFile.write(dashboard_template.format(
            day=current_date.strftime("%-d"),
            month=current_date.strftime("%B"),
            weekday=current_date.strftime("%A"),
            tomorrow=(current_date + timedelta(days=1)).strftime("%A"),
            dayafter=(current_date + timedelta(days=2)).strftime("%A"),
            dayafterafter=(current_date + timedelta(days=3)).strftime("%A"),
            events_0=cal_events_list[0],
            events_1=cal_events_list[1],
            events_2=cal_events_list[2],
            events_3=cal_events_list[3],
            events_4=cal_events_list[4],
            events_5=cal_events_list[5],
            events_6=cal_events_list[6],
            events_7=cal_events_list[7],
            events_8=cal_events_list[8],
            events_9=cal_events_list[9],
            birthday_0=birthday_events_list[0],
            birthday_1=birthday_events_list[1],
            birthday_2=birthday_events_list[2],
            birthday_3=birthday_events_list[3],
            birthday_4=birthday_events_list[4],
            task_0=task_events_list[0],
            task_1=task_events_list[1],
            task_2=task_events_list[2],
            task_3=task_events_list[3],
            task_4=task_events_list[4],
            task_5=task_events_list[5],
            current_weather_text=string.capwords(now_weather[0]["weather"]["description"]),
            current_pop=str(round(now_weather[0]["precip"])),
            current_weather_id=now_weather[0]["weather"]["code"],
            current_weather_temp=round(now_weather[0]["temp"]),
            today_weather_id=daily_forecast[1]["weather"]["code"],
            tomorrow_weather_id=daily_forecast[2]["weather"]["code"],
            dayafter_weather_id=daily_forecast[3]["weather"]["code"],
            today_weather_pop=str(round(daily_forecast[1]["pop"])),
            tomorrow_weather_pop=str(round(daily_forecast[2]["pop"])),
            dayafter_weather_pop=str(round(daily_forecast[3]["pop"])),
            today_weather_min=str(round(daily_forecast[1]["min_temp"])),
            tomorrow_weather_min=str(round(daily_forecast[2]["min_temp"])),
            dayafter_weather_min=str(round(daily_forecast[3]["min_temp"])),
            today_weather_max=str(round(daily_forecast[1]["max_temp"])),
            tomorrow_weather_max=str(round(daily_forecast[2]["max_temp"])),
            dayafter_weather_max=str(round(daily_forecast[3]["max_temp"]))
            #topic_title=topic["title"],
            #topic_text=topic["text"]


  
        ))
        htmlFile.close()
        self.logger.info('dashboard.html mis à jour')

        self.get_screenshot(path_to_server_image)
