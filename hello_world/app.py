import json

# import requests
import boto3


def lambda_handler(event, context):
    client = boto3.client('location')

    response = client.calculate_route(
        CalculatorName='GetDistanceTimeForDelivery',
        CarModeOptions={
            'AvoidFerries': True,
            'AvoidTolls': False
        },
        DepartNow=True,
        DeparturePosition=[
            13.725520, 100.584480
        ],
        DestinationPosition=[
            13.737418, 100.399955,
        ],
        DistanceUnit='Kilometers',
        TravelMode='Car',
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
