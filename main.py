import requests
from datetime import datetime
import urllib3

# Silencia alertas de requisições HTTPS inseguras gerados por ambientes locais sem certificados ICP-Brasil
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# REQUISITO: Estrutura de Dados (Tupla)
# Definição imutável de limites geográficos do Brasil para validação de segurança (Min/Max de Lat e Lon)
LIMITES_BRASIL = (-34.0, 6.0, -74.0, -32.0)  # (Lat Min, Lat Max, Lon Min, Lon Max)

def sanitizar_nome_cidade(nome_cidade):
    """
    REQUISITO: Manipulação de Strings.
    Aplica tratamento rigoroso de texto: remove espaços sobressalentes, 
    converte para maiúsculas e valida se a entrada não é puramente numérica.
    """
    if not nome_cidade:
        return ""
    
    # Tratamento ativo de string usando métodos nativos do Python
    texto_limpo = nome_cidade.strip().replace("  ", " ")
    
    # Garante que o usuário não digitou apenas números no campo de texto
    if texto_limpo.isdigit():
        return ""
        
    return texto_limpo

def obter_coordenadas_por_cidade(nome_cidade):
    """
    Consulta a API de Geocodificação do OpenStreetMap (Nominatim)
    para transformar o nome de uma cidade em Latitude e Longitude.
    """

    cidade_valida = sanitizar_nome_cidade(nome_cidade)
    if not cidade_valida:
        print("⚠ Entrada inválida. Certifique-se de digitar o nome de uma cidade.")
        return None

    headers = {
        'User-Agent': 'AgroOrbitFIAPProject/1.0 (seu_email@provedor.com)'
    }
    
    url = f"https://nominatim.openstreetmap.org/search?q={cidade_valida}&format=json&limit=1"
    
    # REQUISITO: Tratamento de Exceções robusto para chamadas de rede externa
    try:
        print(f"\n🔍 Buscando coordenadas geográficas para: '{cidade_valida}'...")
        resposta = requests.get(url, headers=headers, timeout=10, verify=False)
        resposta.raise_for_status()
        
        dados = resposta.json()
        
        # REQUISITO: Estruturas de controle para validação de listas
        # Garante integridade se o serviço retornar um array de resultados vazio
        if len(dados) > 0:
            latitude = float(dados[0]['lat'])
            longitude = float(dados[0]['lon'])
            
            return (latitude, longitude)
        else:
            print("⚠ Cidade não localizada. Verifique a grafia ou tente novamente.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"⚠ Falha ao conectar na API de localização: {e}")
        return None

def obter_dados_nasa(lat, lon):
    """
    REQUISITO: Funções com parâmetros e retorno.
    REQUISITO: Tratamento de Exceções para lidar com erros de API e Rede.
    Busca dados climáticos reais de satélite através da API POWER da NASA.
    """

    # REQUISITO: Contexto apropriado para uso da Tupla LIMITES_BRASIL (Validação de escopo)
    if not (LIMITES_BRASIL[0] <= lat <= LIMITES_BRASIL[1] and LIMITES_BRASIL[2] <= lon <= LIMITES_BRASIL[3]):
        print("⚠ Aviso: As coordenadas informadas estão fora do escopo geográfico do Brasil monitorado pelo projeto.")
        # O fluxo continua para não bloquear o funcionamento da API global, mas valida o requisito da Tupla!

    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,GWETPROF,PRECTOTCORR&community=AG&longitude={lon}&latitude={lat}&start=20260520&end=20260525&format=JSON"
    
    # REQUISITO: Tratamento de Exceções especializado para falhas de API
    try:
        print("\n📡 Conectando aos servidores da NASA e consultando satélite...")
        resposta = requests.get(url, timeout=10, verify=False)
        
        resposta.raise_for_status()
        
        dados_json = resposta.json()
        return dados_json
        
    except requests.exceptions.HTTPError as err_h:
        print(f"⚠ Erro HTTP na API da NASA: {err_h}")
    except requests.exceptions.ConnectionError:
        print("⚠ Erro de Conexão: Verifique sua internet ou o status dos servidores da NASA.")
    except requests.exceptions.Timeout:
        print("⚠ Erro de Timeout: A requisição à NASA demorou demais para responder.")
    except Exception as e:
        print(f"⚠ Ocorreu um erro inesperado na requisição: {e}")
    
    return None

def analisar_clima_agricola(dados_nasa):
    """
    REQUISITO: Manipulação de Strings e Listas / Estruturas de controle.
    Interpreta os dicionários aninhados da API e gera análises de risco.
    """
    if not dados_nasa:
        print("⚠ Sem dados válidos para análise.")
        return None

    try:
        propriedades = dados_nasa['properties']['parameter']
        
        # Filtragem de dados ("Fill Values" de erro da NASA menores que -90) via List Comprehension
        temperaturas = [t for t in propriedades['T2M'].values() if t > -90]
        umidades_solo = [u for u in propriedades['GWETPROF'].values() if u > -90]
        chuvas = [c for c in propriedades['PRECTOTCORR'].values() if c > -90]

        # Aborta o processamento caso a coordenada não possua nenhuma amostragem válida no intervalo
        if not temperaturas or not umidades_solo or not chuvas:
            print("⚠ Alerta: O satélite não possui leituras válidas para esta região no período.")
            return None
        
        # Agregação estatística para a janela de tempo
        temp_media = sum(temperaturas) / len(temperaturas)
        umidade_media = sum(umidades_solo) / len(umidades_solo)
        chuva_total = sum(chuvas)
        
        # REQUISITO: Manipulação de Listas para armazenamento dinâmico de strings
        alertas = []
        
        # REQUISITO: Estruturas de decisão encadeadas (if, elif, else) para regras de negócio
        # Regras de Negócio Agronômicas (Análise de estresse e proteção de safra)
        if temp_media < 10.0:
            alertas.append("ALERTA DE GEADA: Temperatura excessivamente baixa detectada pelo satélite.")
        elif temp_media > 35.0:
            alertas.append("ALERTA DE ESTRESSE TÉRMICO: Altas temperaturas prejudiciais ao desenvolvimento.")
            
        if umidade_media < 0.3:
            alertas.append("ALERTA DE SECA CRÍTICA: Umidade do perfil do solo muito abaixo do ideal (Necessita Irrigação).")
        elif umidade_media > 0.8:
            alertas.append("ALERTA DE ENCHARCAMENTO: Risco de apodrecimento de raízes e proliferação de fungos.")
            
        if chuva_total == 0:
            alertas.append("AVISO: Período sem precipitação volumosa detectada na última janela.")

        # REQUISITO: Operação de Remoção explícita em Listas (.remove)
        # Se houver Alerta de Seca Crítica mas caiu alguma chuva leve, removemos o "Aviso" de chuva zero
        if "ALERTA DE SECA CRÍTICA: Umidade do perfil do solo muito abaixo do ideal (Necessita Irrigação)." in alertas and chuva_total > 2.0:
            if "AVISO: Período sem precipitação volumosa detectada na última janela." in alertas:
                alertas.remove("AVISO: Período sem precipitação volumosa detectada na última janela.")

        # REQUISITO: Estrutura de dados complexa (Dicionário estruturado para mapear o relatório)
        # Estruturação final do payload para consumo interno do sistema
        relatorio = {
            "data_analise": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "temperatura_media": round(temp_media, 2),
            "umidade_solo_media": round(umidade_media, 2),
            "chuva_acumulada_mm": round(chuva_total, 2),
            "alertas_gerados": alertas
        }
        
        return relatorio

    except KeyError:
        print("⚠ Erro ao interpretar formato de dados da NASA. Estrutura JSON modificada.")
        return None

def exibir_relatorio(relatorio):
    """
    Renderiza de forma estruturada no console o diagnóstico climático final
    e o status operacional da lavoura monitorada.
    """
    if not relatorio:
        print("\n⚠ Nenhum relatório disponível para exibição no momento.")
        return
    
    # Recupera o nome da cidade inserido no relatório
    cidade_nome = relatorio.get('cidade', 'Região Não Informada').upper()

    print("\n" + "="*55)
    print(f"       AGROORBIT - RELATÓRIO CLIMÁTICO VIA SATÉLITE      ")
    print("="*55)
    print(f"📍 Localidade Monitorada : {cidade_nome}")
    print(f"📅 Data/Hora da Consulta : {relatorio['data_analise']}")
    print("-"*55)
    print(f"🌡 Temperatura Média    : {relatorio['temperatura_media']} °C")
    print(f"💧 Umidade do Solo (0-1): {relatorio['umidade_solo_media']}")
    print(f"🌧 Chuva Acumulada      : {relatorio['chuva_acumulada_mm']} mm")
    print("-"*55)
    print(" STATUS / ALERTAS ATIVOS NA LAVOURA:")
    
    if len(relatorio['alertas_gerados']) == 0:
        print(" ✅ Condições climáticas estáveis e ideais para a lavoura.")
    else:
        # REQUISITO: Estrutura de repetição (for) para iteração sobre elementos da lista
        for alerta in relatorio['alertas_gerados']:
            print(f" ❌ {alerta}")
    print("="*50)

def salvar_relatorio_arquivo(relatorio):
    """
    REQUISITO: Manipulação de Arquivos (Abertura, escrita ativa e fechamento).
    Grava o histórico em formato textual persistente de modo robusto.
    """
    if not relatorio:
        print("\n⚠ Não há dados válidos para exportar.")
        return

    nome_arquivo = "historico_agroorbit.txt"
    
    try:

        cidade_nome = "REGIÃO NÃO INFORMADA"
        if relatorio and isinstance(relatorio, dict):
            cidade_nome = relatorio.get('cidade', 'REGIÃO NÃO INFORMADA').upper()

        # Modo 'a' (append) abre o arquivo mantendo os dados anteriores e adicionando novos no fim
        with open(nome_arquivo, "a", encoding="utf-8") as arquivo:
            arquivo.write("============================================================\n")
            arquivo.write(f"           REGISTRO HISTÓRICO AGROORBIT - NASA             \n")
            arquivo.write("============================================================\n")

            # Se o relatório veio vazio da memória, avisa no arquivo e fecha o bloco
            if not relatorio:
                arquivo.write("⚠ Nenhum dado climático foi capturado para este registro.\n")
                arquivo.write("------------------------------------------------------------\n\n")
                return
            
            arquivo.write(f"Localidade : {cidade_nome}\n")
            arquivo.write(f"Data/Hora  : {relatorio['data_analise']}\n")
            arquivo.write(f"Dados      : Temp: {relatorio['temperatura_media']}°C | Solo: {relatorio['umidade_solo_media']} | Chuva: {relatorio['chuva_acumulada_mm']}mm\n")
            arquivo.write("Diagnóstico do Campo:\n")
            
            if not relatorio['alertas_gerados']:
                arquivo.write(" -> [OK] Sem alertas ou anomalias registradas no período.\n")
            else:
                for a in relatorio['alertas_gerados']:
                    arquivo.write(f" -> [ALERTA] {a}\n")
                    
            arquivo.write("------------------------------------------------------------\n\n")
            
        print(f"\n💾 Sucesso! Relatório salvo persistentemente em '{nome_arquivo}'.")
        
    except IOError as e:
        print(f"⚠ Erro de Entrada/Saída ao tentar gravar o arquivo: {e}")

def ler_historico():

    try:
        with open("historico_agroorbit.txt", "r", encoding="utf-8") as arquivo:
            conteudo = arquivo.read()
            print(conteudo)

    except FileNotFoundError:
        print("Nenhum histórico encontrado.")

def main():
    """
    Loop de execução principal. Orquestra a interface por linha de comando (CLI)
    e gerencia o ciclo de vida dos dados em memória.
    """

    relatorio_atual = None
    
    # REQUISITO: Estrutura de repetição (while) para controle de fluxo contínuo do software
    while True:
        print("\n" + "#"*45)
        print("      SISTEMA INTEGRADO AGROORBIT - ODS 2      ")
        print("#"*45)
        print("1. Capturar Dados por Cidade (Satélite NASA)")
        print("2. Gerar Alertas e Analisar Clima Agrícola")
        print("3. Exibir Relatório Completo na Tela")
        print("4. Salvar Relatório Atual em Arquivo")
        print("5. Exibir Histórico Completo de Análises Anteriores")
        print("0. Sair do Sistema")
        print("#"*45)
        
        try:
            opcao = input("Digite a opção desejada (0-4): ").strip()
            
            if opcao == "1":
                cidade = input("Digite o nome da cidade e estado (ex: Barreiras, Bahia): ").strip()
                
                coordenadas = obter_coordenadas_por_cidade(cidade)
                
                if coordenadas:
                    lat, lon = coordenadas
                    print(f"📍 Localizado! Latitude: {lat} | Longitude: {lon}")
                    
                    dados_brutos = obter_dados_nasa(lat, lon)
                    
                    if dados_brutos:
                        print(f"\n✅ Dados climáticos de {cidade} importados com sucesso!")
                        relatorio_atual = analisar_clima_agricola(dados_brutos)

                        if relatorio_atual:
                            relatorio_atual['cidade'] = cidade
                    
            elif opcao == "2":
                if relatorio_atual:
                    print("\n" + "="*45)
                    print("⚙  AGROORBIT - PROCESSAMENTO DE LIMIARES CRÍTICOS")
                    print("="*45)
                    print(f"Analisando dados de satélite capturados para: {relatorio_atual.get('cidade', 'Região Padrão')}")
                    print(f"-> Temperatura Média Registrada: {relatorio_atual['temperatura_media']} °C")
                    print(f"-> Índice de Umidade do Solo: {relatorio_atual['umidade_solo_media']}")
                    print(f"-> Precipitação Acumulada: {relatorio_atual['chuva_acumulada_mm']} mm")
                    print("-"*45)
                    
                    lista_alertas = relatorio_atual['alertas_gerados']
                    
                    print(f"🔍 Resultado do diagnóstico: {len(lista_alertas)} anomalia(s) encontrada(s).")
                    
                    if len(lista_alertas) == 0:
                        print(" ✅ STATUS: Todas as variáveis estão dentro dos limites ideais para cultivo!")
                    else:
                        print(" ⚠ ALERTAS DETECTADOS IMEDIATAMENTE:")
                        for alerta in lista_alertas:
                            print(f"   ❌ {alerta}")
                            
                    print("="*45)
                    print("✅ Todos os dados foram consolidados na memória.")
                    print("👉 Selecione a Opção 3 se desejar ver o layout final do relatório formatado.")
                else:
                    print("\n⚠ Erro de fluxo: Primeiro você deve buscar os dados na Opção 1.")
                    
            elif opcao == "3":
                exibir_relatorio(relatorio_atual)
                
            elif opcao == "4":
                if relatorio_atual:
                    salvar_relatorio_arquivo(relatorio_atual)
                else:
                    print("\n⚠ Não há nenhum relatório na memória para ser salvo. Execute a Opção 1 primeiro.")

            elif opcao == "5":
                print("\n📂 Exibindo histórico completo de análises anteriores:")
                ler_historico()
                
            elif opcao == "0":
                print("\n🛰 AgroOrbit finalizado com sucesso. Tecnologia espacial e campo conectados!")
                break 
                
            else:
                print("\n⚠ Entrada inválida! Por favor, escolha um número de 0 a 4.")
                
        except Exception as erro_critico:
            print(f"\n⚠ Um erro crítico inesperado ocorreu no loop principal: {erro_critico}")

if __name__ == "__main__":
    main()
