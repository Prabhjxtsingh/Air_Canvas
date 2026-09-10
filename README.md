# Air Canvas

This repository contains two versions of Air Canvas:

## Version 1: Desktop app

The original OpenCV and MediaPipe webcam application is in `version1/`.

```powershell
python -m pip install -r version1/requirements.txt
python version1/air_canvas.py
```

## Version 2: Django web app

The browser-based Django application is in `version2/`.

```powershell
python -m pip install -r requirements.txt
python version2/manage.py runserver
```

Open `http://127.0.0.1:8000/` and allow camera access. See the detailed
instructions in [version2/README.md](version2/README.md).
