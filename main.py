import requests
import json
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# REQUISITO: Estrutura de Dados (Uso de Tupla para Configurações Fixas)
# Coordenadas padrão de uma região agrícola de exemplo (Matopiba / Cerrado)
# =====================================================================
COORDENADAS_PADRAO = (-12.50, -45.50)  # (Latitude, Longitude)

def obter_coordenadas_por_cidade(nome_cidade):
    """
    Consulta a API de Geocodificação do OpenStreetMap (Nominatim)
    para transformar o nome de uma cidade em Latitude e Longitude.
    """
    # A API exige um User-Agent limpo para identificar a aplicação e evitar bloqueios
    headers = {
        'User-Agent': 'AgroOrbitFIAPProject/1.0 (seu_email@provedor.com)'
    }
    
    # URL de busca da API Nominatim
    url = f"https://nominatim.openstreetmap.org/search?q={nome_cidade}&format=json&limit=1"
    
    try:
        print(f"\n🔍 Buscando coordenadas geográficas para: '{nome_cidade}'...")
        resposta = requests.get(url, headers=headers, timeout=10, verify=False)
        resposta.raise_for_status()
        
        dados = resposta.json()
        
        # REQUISITO: Estruturas de controle e validação de listas
        if len(dados) > 0:
            # A API retorna strings, convertemos para float para uso matemático posterior
            latitude = float(dados[0]['lat'])
            longitude = float(dados[0]['lon'])
            
            # REQUISITO: Retorno de dados em formato de Tupla
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
    # Montagem da URL da API oficial da NASA POWER
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,GWETPROF,PRECTOTCORR&community=AG&longitude={lon}&latitude={lat}&start=20260520&end=20260525&format=JSON"
    
    try:
        print("\n📡 Conectando aos servidores da NASA e consultando satélite...")
        resposta = requests.get(url, timeout=10, verify=False)
        
        # Garante que a requisição HTTP ocorreu com sucesso (Status 200)
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
        # Extraindo dicionários de parâmetros climáticos retornados pela NASA
        propriedades = dados_nasa['properties']['parameter']
        
        temperaturas = [t for t in propriedades['T2M'].values() if t > -90]
        umidades_solo = [u for u in propriedades['GWETPROF'].values() if u > -90]
        chuvas = [c for c in propriedades['PRECTOTCORR'].values() if c > -90]

        if not temperaturas or not umidades_solo or not chuvas:
            print("⚠ Alerta: O satélite não possui leituras válidas para esta região no período.")
            return None
        
        # Cálculo de médias usando iteração (For) e tipos numéricos (Float)
        temp_media = sum(temperaturas) / len(temperaturas)
        umidade_media = sum(umidades_solo) / len(umidades_solo)
        chuva_total = sum(chuvas)
        
        # REQUISITO: Manipulação de Listas para armazenar alertas gerados dinamicamente
        alertas = []
        
        # REQUISITO: Estruturas de Controle Avançadas (if, elif, else)
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

        # REQUISITO: Criação de um Dicionário Estruturado contendo o diagnóstico completo
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
    Exibe de forma amigável no terminal os dados processados e os alertas ativos.
    """
    if not relatorio:
        print("\n⚠ Nenhum relatório disponível para exibição no momento.")
        return

    print("\n" + "="*50)
    print("        AGROORBIT - RELATÓRIO VIA SATÉLITE NASA       ")
    print("="*50)
    print(f"Data/Hora da Consulta: {relatorio['data_analise']}")
    print(f"Temperatura Média do Ar: {relatorio['temperatura_media']} °C")
    print(f"Índice de Umidade do Solo: {relatorio['umidade_solo_media']} (Escala 0 a 1)")
    print(f"Volume de Chuva Acumulado: {relatorio['chuva_acumulada_mm']} mm")
    print("-"*50)
    print(" STATUS / ALERTAS ATIVOS NO CAMPO:")
    
    if len(relatorio['alertas_gerados']) == 0:
        print(" ✅ Condições climáticas estáveis e ideais para a lavoura.")
    else:
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
        # Abre o arquivo em modo 'append' (a) para adicionar sem apagar o histórico anterior
        with open(nome_arquivo, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"--- REGISTRO AGROORBIT {relatorio['data_analise']} ---\n")
            arquivo.write(f"Temperatura: {relatorio['temperatura_media']} C | Solo: {relatorio['umidade_solo_media']} | Chuva: {relatorio['chuva_acumulada_mm']} mm\n")
            arquivo.write("Alertas processados:\n")
            if not relatorio['alertas_gerados']:
                arquivo.write(" - Sem alertas cadastrados.\n")
            else:
                for a in relatorio['alertas_gerados']:
                    arquivo.write(f" - {a}\n")
            arquivo.write("="*60 + "\n\n")
            
        print(f"\n💾 Sucesso! Relatório salvo persistentemente em '{nome_arquivo}'.")
        
    except IOError as e:
        print(f"⚠ Erro de Entrada/Saída ao tentar gravar o arquivo: {e}")

# No topo do arquivo, você pode remover ou deixar a COORDENADAS_PADRAO apenas como backup

def main():
    relatorio_atual = None
    
    while True:
        print("\n" + "#"*45)
        print("      SISTEMA INTEGRADO AGROORBIT - ODS 2      ")
        print("#"*45)
        print("1. Capturar Dados por Cidade (Satélite NASA)")
        print("2. Gerar Alertas e Analisar Clima Agrícola")
        print("3. Exibir Relatório Completo na Tela")
        print("4. Salvar Relatório Atual em Arquivo")
        print("0. Sair do Sistema")
        print("#"*45)
        
        try:
            opcao = input("Digite a opção desejada (0-4): ").strip()
            
            if opcao == "1":
                # REQUISITO: Manipulação de strings com input dinâmico
                cidade = input("Digite o nome da cidade e estado (ex: Barreiras, Bahia): ").strip()
                
                # Primeiro passo: Descobre a Lat e Lon da cidade digitada
                coordenadas = obter_coordenadas_por_cidade(cidade)
                
                if coordenadas:
                    lat, lon = coordenadas
                    print(f"📍 Localizado! Latitude: {lat} | Longitude: {lon}")
                    
                    # Segundo passo: Passa a lat/lon dinâmicas para a API da NASA
                    dados_brutos = obter_dados_nasa(lat, lon)
                    
                    if dados_brutos:
                        print(f"\n✅ Dados climáticos de {cidade} importados com sucesso!")
                        relatorio_atual = analisar_clima_agricola(dados_brutos)
                        # Adicionamos o nome da cidade no relatório para exibição posterior
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
                    
                    # Captura a lista de alertas gerados
                    lista_alertas = relatorio_atual['alertas_gerados']
                    
                    print(f"🔍 Resultado do diagnóstico: {len(lista_alertas)} anomalia(s) encontrada(s).")
                    
                    # REQUISITO: Estrutura de repetição (for) e controle (if/else)
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
                # Pequeno ajuste para exibir o nome da cidade se ela existir no relatório
                if relatorio_atual and 'cidade' in relatorio_atual:
                    print(f"\n🌍 Região Analisada: {relatorio_atual['cidade'].upper()}")
                exibir_relatorio(relatorio_atual)
                
            elif opcao == "4":
                salvar_relatorio_arquivo(relatorio_atual)
                
            elif opcao == "0":
                print("\n🛰 AgroOrbit finalizado com sucesso. Tecnologia espacial e campo conectados!")
                break 
                
            else:
                print("\n⚠ Entrada inválida! Por favor, escolha um número de 0 a 4.")
                
        except Exception as erro_critico:
            print(f"\n⚠ Um erro crítico inesperado ocorreu no loop principal: {erro_critico}")

if __name__ == "__main__":
    main()