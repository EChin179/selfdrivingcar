import socketio
import eventlet
import numpy as np
# sockets are used to perform real time communication between a client and a Server
# it listens for new events from the server allowing us to continuously update the client with data
from flask import Flask
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import cv2

sio = socketio.Server()

app = Flask(__name__) # '__main__'
speed_limit = 30

# preprocessing data and preparing it for use
def img_preprocess(img):
  # removing noise by cropping image (removing scenery, car hood, etc)
  img = img[60:135, :, :]
  img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
  # Gaussian blur smoothes out an image and reduces its noise
  img = cv2.GaussianBlur(img, ksize=(3, 3), sigmaX=0)
  # decreasing image size allows for faster computation
  img = cv2.resize(img, (200, 66))
  img = img / 255
  return img

# listening for updates that will be sent from the telemetry from the simulator
@sio.on('telemetry')
def telemetry(sid, data):
    speed = float(data['speed'])
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    image = np.array([image])
    steering_angle = float(model.predict(image))
    throttle = 1.0 - speed / speed_limit
    print('{} {} {}'.format(steering_angle, throttle, speed))
    send_control(steering_angle, throttle)


@sio.on('connect')
def connect(sio, environ):
    print('Connected!')
    send_control(0, 1)

# send the car a straight steering angle and a full throttle
def send_control(steering_angle, throttle):
    sio.emit('steer', data = {
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })

if __name__ == '__main__':
    model = load_model('model.h5')
    app = socketio.Middleware(sio, app)
    # using wsgi to send requests made by the client to the web application
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
