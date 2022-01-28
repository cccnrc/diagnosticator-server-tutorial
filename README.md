# Diagnosticator Tutorial

This online-only application gives any [Diagnosticator](https://diagnosticator.com) registered user the chance to try it without deploy: [Diagnosticator Tutorial](https://diagnosticator-tutorial.com)

If you just wanna take the tutorial you don't need to locally deploy any of this, just go [there](https://diagnosticator-tutorial.com)

Otherwise, if you want to modify, add, improve, etc. any aspect of the tutorial, you cane easily deploy this application locally and make your changes.

To locally deploy this version you can use [Flask](https://flask.palletsprojects.com/en/2.0.x/):

1. clone the repository
```
git clone https://github.com/cccnrc/diagnosticator-server-tutorial
cd diagnosticator-server-tutorial
APP_DIR=$( pwd )
```

2. create your [Python](https://www.python.org/) (we suggest Python 3.9) virtual environment
```
python3.9 -m venv venv
```

3. store needed environment variables into `venv`, so the application loads them at any `source` activation (change `<your-application-folder>` with the pathway of the folder in which you are deploying the application: the `$APP_DIR` folder specified above)
```
echo '
export UPLOAD_FOLDER=<your-application-folder>/upload
export SERVER_ADDRESS=https://diagnosticator.com
' >> source/venv/bin/activate
```
note: with the above `echo` command you are going to [append](https://wikidiff.com/write/append) those lines to `${APP_DIR}/venv/bin/activate` file: don't append different lines multiple times! If you need to change those, delete the ones you put in `${APP_DIR}/venv/bin/activate` before!

4. activate your virtual environment and install requirements
```
source venv/bin/activate
pip install -r requirements.txt
```
note: if you find any trouble with this step this is probably due to lack of dependencies on your system.
As example, [PyMySQL](https://pypi.org/project/PyMySQL/) requires your system to have (installed and running) either [MySQL](https://www.mysql.com/) (version 5.6 or above) or [MariaDB](https://mariadb.org/) (version 10.0 or above).
If you don't have those installed you will see that the above `pip install` command will fail.
Similarly, [PyCrypto](https://pypi.org/project/pycrypto/) have similar dependencies need etc.
Look at the logs to identify which dependencies you are missing and fix each of them until you get the `pip install` command to install all packages without error.

5. create you `.flaskenv` file that will be automatically loaded by Flask. Here you can specify Flask variables:
```
echo '
FLASK_ENV=development
FLASK_APP=main.py
FLASK_DEBUG=True
FLASK_RUN_HOST=127.0.0.1
FLASK_RUN_PORT=3000
' > .flaskenv
```
as example, this will run Flask in:
- `main.py`: this simply tells Flask where is the application main file
- `development` mode: automatic reload at any detected changes, very useful for development!
- `debug` mode: lots of logs to the terminal and the browser, very useful for development as well!
- `host` and `port`: http://127.0.0.1:3000, to specify the address and port for the application

6. create the local application [sqlite](https://www.sqlite.org/index.html) database:
```
flask db init
flask db migrate
flask db upgrade
```
note: next times you will need to restart the application you have to skip the `flask db init` command, otherwise you will be thrown an error!

7. run your [Diagnosticator Tutorial](https://diagnosticator-tutorial.com) local application!
```
flask run
```

Now you can access your application through your browser at http://127.0.0.1:3000 (unless you changed host/port in `.flaskenv`).


You can also modify whatever you think it's improvable here! Don't forget to share those changes with our community through a new [GitHub branch](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches):
```
git branch <your-name>-development
git checkout <your-name>-development
git add .
git commit -m "<your-name>-development ..."
git push https://github.com/cccnrc/diagnosticator-server-tutorial.git <your-name>-development
```
note: change `<your-name>` with your [GitHub](https://github.com/) username or whatever other identifier you wish.







Looking forward to see these changes! :sunglasses:
