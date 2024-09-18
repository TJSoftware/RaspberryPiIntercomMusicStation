import datetime
import os
import pika
import RPi.GPIO as GPIO
import signal
import socket
import subprocess
import time
import threading
import logging
import sys

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)

# Log to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.CRITICAL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configuration
DEVICE_ID = socket.gethostname()  # Automatically set the device ID to the hostname
RABBITMQ_HOST = 'greefkarga'
RABBITMQ_PORT = 5672
RABBITMQ_VHOST = 'vhost'
RABBITMQ_USER = 'username'
RABBITMQ_PASS = 'password'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'YourRoutingKey'
NETCAT_PORT = '12345'
BUTTON_GPIO_PIN = 17

# RabbitMQ connection parameters
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
parameters = pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_VHOST, credentials)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Global state
button_pressed = False

# Initialize the subprocess variables
arecord_process = None
aplay_process = None

def start_recording():
    global arecord_process
    if arecord_process is None:
        logger.debug("Starting recording...")

        # Start arecord and pipe to netcat in a single subprocess
        arecord_process = subprocess.Popen('arecord -f cd | nc -l -p ' + NETCAT_PORT, shell=True, preexec_fn=os.setsid)

def stop_recording():
    global arecord_process
    if arecord_process is not None:
        logger.debug("Stopping recording...")

        # Terminate the arecord process
        os.killpg(os.getpgid(arecord_process.pid), signal.SIGTERM)
        arecord_process = None

# Function to send a message to RabbitMQ
def send_message(state):
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
    
    message = f"{DEVICE_ID}: Button {'pressed' if state else 'released'} at {datetime.datetime.now()}"
    body = message.encode('utf-8')
    
    channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY, body=body)
    logger.debug(f" [x] Sent {message}")
    
    connection.close()

# Callback function for RabbitMQ messages
def on_message(ch, method, properties, body):
    message = body.decode('utf-8')
    logger.debug(f" [x] Received {message}")
    sender_id, msg = message.split(": ", 1)
    if sender_id != DEVICE_ID and message.find('pressed') >= 0:
        logger.debug("starting play")
        aplay_process = subprocess.Popen('nc ' + sender_id + ' ' + NETCAT_PORT + ' | aplay -f cd', shell=True, preexec_fn=os.setsid)
    else:
        aplay_process = None

# Thread for receiving messages
def receive_messages():
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
    result = channel.queue_declare(queue='', durable=False, exclusive=True, auto_delete=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=ROUTING_KEY)
    
    channel.basic_consume(queue=queue_name, on_message_callback=on_message, auto_ack=True)
    
    logger.info(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

# Thread for polling the button state
def poll_button():
    global button_pressed
    while True:
        current_state = GPIO.input(BUTTON_GPIO_PIN) == GPIO.LOW
        if current_state != button_pressed:
            button_pressed = current_state
            if button_pressed:
                start_recording()
            else:
                stop_recording()

            send_message(button_pressed)
        time.sleep(0.1)  # Polling interval

# Start threads for receiving messages and polling the button
receive_thread = threading.Thread(target=receive_messages)
poll_thread = threading.Thread(target=poll_button)

receive_thread.start()
poll_thread.start()

# Keep the main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.debug("Exiting...")
finally:
    GPIO.cleanup()
