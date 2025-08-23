## Getting started
Run following commands

1. `python3 -m venv automation_env` //1st time only
2. `. automation_env/bin/activate` //to activate environment
3. `deactivate` //to deactivate environment
4. `pip install requirements.txt` //install all the app dependencies
5. `flask --app main --debug run` or `python main.py` //to run the web application

## To deploy on vercel

1. `pip freeze > requirements.txt`
2. https://www.youtube.com/watch?v=LaMVBDbUtMA
3. login to vercel => `vercel login`
4. trigger deployment => `vercel .`
