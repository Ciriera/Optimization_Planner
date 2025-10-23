cd frontend; $env:DANGEROUSLY_DISABLE_HOST_CHECK="true"; npm start

py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000