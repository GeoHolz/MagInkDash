#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run this script first to obtain the token. Credentials.json must be in the same folder first.
To obtain Credentials.json, follow the instructions listed in the following link.
https://developers.google.com/calendar/api/quickstart/python
"""

from __future__ import print_function
import datetime
import pickle
import os.path
import json
import logging
import sys
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from render.render import RenderHelper
from pytz import timezone
from datetime import datetime as dt
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from datetime import timedelta

now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
now_day = datetime.datetime.now()
tomorrow_day=datetime.datetime.now() + timedelta(days=1)
now_day = now_day.strftime("%d-%m")
tomorrow_day=tomorrow_day.strftime("%d-%m")




# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
def is_multiday(start, end):
    # check if event stretches across multiple days
    return start.date() != end.date()

def get_weather(when,apikey,postal_code,country,lang):
    if(when=="now"):
        url="https://api.weatherbit.io/v2.0/current?key={}&postal_code={}&country={}&lang={}".format(apikey,postal_code,country,lang)
    else:
        url="https://api.weatherbit.io/v2.0/forecast/daily?key={}&postal_code={}&country={}&lang={}&days=4".format(apikey,postal_code,country,lang)
    response = requests.get(url)
    data = json.loads(response.text)
    weather = data["data"]

    return weather
def date_is_today(today,now_day,tomorrow_day):
    
    if(today == now_day):
        today="Aujourd'hui"  
    elif(today == tomorrow_day):
        today="Demain" 
    else:
        today="Le " + today
    return today
def set_event_format(event):
    if(event['start'].get('date', event['start'].get('date'))):
        # Journée entiere, mise en forme date de debut
        start = event['start'].get('date', event['start'].get('date'))
        tmpstart = datetime.datetime.strptime(start,'%Y-%m-%d')
        start = tmpstart.strftime('%d-%m')
        # Journée entiere, mise en forme date de fin
        end = event['end'].get('date', event['end'].get('date'))
        tmpend = datetime.datetime.strptime(end,'%Y-%m-%d')
        end = tmpend + datetime.timedelta(days=-1)
        end = end.strftime('%d-%m')
       
        if(tmpend.strftime('%d-%m-%Y') == tmpstart.strftime('%d-%m-%Y')):
            end = tmpend.strftime('%H:%M')
            jour=date_is_today(tmpend.strftime('%d-%m'),now_day,tomorrow_day)
            return(jour + " de " + tmpstart.strftime('%H:%M') + " à " + tmpend.strftime('%H:%M') + " : " + event['summary'])
        else:
            if(start==end) :
                jour=date_is_today(end,now_day,tomorrow_day)
                return(jour + " : " + event['summary'])
            else:
                return("Du " + start + " au " + end + " : " + event['summary'])
    else:
        start = event['start'].get('dateTime', event['start'].get('date'))
        tmpstart=datetime.datetime.strptime(start,'%Y-%m-%dT%H:%M:%S+02:00')
        start = tmpstart.strftime('%d-%m %H:%M')
        end = event['end'].get('dateTime', event['end'].get('date'))
        tmpend = datetime.datetime.strptime(end,'%Y-%m-%dT%H:%M:%S+02:00')
        end = tmpend.strftime('%d-%m %H:%M')
    
        if(tmpend.strftime('%d-%m-%Y') == tmpstart.strftime('%d-%m-%Y')):
            end = tmpend.strftime('%H:%M')
            jour=date_is_today(tmpend.strftime('%d-%m'),now_day,tomorrow_day)
            return(jour + " de " + tmpstart.strftime('%H:%M') + " à " + tmpend.strftime('%H:%M') + " : " + event['summary'])
        else:
            return("Du " + start + " au " + end + " : " + event['summary'])

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    now_day = datetime.datetime.now()
    tomorrow_day=datetime.datetime.now() + timedelta(days=1)
    now_day = now_day.strftime("%d-%m")
    tomorrow_day=tomorrow_day.strftime("%d-%m")
    
    creds = None
    # Basic configuration settings (user replaceable)
    configFile = open('config.json')
    config = json.load(configFile)
    calendarsID = config['calendars'] # Google Calendar IDs
    calendarsID2 = config['calendars2'] # Google Calendar IDs
    birthday_calendars = config['birthday_calendars'] # Google Calendar IDs
    displayTZ = timezone(config['displayTZ']) # list of timezones - print(pytz.all_timezones)
    imageWidth = config['imageWidth']  # Width of image to be generated for display.
    imageHeight = config['imageHeight']  # Height of image to be generated for display.
    rotateAngle = config['rotateAngle']  # If image is rendered in portrait orientation, angle to rotate to fit screen
    path_to_server_image = config["path_to_server_image"]  # Location to save the generated image
    weatherbit_api_key = config["weatherbit_api_key"]
    weatherbit_postal_code = config["weatherbit_postal_code"]
    weatherbit_country = config["weatherbit_country"]
    weatherbit_lang = config["weatherbit_lang"]

   # Logger 
    logger = logging.getLogger('maginkdash')
    logging.basicConfig(filename="logfile.log", format='%(asctime)s %(levelname)s - %(message)s', filemode='a')
    logger = logging.getLogger('maginkdash')
    logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
    logger.setLevel(logging.INFO)
    logger.info("******" + now + "**************Starting dashboard update****************************************")

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds,cache_discovery=False)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId=calendarsID, timeMin=now,
                                        maxResults=12, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    eventList= []
    if not events:
        print('No upcoming events found.')
    for event in events:
        eventList.append(set_event_format(event))
    print(eventList)
    
############################### ANNIVERSAIRE ############################################################
    # Call the Calendar API
    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    # now_day = datetime.datetime.now()
    # now_day = now_day.strftime("%d-%m")
    events_result_birthday = service.events().list(calendarId=birthday_calendars, timeMin=now,
                                        maxResults=5, singleEvents=True,
                                        orderBy='startTime').execute()
    events_birthday = events_result_birthday.get('items', [])

    eventListBirthday= []

    if not events:
        print('No upcoming events found.')
    for event_birthday in events_birthday:
        start_birthday = event_birthday['start'].get('dateTime', event_birthday['start'].get('date'))
        tmpstart = datetime.datetime.strptime(start_birthday,'%Y-%m-%d')
        start_birthday = tmpstart.strftime('%d-%m')
        start_birthday = date_is_today(start_birthday,now_day,tomorrow_day)
        eventListBirthday.append(start_birthday + " : " + event_birthday['summary'].replace(' - Anniversaire',''))
    print(eventListBirthday)       



    
    
############################### TASK d9ed82ea5c838200ae35f8f47e7c6ea5b21cded3259095a853c7fd42688e2144@group.calendar.google.com ############################################################
    events_result_maison = service.events().list(calendarId=calendarsID2, timeMin=now,
                                        maxResults=5, singleEvents=True,
                                        orderBy='startTime').execute()
    events_maison = events_result_maison.get('items', [])

    eventListmaison= []
    if not events:
        print('No upcoming events found.')
    for event_maison in events_maison:
        eventListmaison.append(set_event_format(event_maison))
    print(eventListmaison)       

    currDate = dt.now(displayTZ).date()

    ## Retrieve Weather Data
    daily_forecast = get_weather("daily",weatherbit_api_key,weatherbit_postal_code,weatherbit_country,weatherbit_lang)
    now_weather=get_weather("now",weatherbit_api_key,weatherbit_postal_code,weatherbit_country,weatherbit_lang)
    ## Render
    renderService = RenderHelper(imageWidth, imageHeight, rotateAngle)
    renderService.process_inputs(currDate, daily_forecast, eventList, path_to_server_image,eventListBirthday,eventListmaison,now_weather)
    logger.info("Completed dashboard update")
if __name__ == '__main__':
    main()