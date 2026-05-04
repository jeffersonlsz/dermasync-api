# run_tests.py
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import webbrowser


def limpar_relatorios_antigos():
    print("Limpando relatórios anteriores...")
    for path in ["htmlcov", "report.json", "logs_testes.jsonl"]:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _build_pytest_command():
    cmd = [sys.executable, "-m", "pytest", "tests/"]

    has_cov = _module_available("pytest_cov")
    has_json_report = _module_available("pytest_jsonreport")

    if has_cov:
        cmd.extend(["--cov=app", "--cov-report=html"])
    else:
        print("Aviso: plugin pytest-cov não encontrado. Cobertura HTML será ignorada.")

    if has_json_report:
        cmd.extend(["--json-report", "--json-report-file=report.json"])
    else:
        print("Aviso: plugin pytest-json-report não encontrado. report.json não será gerado.")

    return cmd


def rodar_pytest():
    print("Rodando Pytest...\n")
    cmd = _build_pytest_command()
    print("Comando:", " ".join(cmd))
    result = subprocess.run(cmd, text=True)
    return result.returncode


def abrir_htmlcov():
    index_path = os.path.abspath("htmlcov/index.html")
    if not os.path.exists(index_path):
        print("\nRelatório de cobertura HTML não foi gerado.")
        return

    print(f"\nAbrindo relatório de cobertura: {index_path}")
    try:
        webbrowser.open(f"file://{index_path}")
    except Exception as exc:
        print(f"Erro ao abrir navegador: {exc}")


def mostrar_resumo_teste():
    if not os.path.exists("report.json"):
        print("Arquivo report.json não encontrado.")
        return

    try:
        with open("report.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        summary = data.get("summary", {})
        print("\nResumo dos testes:")
        print(f"   Passaram: {summary.get('passed', 0)}")
        print(f"   Falharam: {summary.get('failed', 0)}")
        print(f"   Total:     {summary.get('total', 0)}")

        if summary.get("failed", 0) > 0:
            print("\nAlguns testes falharam. Verifique detalhes no report.json e logs/test.log")
    except Exception as exc:
        print(f"Erro ao ler report.json: {exc}")


def main():
    limpar_relatorios_antigos()
    exit_code = rodar_pytest()
    mostrar_resumo_teste()
    abrir_htmlcov()

    if exit_code != 0:
        print("\nExecução finalizada com falhas.")
    else:
        print("\nExecução finalizada com sucesso.")

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
