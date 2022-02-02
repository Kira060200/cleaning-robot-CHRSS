from flask import Flask
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from threading import Thread
import json
import time
import eventlet

import db
import auth
import status
from controllers import automatic_empty_controller, air_controller, cleaning_controller, cleaning_schedule_controller, \
    mop_settings_controller, vacuum_settings_controller, cleaning_history_controller, environment_controller, led_controller
import controllers.map_controller

app = None
mqtt = None
socketio = None
thread = None

eventlet.monkey_patch()


def create_app(test_config=None):
    # create and configure the app
    global app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE='cleaning-robot.sqlite',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    db.init_app(app)

   # a simple page that says hello
    @app.route('/start_MQTT')
    def hello():
        global thread
        if thread is None:
            thread = Thread(target=background_thread)
            thread.daemon = True
            thread.start()
        return 'Hello, World!'

    app.register_blueprint(auth.bp)
    app.register_blueprint(environment_controller.bp)
    app.register_blueprint(cleaning_controller.bp)
    app.register_blueprint(vacuum_settings_controller.bp)
    app.register_blueprint(mop_settings_controller.bp)
    app.register_blueprint(cleaning_schedule_controller.bp)
    app.register_blueprint(cleaning_history_controller.bp)
    app.register_blueprint(air_controller.bp)
    app.register_blueprint(automatic_empty_controller.bp)
    app.register_blueprint(controllers.map_controller.bp)
    app.register_blueprint(controllers.map_controller.bp_cells)
    app.register_blueprint(led_controller.bp)

    return app

def create_mqtt_app():
    # Setup connection to mqtt broker
    app.config['MQTT_BROKER_URL'] = 'localhost'  # use the free broker from HIVEMQ
    app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
    app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
    app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
    app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
    app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

    global mqtt
    mqtt = Mqtt(app)
    global socketio
    socketio = SocketIO(app, async_mode="eventlet")

    return mqtt


# Start MQTT publishing

# Function that every second publishes a message
def background_thread():
    count = 0
    while True:
        time.sleep(1)
        # Using app context is required because the get_status() functions
        # requires access to the db.
        with app.app_context():
            message = json.dumps(status.get_status(), default=str)
        # Publish
        mqtt.publish('robot/status', message)


# App will now have to be run with `python app.py` as flask is now wrapped in socketio.
# The following makes sure that socketio is also used

def run_socketio_app():
    create_app()
    create_mqtt_app()
    socketio.run(app, host='localhost', port=5000, use_reloader=False, debug=True)


# If we run with python - this would imply to initialize the database manually
if __name__ == '__main__':
    run_socketio_app()
