import os
import shutil
import time
import sys

# pasta onde os arquivos CSVs são guardados quando baixa
DOWNLOADS_DIR = '/home/superuser/Downloads'
# Pasta de destino onde serão guardados os arquivos CSV
DEST_DIR = '/run/media/superuser/Almacen/mapbiomas/dadosCol10/ROIsv2'  
CHECK_INTERVAL = 120  # Intervalo de verificação em segundos (2 minutos)
STOP_FILE = 'stop.txt'  # Arquivo para sinalizar parada

# Criar pasta de destino se não existir
if not os.path.exists(DEST_DIR):
    os.makedirs(DEST_DIR)
    print(f"Pasta de destino criada: {DEST_DIR}")

# Função para verificar e mover arquivos CSV
def check_and_move_csv():
    print(f"Verificando pasta: {DOWNLOADS_DIR}")
    for file_name in os.listdir(DOWNLOADS_DIR):
        if file_name.lower().endswith('_cleaned.csv'):
            src_path = os.path.join(DOWNLOADS_DIR, file_name)
            dest_path = os.path.join(DEST_DIR, file_name)
            try:               
                # Mover o arquivo
                shutil.move(src_path, dest_path)
                print(f"Arquivo movido: {file_name} \n ----> {dest_path}")
            except Exception as e:
                print(f"Erro ao mover {file_name}: {str(e)}")

# Função principal
def main():
    print(f"Iniciando monitoramento da pasta {DOWNLOADS_DIR}")
    print(f"Arquivos CSV serão movidos para {DEST_DIR}")
    print(f"Crie um arquivo {STOP_FILE} para parar o script.")

    while True:
        # Verificar se o arquivo de parada existe
        if os.path.exists(STOP_FILE):
            print("Arquivo de parada detectado. Encerrando o script...")
            break
        
        check_and_move_csv()
        time.sleep(CHECK_INTERVAL)

    print("Script finalizado.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrompido pelo usuário (Ctrl+C).")
        sys.exit(0)