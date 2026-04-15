import json
from pathlib import Path
from collections import Counter

# Define o caminho para a pasta onde estão os seus JSONs
pasta_jsons = Path('./FS_col11_json')

# Inicializa o contador (ele vai somar a frequência de cada feature automaticamente)
contador_features = Counter()

# Verifica se a pasta existe
if not pasta_jsons.exists():
    print(f"❌ A pasta {pasta_jsons} não foi encontrada.")
else:
    print(f"📂 Lendo arquivos JSON na pasta: {pasta_jsons}...")
    
    # Busca todos os arquivos .json dentro da pasta
    arquivos = list(pasta_jsons.glob('*.json'))
    
    for arquivo in arquivos:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
                # Extrai a lista da chave 'features' (se não existir, retorna lista vazia)
                features_do_arquivo = dados.get('features', [])
                
                # Atualiza o contador com as features deste arquivo
                contador_features.update(features_do_arquivo)
                
        except Exception as e:
            print(f"⚠️ Erro ao ler o arquivo {arquivo.name}: {e}")

    # =========================================================================
    # RESULTADOS
    # =========================================================================
    
    print(f"✅ Foram processados {len(arquivos)} arquivos.\n")
    
    # Converte o contador para um dicionário normal (conforme você pediu)
    dicionario_ocorrencias = dict(contador_features)
    
    # Extrai APENAS O NOME das 50 features mais comuns
    top_50_features = [feature for feature, contagem in contador_features.most_common(50)]
    
    print("🏆 TOP 50 FEATURES MAIS FREQUENTES:")
    print("="*50)
    for i, (feature, contagem) in enumerate(contador_features.most_common(50), 1):
        print(f"{i:02d}. {feature} (apareceu em {contagem} JSONs)")
    
    print("="*50)
    print("\nLista do Top 50 pronta para copiar e colar no seu script GEE:")
    print(top_50_features)

    # (Opcional) Salvar a lista consolidada em um novo JSON para usar no GEE
    with open('melhores_50_features.json', 'w') as f:
        json.dump({"top_50_features": top_50_features}, f, indent=4)
        print("\n💾 Lista salva no arquivo 'melhores_50_features.json'.")