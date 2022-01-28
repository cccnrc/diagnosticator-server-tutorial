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

3. store needed environment variables into `venv`, so the application loads them at any activation (`source`)
```
echo '
export UPLOAD_FOLDER=<your-application-folder>/upload
export SERVER_ADDRESS=https://diagnosticator.com
' >> source/venv/bin/activate
source venv/bin/activate
```
note: with the above `echo` command you are going to [append](https://wikidiff.com/write/append) those lines to `${APP_DIR}/venv/bin/activate` file: don't append different lines multiple times! If you need to change those, delete the ones you put in `${APP_DIR}/venv/bin/activate` before!

4. create you `.flaskenv` file that will be automatically loaded by Flask. Here you can specify Flask variables:
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
















###
