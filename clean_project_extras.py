import subprocess

# Pacotes problemáticos que incham a imagem
bloat = [
    "kubernetes",
    "posthog",
    "watchfiles",
    "pillow",
    "scikit-learn",
    "scipy",
    "sympy",
    "markdown-it-py",
    "mdurl",
    "Pygments",
    "tokenizers",
    "transformers",
    "onnxruntime",
    "regex",
    "huggingface-hub",
    "joblib",
    "networkx",
    "safetensors",
    "shellingham",
    "colorama",
    "pyreadline3",
    "humanfriendly",
    "rich"
]

for pacote in bloat:
    subprocess.call(["pip", "uninstall", "-y", pacote])
