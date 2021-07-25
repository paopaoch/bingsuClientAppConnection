import json
import requests
import boto3
from boto3.dynamodb.conditions import Key
import math

def calculate_points(event, context):
    item = event['arguments']
    source = item['source']
    dest = item['dest']
    name = item['name']
    if item['id_user']:
        id_type='user'
    else:
        id_type = item['company'].lower()
    id_key = id_type + '_id'
    app_id = item['id']
    write = item['write']
    restaurant_name = item['restaurant']
    items_no = int(item['item_no'])
    dynamodb = boto3.resource('dynamodb')


    user_table = dynamodb.Table('BingsuUser')
    if item['id_user']:
        response_user = user_table.query(
            KeyConditionExpression=Key(id_key).eq(app_id)
        )
    else:
        response_user = user_table.query(
            IndexName=id_key,
            KeyConditionExpression=Key(id_key).eq(app_id)
        )
        
    old_points = int(response_user['Items'][0][item['company'].lower() + '_points'])


    emmision_table = dynamodb.Table('BingsuEmissionRate')
    response_emission = emmision_table.query(
        KeyConditionExpression=Key('uuid').eq(name)
    )
    emission_rate = float(response_emission['Items'][0]['emission_rate'])


    # # ------For finding distance, time, speed------
    location_service = boto3.client('location')

    location_response = location_service.calculate_route(
        CalculatorName='GetDistanceTimeForDelivery',
        CarModeOptions={
            'AvoidFerries': True,
            'AvoidTolls': False
        },
        DepartNow=True,
        DeparturePosition=source,
        DestinationPosition=dest,
        DistanceUnit='Kilometers',
        TravelMode='Car',
    )
    distance_km = location_response['Summary']['Distance']
    time_hr = location_response['Summary']['DurationSeconds'] / 3600
    avg_speed_kmph = distance_km / time_hr

    # # ------Calculation------
    carbon_emission_g = emission_rate * distance_km
    carbon_scaled = 50 * math.log(carbon_emission_g + 1)
    carbon_emission_g_adj_1 = carbon_scaled * (1 + 0.00005*math.pow(avg_speed_kmph - 55, 2))
    carbon_emission_g_adj_2 = carbon_emission_g_adj_1 * (distance_km/(distance_km + 2))
    item_metrics = 1 + items_no/20
    score = carbon_emission_g_adj_2/item_metrics
    old_score = 500 - old_points/10
    new_score = (old_score + score)/2
    new_points = int(10*(500 - new_score))

    new_carbons = float(response_user['Items'][0]['co2_amount']) + carbon_emission_g

    # # ------Writing to database------
    if write:    
        client_lambda = boto3.client('lambda')
        arguments = {
            "user_id": response_user['Items'][0]['user_id'],
            item['company'].lower() + '_points': new_points,
            "co2_amount": new_carbons,
        }

        update_user_response = client_lambda.invoke(
            FunctionName = 'arn:aws:lambda:ap-southeast-1:405742985670:function:bingsuUser-UpdateUserFunction-9I54tc4Xyb2h',
            InvocationType = 'RequestResponse',
            Payload = json.dumps({'arguments': arguments})
        )
        update_user_status =  json.load(update_user_response['Payload'])

        arguments = {
            "user_id": response_user['Items'][0]['user_id']
            ,"points_amount": new_points - old_points
            ,"company_name": item['company'].lower()
            ,"co2_amount": carbon_emission_g
            ,"restaurant_name": restaurant_name
            ,"distance": distance_km
            ,"item": items_no
        }
        insert_trans_response = client_lambda.invoke(
            FunctionName = 'arn:aws:lambda:ap-southeast-1:405742985670:function:bingsuPointsTrans-AddPointsTransFunction-p02oBr9UtPyz',
            InvocationType = 'RequestResponse',
            Payload = json.dumps({'arguments': arguments})
        )
        insert_trans_status =  json.load(insert_trans_response['Payload'])
        
        carbon_emission_g = 0
        new_points = 0

    else:
        update_user_status = "write was false"
        insert_trans_status = "write was false"
    return {
        "statusCode": 200,
        "body": {
            "carbon_emission_g" : carbon_emission_g,
            "points" : new_points - old_points,
            "save_status": update_user_status,
            "insert_status": insert_trans_status
        },
    }


def get_external_client_id_mock_up(event, context):
    from uuid import uuid4
    item = event['arguments']
    user_id = item['user_id']
    company = item['company']
    company_id = str(uuid4())

    client_lambda = boto3.client('lambda')
    arguments = {
        "user_id": user_id,
        company + '_id': company_id
    }
    update_user_response = client_lambda.invoke(
        FunctionName = 'arn:aws:lambda:ap-southeast-1:405742985670:function:bingsuUser-UpdateUserFunction-9I54tc4Xyb2h',
        InvocationType = 'RequestResponse',
        Payload = json.loads({'arguments': arguments})
    )
    update_user_status =  json.load(update_user_response['Payload'])
    return {'save_status': update_user_status, company + '_id': company_id}