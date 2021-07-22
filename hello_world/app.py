import json
import requests
import boto3


def lambda_handler(event, context):
    item = event['arguments']
    source = item['source']
    dest = item['dest']

    # ------For finding distance, time, speed------
    api_key ='AIzaSyBiOi79T_MesgMRTSnHqcCmlfLEFpNEjq8' 
    url ='https://maps.googleapis.com/maps/api/distancematrix/json?'
    
    r = requests.get(url + 'origins=' + source +
                    '&destinations=' + dest +
                    '&departure_time=now' +
                    '&key=' + api_key)
    x = r.json()

    distance_km = int(x['rows'][0]['elements'][0]['distance']['value']) / 1000
    time_hr = int(x['rows'][0]['elements'][0]['duration']['value']) / 3600
    avg_speed_kmph = distance_km / time_hr

    return {
        "statusCode": 200,
        "body": json.dumps({
            "distance": distance_km,
            "time" : time_hr,
            "speed" : avg_speed_kmph
        }),
    }
