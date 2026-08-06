import os
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from ultralytics import YOLO

# 1. Configurações Iniciais e Criação de Diretórios
# Insira a URL do seu stream ao vivo. Suporta links RTSP, M3U8 ou HTTP(S) de câmeras IP.
STREAM_URL = "https://d3b8201cy0qzzb.cloudfront.net/out/v1/db7ff89ac2dc4a2fa37f763f27429d86/CMAF_HLS/index_1.m3u8" 
DATA_DIR = "data"
IMAGES_DIR = "images"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# 2. Captura do Frame ao Vivo (Extract)
image_path = "temp_image.jpg"
print(f"Tentando conectar ao stream: {STREAM_URL}")

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    raise Exception("Falha ao abrir a conexão com o stream de vídeo. Verifique a URL.")

# Lê apenas um frame do vídeo ao vivo
ret, frame = cap.read()
cap.release() # Boas práticas: liberar a conexão imediatamente para não travar o runner

if not ret:
    raise Exception("A conexão foi estabelecida, mas não foi possível ler o frame.")

# Salva o frame fisicamente para o YOLO processar
cv2.imwrite(image_path, frame)
print("Frame capturado e salvo com sucesso!")

# 3. Inferência com YOLOv8 (Transform / Machine Learning)
# O modelo 'yolov8n.pt' será baixado automaticamente na primeira execução
print("Iniciando inferência...")
model = YOLO('yolov8n.pt') 
results = model(image_path)

# Dicionário do COCO dataset: 2=car, 3=motorcycle, 5=bus, 7=truck
vehicle_classes = [2, 3, 5, 7]
counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

# Contagem de objetos detectados
for box in results[0].boxes:
    cls_id = int(box.cls[0])
    if cls_id in vehicle_classes:
        class_name = model.names[cls_id]
        if class_name in counts:
            counts[class_name] += 1

# Salvar a imagem processada com as caixas de detecção
results[0].save(filename=os.path.join(IMAGES_DIR, 'latest_detection.jpg'))
print(f"Detecções: {counts}")

# 4. Atualização do Histórico de Dados (Load)
csv_path = os.path.join(DATA_DIR, 'traffic_log.csv')
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

new_data = {
    "timestamp": [timestamp],
    "car": [counts["car"]],
    "motorcycle": [counts["motorcycle"]],
    "bus": [counts["bus"]],
    "truck": [counts["truck"]]
}
df_new = pd.DataFrame(new_data)

# Faz o append se o arquivo já existir, caso contrário, cria um novo
if os.path.exists(csv_path):
    df_new.to_csv(csv_path, mode='a', header=False, index=False)
else:
    df_new.to_csv(csv_path, index=False)

# 5. Atualização da Visualização (Gráfico)
df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Pegar apenas os últimos 24 registros
df_recent = df.tail(24)

plt.figure(figsize=(10, 5))
plt.plot(df_recent['timestamp'], df_recent['car'], label='Carros', marker='o', color='blue')
plt.plot(df_recent['timestamp'], df_recent['truck'], label='Caminhões', marker='x', color='red')
plt.title("Fluxo de Veículos - Últimas 24 Registros")
plt.xlabel("Horário")
plt.ylabel("Quantidade")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

# Salvar o gráfico
plt.savefig(os.path.join(IMAGES_DIR, 'chart.png'))
plt.close()

print("Pipeline executado com sucesso!")
