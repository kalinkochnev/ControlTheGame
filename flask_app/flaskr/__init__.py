import os

from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # inits db
    from . import database as db
    db.init_app(app)

    """# Checks if the game watcher is already running
    if not werkzeug.serving.is_running_from_reloader():
        start_tracking()

    @app.route("/")
    def home():
        if current_state is not None:
            return str(current_state.currently_running)
        else:
            return str("No games running")"""

    return app

"""
def start_tracking():
    calculator = cg.GameObject.min_init("Calculator", 100)
    # chrome = GameObject.min_init("Chrome", 5)
    discord = cg.GameObject.min_init("Discord", 100)

    settings = cg.Settings(1, 5, calculator, discord)

    tracker = cg.Tracker(settings)
    # TODO figure out how to get the current state and display it
    global current_state
    current_state = cg.CurrentState(settings)
    manager = cg.GameManager()

    print("Starting tracker...")
    tracker.start()
    while True:
        current_state.update_running()
        manager.run(current_state)

        now = datetime.now().strftime("%c")
        print(f"------ {now} ------")
        time.sleep(settings.loop_time)
        print("\n")"""