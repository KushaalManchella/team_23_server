from __future__ import print_function
from app import app
from flask import render_template, jsonify, request
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List
import json

'''
@app.route('/')
@app.route('/index', methods=['GET','POST'])
def index():
    user = {'username': 'Kushaal'}
    posts = [
        {
            'author': {'username': 'Arthur'},
            'body': 'Not surprised!'
        },
        {
            'author': {'username': 'Francis'},
            'body': 'I son!'
        }
    ]

    if request.method == 'POST':
        some_json = request.get_json()
        return jsonify({'you sent': some_json}), 201
    elif request.method == 'GET':
        return render_template('index.html', title='Home', user=user, posts=posts)
'''
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


def days_in_month(month: int, year: int) -> int:
    is_leap_year = bool()
    if year % 4 == 0:
        is_leap_year = True

    if month == 9 or month == 4 or month == 6 or month == 11:
        return 30
    elif month == 1 or month == 3 or month == 5 or month== 7 or month == 8 or month == 10 or month== 12:
        return 31
    elif month == 2 and is_leap_year == True:
        return 29
    elif month == 2 and is_leap_year == False:
        return 28
    else:
        return -1


def get_end_time(now: str) -> str:
    end_time = now
    month_days = days_in_month(int(now[5:7]), int(now[0:4]))
    #print(int(now[8:10]))
    #print(month_days)
    if int(now[8:10]) + 7 > month_days:   # the week moves into the next month
        temp_day = str(7 - (month_days - int(now[8:10])))
        #print("temp_day = {}".format(temp_day))
        temp_month = int(end_time[5:7])
        end_time = list(end_time)
        #print("list end_time = {}".format(end_time))
        end_time[9] = str(temp_day)
        end_time[8] = '0'
        if temp_month != 12:
            temp_month += 1
        else:
            temp_month = 1
        if len(str(temp_month)) == 1:
            end_time[5] = '0'
            end_time[6] = str(temp_month)
            end_time = ''.join(end_time)
        else:
            end_time[5], end_time[6] = str(temp_day)[0], str(temp_day)[1]
            end_time = ''.join(end_time)
        end_time = ''.join(end_time)
        #print("> month days")


    else:                                  # the week stays in the same month
        temp_day = int(end_time[8:10]) + 7
        end_time = list(end_time)
        if len(str(temp_day)) == 1:
            end_time[9] = str(temp_day)
            end_time = ''.join(end_time)
        else:
            end_time[8], end_time[9] = str(temp_day)[0], str(temp_day)[1]
            end_time = ''.join(end_time)

    return end_time


def get_events(service, now, end_time, out_dict):  # gets events and prints the output
    #print('Getting all events till 7 days from now')
    events_result = service.events().list(calendarId='primary', timeMin=now, timeMax=end_time,
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        #print(start, event['summary'])
        out_dict['events'].append({'time': start,'event': event['summary']})


    return out_dict

def add_events(event, service):
    event = service.events().insert(calendarId='primary', body=event).execute()
    #print('Event created: %s' % (event.get('htmlLink')))




@app.route('/')
@app.route('/index', methods=['GET','POST'])
def index():

    posts = [
        {
            'author': {'username': 'Kushaal'},
            'body': 'The get commands work!'
        },
        {
            'author': {'username': 'Tinu'},
            'body': 'the post commands work!'
        }
    ]

    user = {'username': 'Kushaal'}

    out_dict = {}
    out_dict['events'] = []
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
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

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    end_time = get_end_time(now)

    #print('Getting all events till 7 days from now')
    out_dict = get_events(service, now, end_time, out_dict)

    if request.method == 'POST':
        some_json = request.get_json()
        #print(some_json)
        if request.headers['Content-Type'] == 'application/json':
            #print('application/json')
            add_events(some_json, service)
            out_dict = get_events(service, now, end_time, out_dict)
            return jsonify(out_dict), 201
        return render_template('index.html', title='Home', user=user, posts=posts)
    elif request.method == 'GET':

        return jsonify(out_dict), 200
        #return render_template('index.html', title='Home', user=user, posts=posts)
