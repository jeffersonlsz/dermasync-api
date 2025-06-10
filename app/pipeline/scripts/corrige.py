import json

# Arquivo de entrada e saída (pode ser o mesmo se quiser sobrescrever)
input_file = 'app/pipeline/dados/jsonl_enriquecidos/relatos_enriquecidos-20250609.jsonl'
output_file = 'app/pipeline/dados/jsonl_enriquecidos/relatos_enriquecidos-20250609-n.jsonl'

with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
    for line in f_in:
        # Carrega o JSON da linha atual
        data = json.loads(line.strip())
        
        # Adiciona o campo 'origem': 'local'
        data['origem'] = 'local'
        
        # Escreve a linha modificada no arquivo de saída
        f_out.write(json.dumps(data, ensure_ascii=False) + '\n')

print(f"Campo 'origem':'local' adicionado a todas as linhas. Arquivo salvo em: {output_file}")