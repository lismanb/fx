from fx.fxrates import create_app
import os

os.environ.setdefault("FXRATES_SETTINGS", "conf/fxrates.cfg")

application = create_app()