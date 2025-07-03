import base64
from io import BytesIO

from PIL import Image


def gerar_imagem_fake_base64() -> str:
    # Gera uma imagem RGB simples (100x100)
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
