import json
import requests
import boto3
from boto3.dynamodb.conditions import Key

# item = event['arguments']
# user_id = item['user_id']
# dynamodb = boto3.resource('dynamodb')

# table = dynamodb.Table(os.environ.get('BINGSU_USER_TABLE_NAME'))
# response = table.query(
#     KeyConditionExpression=Key('user_id').eq(user_id)
# )
# return {'status': 200,
#         'data': response['Items']}

def lambda_handler(event, context):
    item = event['arguments']
    source = item['source']
    dest = item['dest']
    name = item['name']
    id_key = item['company'].lower() + '_id'
    app_id = item['id']
    dynamodb = boto3.resource('dynamodb')
    emmision_table = dynamodb.Table('BingsuEmissionRate')
    user_table = dynamodb.Table('BingsuUser')
    response_user = user_table.query(
        IndexName=id_key,
        KeyConditionExpression=Key(id_key).eq(app_id)
    )
    response_emission = emmision_table.query(
        KeyConditionExpression=Key('uuid').eq(name)
    )
    emission_rate = response_emission['Items'][0]['emission_rate']


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
            "speed" : avg_speed_kmph,
            "emission_rate" : emission_rate,
            "response_user" : response_user
        }),
    }
