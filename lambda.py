"""
First Lambda Function: serializeImageData
"""
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    
    key = event['s3_key']
    bucket = event['s3_bucket']

    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket,key,'/tmp/image.png')

    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

"""
Second Lambda Function: classifyImage
"""
import json
import base64
import boto3
#from sagemaker.serializers import IdentitySerializer
#from sagemaker.predictor import Predictor

runtime = boto3.client('runtime.sagemaker')
#session = boto3.session()

# Fill this in with the name of your deployed model
ENDPOINT = "image-classification-2022-02-27-05-27-17-852"

def lambda_handler(event, context):

    # Decode the image data
    image = base64.b64decode(event['body']['image_data'])
    
    # invoke endpoint
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT,ContentType ='image/png',Body=image)

    # Make a prediction:
    inferences = json.loads(response['Body'].read())

    # We return the data back to the Step Function
    event['body']["inferences"] = inferences

       
    return {
        'statusCode': 200,
        'body': event['body']
    }

"""
Third Lambda Function: thresholdPrediction
"""

import json


THRESHOLD = .93


def lambda_handler(event, context):

    # Grab the inferences from the event
    inferences = event['body']['inferences']
    
    # input from previous lambda comes out as strings for some reason, 
    # so extract string version of inferences, then convert into a list of inferences
    
    #extract_inferences_from_string = event['body'][-43:-2]
    #str_inferences = extract_inferences_from_string.split(', ')
    #inferences = [float(inference) for inference in str_inferences]

    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = any(val > THRESHOLD for val in inferences)

    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': event['body']
    }