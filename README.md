# 🛰️ AgroOrbit - Monitoramento Inteligente via Satélite (ODS 2)

O **AgroOrbit** é uma solução tecnológica integrada desenvolvida para a **Global Solution 2026**. O objetivo central do projeto é combater a escassez de alimentos e mitigar as perdas agrícolas causadas por eventos climáticos extremos, alinhando-se diretamente com a **ODS 2 (Fome Zero e Agricultura Sustentável)**. 

A aplicação utiliza dados de sensoriamento remoto e meteorologia espacial extraídos diretamente da **API POWER da NASA** e do ecossistema **OpenStreetMap (Nominatim API)** para analisar o clima do solo e da atmosfera em tempo real de qualquer cidade informada pelo usuário, gerando diagnósticos preditivos e alertas automatizados de riscos (como seca crítica ou geada).

---

## 👥 Integrantes do Grupo

* **Douglas Taveira Vilella Roberto** – RM 567846
* **Fábio Alexandre Barbosa Filho** – RM 567419
* **Gilberto Hideaki Matsunaga** – RM 568191
* **Igor Davi Avelar Rosa Cesário** – RM 568163
* **Wenderson da Silva Santos** – RM 567847

---

## 🚀 Funcionalidades da Aplicação

1. **Geocodificação Dinâmica (OpenStreetMap):** Permite buscar os dados climáticos fornecendo apenas o nome da cidade. O sistema converte o texto em coordenadas geográficas válidas (Latitude e Longitude).
2. **Integração Real com Satélites da NASA:** Consome dados meteorológicos agregados de satélite para as coordenadas especificadas.
3. **Análise Agroclimática Automatizada:** Processa variáveis cruciais (Temperatura do Ar, Umidade do Solo e Índice de Precipitação) tratando ruídos ou leituras nulas da API.
4. **Geração de Alertas de Risco:** Identifica anomalias críticas no campo, notificando o produtor sobre riscos iminentes de geadas, encharcamentos ou estresse térmico.
5. **Persistência de Dados:** Salva e acumula o histórico de relatórios em um arquivo local (`historico_agroorbit.txt`) para consultas offline e auditorias do agricultor.

---

## 🎯 Requisitos de Engenharia Atendidos (Computational Thinking)

O código-fonte foi modularizado em funções puras e de responsabilidade única, implementando:
* **Estruturas de Controle:** Laços contínuos com `while`, iterações de coleções com `for` e validações condicionais complexas (`if-elif-else`).
* **Estruturas de Dados Avançadas:** Mapeamento imutável de constantes por **Tuplas**, listas dinâmicas filtradas via *List Comprehension* e estruturação de objetos via **Dicionários**.
* **Tratamento de Exceções:** Blocos `try-except` especializados em falhas físicas de rede, indisponibilidade de servidores (HTTP, timeouts) e inconsistências locais de SSL.
* **Manipulação de Arquivos:** Gravação assistida e persistente de relatórios textuais utilizando decodificadores universais (`utf-8`).

---

## 🛠️ Pré-requisitos e Como Executar

O projeto utiliza o **Python 3.14+** (ou versões estáveis a partir do 3.10) e a biblioteca externa `requests`.

### 1. Clonar o repositório ou acessar a pasta do projeto:
```bash
cd 1esps_GS_2026_1_sem_python_agro-orbit
python -m pip install requests
python main.py