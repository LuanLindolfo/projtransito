import os
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from ultralytics import YOLO

# 1. Configurações Iniciais e Criação de Diretórios
STREAM_URL = "https://d3b8201cy0qzzb.cloudfront.net/out/v1/db7ff89ac2dc4a2fa37f763f27429d86/CMAF_HLS/index_1.m3u8" 
DATA_DIR = "data"
IMAGES_DIR = "images"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# 2. Captura do Frame ao Vivo (Extract)
print(f"Tentando conectar ao stream: {STREAM_URL}")
cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    raise Exception("Falha ao abrir a conexão com o stream de vídeo. Verifique a URL.")

ret, frame = cap.read()
cap.release() # Libera imediatamente

if not ret:
    raise Exception("A conexão foi estabelecida, mas não foi possível ler o frame.")

# --- NOVA LÓGICA: Detecção de Dia/Noite baseada em luminosidade ---
# Converte a imagem para tons de cinza e calcula a média dos pixels (0 a 255)
gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
brilho_medio = gray_frame.mean()
# Limiar de brilho (ajuste se necessário. Geralmente < 80 a 90 é noite em câmeras de rua)
periodo = "Dia" if brilho_medio > 85 else "Noite"
print(f"Luminosidade média: {brilho_medio:.2f} -> Classificado como: {periodo}")
# -------------------------------------------------------------------

# Salva o frame temporário (YOLO também aceita o frame direto na memória, mas manteremos o arquivo)
image_path = "temp_image.jpg"
cv2.imwrite(image_path, frame)
print("Frame capturado com sucesso!")

# 3. Inferência com YOLOv8 (Transform / Machine Learning)
print("Iniciando inferência...")
model = YOLO('yolov8n.pt') 
# Passando o frame diretamente em vez do caminho da imagem acelera o processo
results = model(frame)

# --- EXPANSÃO: Mais classes do COCO dataset ---
# 0=person, 1=bicycle, 2=car, 3=motorcycle, 5=bus, 7=truck
target_classes = [0, 1, 2, 3, 5, 7]
counts = {"person": 0, "bicycle": 0, "car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

for box in results[0].boxes:
    cls_id = int(box.cls[0])
    if cls_id in target_classes:
        class_name = model.names[cls_id]
        if class_name in counts:
            counts[class_name] += 1

# Renderiza a imagem com as caixas de detecção (bounding boxes)
annotated_frame = results[0].plot()

# Escreve o Período (Dia/Noite) diretamente na imagem final para fins visuais
texto_info = f"Periodo: {periodo} | Brilho: {brilho_medio:.1f}"
cv2.putText(annotated_frame, texto_info, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

# Salva a imagem final processada
cv2.imwrite(os.path.join(IMAGES_DIR, 'latest_detection.jpg'), annotated_frame)
print(f"Detecções: {counts}")

# 4. Atualização do Histórico de Dados (Load)
csv_path = os.path.join(DATA_DIR, 'traffic_log.csv')
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Adicionando as novas métricas ao dataframe
new_data = {
    "timestamp": [timestamp],
    "periodo": [periodo],
    "brilho": [round(brilho_medio, 2)],
    "person": [counts["person"]],
    "bicycle": [counts["bicycle"]],
    "car": [counts["car"]],
    "motorcycle": [counts["motorcycle"]],
    "bus": [counts["bus"]],
    "truck": [counts["truck"]]
}
df_new = pd.DataFrame(new_data)

# Se o CSV antigo existir, precisamos garantir que o cabeçalho bate. 
# Como adicionamos colunas, se você já tinha um arquivo, ele fará o append, mas recomendo deletar o antigo.
if os.path.exists(csv_path):
    df_new.to_csv(csv_path, mode='a', header=False, index=False)
else:
    df_new.to_csv(csv_path, index=False)

# 5. Atualização da Visualização (Gráfico)
df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df_recent = df.tail(24)

# Atualizando o gráfico para mostrar pessoas e carros
plt.figure(figsize=(12, 6))
plt.plot(df_recent['timestamp'], df_recent['car'], label='Carros', marker='o', color='blue')
plt.plot(df_recent['timestamp'], df_recent['truck'], label='Caminhões', marker='x', color='red')
plt.plot(df_recent['timestamp'], df_recent['person'], label='Pessoas', marker='s', color='green')

# Mudando a cor de fundo do gráfico se for noite na última captura
if df_recent['periodo'].iloc[-1] == "Noite":
    plt.gca().set_facecolor('#f0f0f5') # Um cinza bem leve para indicar ambiente noturno

plt.title("Fluxo de Tráfego - Últimas 24 Leituras")
plt.xlabel("Horário")
plt.ylabel("Quantidade detectada")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()

plt.savefig(os.path.join(IMAGES_DIR, 'chart.png'))
plt.close()

print("Pipeline executado com sucesso!")
