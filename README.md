# Air Canvas

This repository contains two versions of Air Canvas:

## Version 1: Desktop app

The original OpenCV and MediaPipe webcam application is in `version1/`.

```powershell
python -m pip install -r version1/requirements.txt
python version1/air_canvas.py
```

## Version 2: Django web app

The browser-based Django application is in the repository root. The original
desktop application remains in `version1/`.

The hosted static version is deployed by GitHub Pages at:
`https://prabhjxtsingh.github.io/Air_Canvas/`

```powershell
python -m pip install -r requirements.txt
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and allow camera access. See the detailed
instructions in [version2/README.md](version2/README.md).

The GitHub Pages version uses the browser download for PNG saving. The local
Django version also stores a server copy in `media/`.

## Project layout

- `version1/` — original desktop OpenCV and MediaPipe application
- `manage.py`, `config/`, `aircanvas/` — Version 2 Django application
- `index.html`, `static/` — GitHub Pages browser entry point and assets
- `.github/workflows/deploy-pages.yml` — automatic Pages deployment
