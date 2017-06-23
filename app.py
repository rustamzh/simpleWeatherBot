from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
import os.path
import sys
import json
import requests
import time
import datetime
import config

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai


app = Flask(__name__)

app.secret_key = config.SECRET_KEY


@app.route("/",methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.form['msg']
        if 'hist' not in session:
            session['hist'] = '[]'
        msglist = json.loads(session['hist'])
        msglist.append({'msg':message, 'sender':'Me'})
        if 'clear' in request.form:
            msglist = []
        else:
            msglist.append({'msg':handleConnection(app.secret_key, message), 'sender':'Bot'})
        session['hist'] = json.dumps(msglist)
        return render_template('index.html', messages=msglist)
    else:
        if 'hist' not in session:
            session['hist'] = '[]'
        msglist = json.loads(session['hist'])
        return render_template('index.html', messages=msglist)





def handleConnection(sessionId, query):
    ai = apiai.ApiAI(config.CLIENT_ACCESS_TOKEN)

    requestAI = ai.text_request()

    requestAI.lang = 'en'  # optional, default value equal 'en'

    requestAI.session_id = sessionId

    requestAI.query = query

    responseAI = requestAI.getresponse()

    res = json.loads(responseAI.read().decode("utf-8"))
    
    if res['result']['fulfillment']['speech']:
        res = res['result']['fulfillment']['speech']
    elif res['alternateResult']['fulfillment']['speech']:
        res = res['alternateResult']['fulfillment']['speech']
    elif 'action' in res['result'] and res['result']['action'] == 'weather' and res['result']['parameters']['date-time']:
        try:
            s=time.mktime(datetime.datetime.strptime(res['result']['parameters']['date-time'], "%Y-%m-%d").timetuple())
        except: 
            return "Error: unsupported yet"
        r=requests.get('http://api.apixu.com/v1/forecast.json?key=' + config.WEATHER_API_KEY +'&q='+res['result']['parameters']['address']['city']+ '&unixdt='+str(s))
        weather = r.json()
        temp = weather['forecast']['forecastday'][0]['day']['avgtemp_c']
        res= res['result']['parameters']['date-time']+" in " + weather['location']['name'] +": "+weather['forecast']['forecastday'][0]['day']['condition']['text']+" - "+ str(temp) + " C"

    elif 'action' in res['result'] and res['result']['action'] == 'weather':
        r=requests.get('http://api.apixu.com/v1/current.json?key=' + config.WEATHER_API_KEY +'&q='+res['result']['parameters']['address']['city'])
        weather = r.json()
        temp = weather['current']['temp_c']
        res= "Today in " + weather['location']['name'] +": "+weather['current']['condition']['text']+" - "+ str(temp) + " C"
   
    return res


if __name__ == "__main__":
    app.run(port=int(os.environ["PORT"]),host=(os.environ["IP"]))
