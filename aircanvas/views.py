import base64
import binascii
import uuid
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST


def canvas(request):
    return render(request, "aircanvas/canvas.html")


@require_POST
def save_drawing(request):
    image_data = request.POST.get("image", "")
    if not image_data.startswith("data:image/png;base64,"):
        return JsonResponse({"error": "Expected a PNG data URL."}, status=400)

    try:
        image_bytes = base64.b64decode(image_data.split(",", 1)[1], validate=True)
    except (ValueError, binascii.Error):
        return JsonResponse({"error": "Invalid PNG data."}, status=400)

    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    filename = f"drawing-{uuid.uuid4().hex[:10]}.png"
    output_path = media_root / filename
    output_path.write_bytes(image_bytes)

    return JsonResponse({"filename": filename, "url": f"/media/{filename}"})
