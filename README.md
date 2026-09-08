# 🚦 Monitoramento Automático de Tráfego

Este repositório atua como um pipeline de dados automatizado. A cada 1 hora, o GitHub Actions captura uma imagem de trânsito ao vivo, executa inferência via YOLOv8 para contar veículos e salva os dados históricos em um arquivo CSV.

### 📸 Última Detecção Ao Vivo
*(Atualizado de hora em hora)*

![Última Detecção](images/latest_detection.jpg)

### 📊 Tendência das Últimas 24 Horas
![Gráfico de Tráfego](images/chart.png)


---

## **📋 Resumo Executivo**

Este é um projeto de **automação de visão computacional** que monitora câmeras de trânsito públicas ao vivo, detecta veículos usando IA, e mantém um dashboard atualizado. O sistema funciona como um **pipeline ETL (Extract-Transform-Load)** executado automaticamente a cada hora via GitHub Actions.

---

## **🏗️ Arquitetura Geral**

```
┌─────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS (Scheduler)                │
│                  Executa a cada hora (cron)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼─────┐            ┌─────▼──────┐
   │EXTRACT   │            │ TRANSFORM  │
   │(Captura) │───────────▶│   (IA/ML)  │
   └──────────┘            └─────┬──────┘
        △                         │
        │      Stream HLS         │
        │   (Câmera Pública)      │
        │                         │
   ┌────┴──────┐            ┌─────▼──────┐
   │  cv2.    │            │   LOAD     │
   │ VideoCapt│            │ (Storage)  │
   └──────────┘            └─────┬──────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼────┐          ┌────────▼────┐
              │CSV Dados │          │Imagens      │
              │(histórico)          │Processadas  │
              └────┬─────┘          └────┬────────┘
                   │                     │
                   └──────────┬──────────┘
                              │
                         ┌────▼──────────┐
                         │  STREAMLIT    │
                         │  Dashboard    │
                         └───────────────┘
```

---

## **📁 Estrutura de Diretórios**

```
projtransito/
├── .github/
│   └── workflows/
│       └── traffic_monitor.yml          # Configuração de automação
├── app.py                               # Dashboard Streamlit
├── run_pipeline.py                      # Script de processamento (ETL)
├── requirements.txt                     # Dependências Python
├── fluxograma_basico.md                # Documentação visual
├── README.md                            # Descrição do projeto
├── data/
│   └── traffic_log.csv                 # Histórico de detecções
└── images/
    ├── latest_detection.jpg            # Última imagem processada
    └── chart.png                        # Gráfico de tendências
```

---

## **🔄 Fluxo de Execução Detalhado**

### **1️⃣ EXTRACT (run_pipeline.py - Linhas 16-27)**
```python
# Captura um frame ao vivo da câmera pública
STREAM_URL = "https://d3b8201cy0qzzb.cloudfront.net/out/v1/db7ff89ac2dc4a2fa37f763f27429d86/CMAF_HLS/index_1.m3u8"
cap = cv2.VideoCapture(STREAM_URL)
ret, frame = cap.read()
```
- **Entrada**: URL de stream HLS (câmera pública em tempo real)
- **Saída**: Frame (imagem estática) capturada no momento exato

---

### **2️⃣ ANÁLISE DE CONDIÇÃO LUMINOSA (Linhas 29-34)**
```python
gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
brilho_medio = gray_frame.mean()
periodo = "Dia" if brilho_medio > 85 else "Noite"
```
- Calcula luminosidade média da imagem
- Classifica como **Dia** (≥85) ou **Noite** (<85)
- Importante para ajustar sensibilidade da IA

---

### **3️⃣ TRANSFORM - Inferência com YOLOv8 (Linhas 42-74)**

#### **Configuração do Modelo**
```python
model = YOLO('yolov8m.pt')  # Modelo Medium (maior precisão)
results = model(frame, conf=0.20, iou=0.45, imgsz=736)
```

