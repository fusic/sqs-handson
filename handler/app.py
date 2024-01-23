import json
import boto3
from boto3.dynamodb.conditions import Key

dynamoDB = boto3.resource('dynamodb').Table('points')
sqs = boto3.resource('sqs').Queue('SQSのURL')

def addPoints(event, context):
    body = json.loads(event['body'])
    user_id = body['userId']
    points_to_add = body['points']
    message_id = body['message_id']
    # SQSにポイント更新イベントを送信
    send_to_queue(user_id, points_to_add, message_id)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Points added successfully"})
    }

def send_to_queue(user_id, points, message_id):
    # ポイント更新イベントをキューに送信
    sqs.send_message(
        MessageBody=json.dumps({'userId': user_id, 'points': points}),
        MessageDeduplicationId=message_id,
        MessageGroupId="1"
    )

# SQSによって呼び出されるメソッド
def processPointsUpdate(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        user_id = body['userId']
        points = body['points']
        ## DynamoDBからデータを取得
        queryData = dynamoDB.query(
            KeyConditionExpression = Key("userId").eq(str(user_id)), # 取得するKey情報
            Limit = 1
        )
        if queryData['Count'] == 0:
            # Dynamo上に該当ユーザーのデータがない場合は新たにレコードを作成
            dynamoDB.put_item(
                Item = {
                    "userId": user_id,
                    "points": points
                }
            )
        else:
            # Dynamo上に該当ユーザーのデータが存在する場合は既存のレコードを更新
            # DynamoDBにポイントを追加
            response = dynamoDB.update_item(
                Key={'userId': str(user_id)},
                UpdateExpression='ADD points :val',
                ExpressionAttributeValues={':val': points},
                ReturnValues='UPDATED_NEW'
            )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Points updated successfully"})
    }
