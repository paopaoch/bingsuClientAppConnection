import json
import requests
import boto3
from boto3.dynamodb.conditions import Key
import math

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
    # id_key = item['company'].lower() + '_id'
    # app_id = item['id']
    items_no = int(item['item_no'])
    dynamodb = boto3.resource('dynamodb')
    emmision_table = dynamodb.Table('BingsuEmissionRate')
    user_table = dynamodb.Table('BingsuUser')
    # response_user = user_table.query(
    #     IndexName=id_key,
    #     KeyConditionExpression=Key(id_key).eq(app_id)
    # )
    response_emission = emmision_table.query(
        KeyConditionExpression=Key('uuid').eq(name)
    )
    emission_rate = float(response_emission['Items'][0]['emission_rate'])


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

    # ------Calculation------
    carbon_emission_g = emission_rate * distance_km
    carbon_scaled = 50 * math.log(carbon_emission_g + 1)
    carbon_emission_g_adj_1 = carbon_scaled * (1 + 0.00005*math.pow(avg_speed_kmph - 55, 2))
    carbon_emission_g_adj_2 = carbon_emission_g_adj_1 * (distance_km/(distance_km + 2))
    item_metrics = 1 + items_no/20
    score = carbon_emission_g_adj_2/item_metrics

    return {
        "statusCode": 200,
        "body": json.dumps({
            "distance": distance_km,
            "time" : time_hr,
            "speed" : avg_speed_kmph,
            "emission_rate" : emission_rate,
            "score" : score
            # "response_user" : response_user
        }),
    }
