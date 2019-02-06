# Set up
# make sure your configuration variables are correct with your local setup.
virtualenv fxtrade
pip install -r requirements
flask init-db

export FXRATES_SETTINGS="conf/fxrates.cfg"
export FLASK_APP="fx.fxrates"

python run.py