| Parâmetro | Valor | Significado |
|-----------|-------|-------------|
| `conf=0.20` | 20% | Aceita detecções com mínimo 20% de certeza (pega veículos distantes) |
| `iou=0.45` | 45% | Se 2 caixas se sobrepõem em 45%+, elimina a de menor confiança |
| `imgsz=736` | 736px | Aumenta resolução da imagem lida pela IA (mais detalhes no fundo) |

#### **Classes Detectadas (COCO Dataset)**
```python
target_classes = [0, 1, 2, 3, 5, 7]
counts = {
    "person": 0,      # Classe 0
    "bicycle": 0,     # Classe 1
    "car": 0,         # Classe 2
    "motorcycle": 0,  # Classe 3
    "bus": 0,         # Classe 5
    "truck": 0        # Classe 7
}
```

#### **Processamento das Detecções**
```python
for box in results[0].boxes:
    cls_id = int(box.cls[0])
    if cls_id in target_classes:
        class_name = model.names[cls_id]
        counts[class_name] += 1  # Incrementa contador da classe
```

- Desenha caixas de detecção na imagem
- Adiciona texto com período e brilho
- Salva em `images/latest_detection.jpg`

---

### **4️⃣ LOAD - Armazenamento de Dados (Linhas 76-124)**

#### **Atualização do CSV (Histórico)**
```python
new_data = {
    "timestamp": "2026-09-08 14:30:00",
    "periodo": "Dia",
    "brilho": 87.45,
    "person": 5,
    "bicycle": 2,
    "car": 23,
    "motorcycle": 1,
    "bus": 3,
    "truck": 2
}
# Append ao arquivo CSV existente
df_new.to_csv(csv_path, mode='a', header=False, index=False)
```

#### **Geração de Gráfico**
```python
# Plota últimas 24 leituras
plt.plot(df_recent['timestamp'], df_recent['car'], label='Carros', color='blue')
plt.plot(df_recent['timestamp'], df_recent['truck'], label='Caminhões', color='red')
plt.plot(df_recent['timestamp'], df_recent['bus'], label='Ônibus', color='orange')
plt.plot(df_recent['timestamp'], df_recent['person'], label='Pessoas', color='green')
plt.savefig('images/chart.png')
```

---

### **5️⃣ Dashboard Streamlit (app.py)**

#### **Interface Dividida em 2 Colunas**

```
┌─────────────────────────────────────────────────────────────┐
│         🚦 Dashboard de Monitoramento de Tráfego              │
├──────────────────────┬──────────────────────────────────────┤
│                      │                                       │
│ 📷 Última Captura    │    📊 Contagem do Momento            │
│                      │                                       │
│ [Imagem com caixas]  │    Carros 🚗     23                 │
│ Atualizado em...     │    Caminhões 🚚  2                  │
│                      │    Ônibus 🚌     3                  │
│ Condição: Dia        │    Pessoas 🚶    5                  │
│ Brilho: 87.45        │                                       │
│                      │    📈 Histórico (Últimas 24 leituras)│
│                      │    [GRÁFICO INTERATIVO COM PLOTLY]   │
│                      │                                       │
└──────────────────────┴──────────────────────────────────────┘
```

#### **Funcionalidades**
- **Cache de 60 segundos**: `@st.cache_data(ttl=60)` para performance
- **Gráfico Interativo**: Plotly Express com múltiplas séries
- **Layout Responsivo**: Usa `st.columns()` para adaptar tela

---

## **⚙️ Automação com GitHub Actions**

### **traffic_monitor.yml - Workflow**

```yaml
name: Auto Traffic Monitor

on:
  schedule:
    - cron: '0 * * * *'        # ⏰ Executa no minuto 0 de cada hora (ex: 10:00, 11:00...)
  workflow_dispatch:            # 🎮 Manual: Botão no GitHub para testar

permissions:
  contents: write               # 🔐 Permite pushes automáticos

jobs:
  detect-and-update:
    runs-on: ubuntu-latest
    
    steps:
      1. Checkout do repositório
      2. Setup Python 3.10
      3. Cache de dependências pip
      4. Instala requirements.txt
      5. Executa run_pipeline.py
      6. Auto-commit dos arquivos gerados
```

