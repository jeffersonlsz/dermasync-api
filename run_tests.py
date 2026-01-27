# run_tests.py
import json
import os
import platform
import subprocess
import webbrowser


def limpar_relatorios_antigos():
    print("🧹 Limpando relatórios anteriores...")

    paths = ["htmlcov", "report.json", "logs_testes.jsonl"]

    for path in paths:
        if os.path.isdir(path):
            import shutil

            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


def rodar_pytest():
    print("✅ Rodando Pytest com cobertura e relatório JSON...\n")

    result = subprocess.run(
        [
            "pytest",
            "--cov=app",
            "--cov-report=html",
            "--json-report",
            "--json-report-file=report.json",
            "tests/",
        ],
        text=True,
    )

    return result.returncode


def abrir_htmlcov():
    index_path = os.path.abspath("htmlcov/index.html")
    print(f"\n📂 Abrindo relatório de cobertura: {index_path}")
    try:
        webbrowser.open(f"file://{index_path}")
    except Exception as e:
        print(f"⚠️ Erro ao abrir navegador: {e}")


def mostrar_resumo_teste():
    if not os.path.exists("report.json"):
        print("⚠️ Arquivo report.json não encontrado.")
        return

    try:
        with open("report.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        summary = data.get("summary", {})
        print("\n📊 Resumo dos testes:")
        print(f"   ✅ Passaram: {summary.get('passed', 0)}")
        print(f"   ❌ Falharam: {summary.get('failed', 0)}")
        print(f"   🧪 Total:     {summary.get('total', 0)}")

        if summary.get("failed", 0) > 0:
            print(
                "\n🚨 Alguns testes falharam. Verifique detalhes no report.json e logs_testes.jsonl"
            )

    except Exception as e:
        print(f"⚠️ Erro ao ler report.json: {e}")


def main():
    limpar_relatorios_antigos()

    exit_code = rodar_pytest()

    mostrar_resumo_teste()
    abrir_htmlcov()

    if os.path.exists("logs_testes.jsonl"):
        print("\n🗃️  Logs dos testes salvos em: logs_testes.jsonl")

    if exit_code != 0:
        print("\n❌ Execução finalizada com falhas.")
    else:
        print("\n✅ Execução finalizada com sucesso.")


if __name__ == "__main__":
    main()
