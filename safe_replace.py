import sys

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('images_refs', 'image_refs')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

files = [
    'app/schema/relato.py',
    'app/routes/galeria_leitura.py',
    'app/services/feed/feed_mapper.py',
    'app/services/image_exposure_projector.py',
    'app/services/relato_adapters.py',
    'app/services/relato_normalizer.py'
]

for f in files:
    replace_in_file(f)

print("Tracked files updated.")