### **Fluxo Temporal**
```
GitHub Actions Runner
    │
    ├─ 00:00 ─▶ Executa pipeline ─▶ Push automático
    ├─ 01:00 ─▶ Executa pipeline ─▶ Push automático
    ├─ 02:00 ─▶ Executa pipeline ─▶ Push automático
    └─ ...
```

---

## **📦 Stack Tecnológico**

| Componente | Tecnologia | Versão | Propósito |
|-----------|-----------|--------|----------|
| **Vision AI** | YOLOv8 (Ultralytics) | Latest | Detecção de objetos em tempo real |
| **Video Capture** | OpenCV | 4.9.0.80 | Leitura de stream HLS |
| **Dados** | Pandas | 2.2.0 | Manipulação de CSV e DataFrames |
| **Visualização** | Matplotlib | 3.8.2 | Gráficos estáticos (historicamente) |
| **Web App** | Streamlit | Latest | Interface interativa |
| **Gráficos Interativos** | Plotly | Latest | Gráficos dinâmicos no dashboard |
| **Automação** | GitHub Actions | v4/v5 | Scheduler e CI/CD |

---

## **💡 Inovações e Detalhes Técnicos**

### **1. Detecção Noturna Aprimorada**
```python
conf=0.20  # Mais tolerante à noite (vs. 0.50 padrão)
imgsz=736  # Resolução aumentada para ver detalhes no escuro
```

### **2. Deduplicação de Detecções**
```python
iou=0.45   # Remove caixas sobrepostas (não conta 2x o mesmo carro)
```

### **3. Cache no Streamlit**
```python
@st.cache_data(ttl=60)  # Reusa dados por 60 segundos (economiza CPU)
```

### **4. Estrutura de Cores no Gráfico**
```python
color_discrete_map={
    "car": "blue",       # Carros em azul
    "truck": "red",      # Caminhões em vermelho
    "bus": "orange",     # Ônibus em laranja
    "person": "green"    # Pessoas em verde
}
```

---

## **🚀 Como o Projeto Funciona na Prática**

### **Cenário de Uso:**

**Hora: 10:00**
```
1. GitHub Actions detecta cron '0 * * * *' 
2. Inicia runner Ubuntu
3. Captura frame da câmera pública
4. YOLOv8 detecta 23 carros, 2 caminhões, 3 ônibus, 5 pessoas
5. Salva imagem anotada e gráfico
6. Append no CSV com timestamp 2026-09-08 10:00:00
7. Faz auto-commit: "🤖 bot: Atualização de métricas e imagens de tráfego"
8. Usuario acessa dashboard no Streamlit
9. Vê últimos dados em tempo real
```

---

## **📊 Arquivo de Saída (traffic_log.csv)**

```csv
timestamp,periodo,brilho,person,bicycle,car,motorcycle,bus,truck
2026-09-08 10:00:00,Dia,87.45,5,2,23,1,3,2
2026-09-08 11:00:00,Dia,89.12,3,1,25,0,2,1
2026-09-08 12:00:00,Dia,92.33,7,3,31,2,4,3
2026-09-08 13:00:00,Noite,42.67,2,0,12,0,1,0
```

---

## **🎯 Objetivos Alcançados**

✅ **Automação completa** - Executa sem intervenção humana  
✅ **Visão computacional** - Detecção precisa com YOLOv8  
✅ **Histórico de dados** - Rastreamento ao longo do tempo  
✅ **Visualização interativa** - Dashboard em tempo real  
✅ **Escalabilidade** - Pode adaptar para múltiplas câmeras  
✅ **Nenhuma infraestrutura custosa** - Usa GitHub Actions gratuitamente  

