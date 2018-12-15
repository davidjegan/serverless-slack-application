import os
import urllib
import boto3


#input
VERIFICATION_TOKEN = os.environ['VERIFICATION_TOKEN']  
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']  


SUPPORTED_TYPES = ['image/jpg', 'image/png', 'image/jpeg']  
MAX_SIZE = 5242880 
rekognition = boto3.client('rekognition')


def check_token(event):
    #Checks incoming token with existing token
    if event['token'] != VERIFICATION_TOKEN:
        print('Invalid token')
        return False
    return True


def confirm_event(event):
    #Validates image attributes and size

    event_details = event['event']
    file_subtype = event_details.get('subtype')
    file_details = event_details['file']
    mime_type = file_details['mimetype']
    file_size = file_details['size']

    if file_subtype != 'file_share':
        print('Not a file_shared event')
        return False
    if mime_type not in SUPPORTED_TYPES:
        print('File is not an image')
        return False
    if file_size > MAX_SIZE:
        print('Image is larger than 5MB')
        return False

    return True


def download_image(url):
    # Download image from private Slack URL using bearer token authorization.
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer %s' % ACCESS_TOKEN})
    return urllib.request.urlopen(request).read()


def detect_attribute(image_bytes):
    # Checks image for label using Amazon Rekoginition
    try:
        response = rekognition.detect_labels(Image={'Bytes': image_bytes,},MinConfidence=80.0)
    except Exception as e:
        raise(e)
    labels = response['Labels']
    if any(label['Name'] == 'Animal' for label in labels):
        return True
    return False


def post_message(channel, message):
    #Posts message to Slack channel via Slack API.
    url = 'https://slack.com/api/chat.postMessage'
    data = urllib.parse.urlencode((("token", ACCESS_TOKEN),("channel", channel),("text", message)))
    data = data.encode("ascii")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    request = urllib.request.Request(url, data, headers)
    urllib.request.urlopen(request)


def lambda_handler(event, context):
    if not check_token(event):  
        return

    if event.get('challenge') is not None:  
        challenge = event['challenge']
        return {'challenge': challenge}

    if not confirm_event(event):  
        return
    #extract data 
    event_details = event['event']
    file_details = event_details['file']
    channel = event_details['channel']
    url = file_details['url_private']
    file_id = file_details['id']

    image_bytes = download_image(url)
    is_animal = detect_attribute(image_bytes)
    message = ""
    if is_animal:
        print('Attribute detected')
        message = 'Wow!! Thats an Animal!!!'
    else:
        print('Attribute not detected')
        message = 'No. This is not an Animal.'
    post_message(channel, message)