#Quick install script for OpenRelay
sudo apt-get install git-core python-virtualenv python-pip
git clone git@github.com:Captainkrtek/OpenRelay.git
virtualenv --no-site-packages OpenRelay
cd OpenRelay
source OpenRelay/bin/activate
sudo pip install -r requirements/production.txt
git submodule init
git submodule update
python manage.py syncdb
./runserver.sh start
google-chrome http://127.0.0.1:8000
