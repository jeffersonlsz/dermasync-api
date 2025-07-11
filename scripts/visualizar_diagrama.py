import webbrowser
from pathlib import Path

TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Diagrama Mermaid</title>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true });
  </script>
</head>
<body>
  <pre class="mermaid">
{conteudo}
  </pre>
</body>
</html>
"""


def gerar_html(mmd_path: str):
    caminho = Path(mmd_path)
    if not caminho.exists():
        print(f"[ERRO] Arquivo {mmd_path} não encontrado.")
        return

    conteudo = caminho.read_text(encoding="utf-8")
    html = TEMPLATE_HTML.replace("{conteudo}", conteudo)

    html_path = caminho.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    print(f"[OK] HTML gerado em: {html_path}")
    webbrowser.open(str(html_path.absolute()))


if __name__ == "__main__":
    gerar_html("outputs/fluxo_req_001.mmd")
