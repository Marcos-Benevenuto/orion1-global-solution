"""
╔══════════════════════════════════════════════════════════════════╗
║     SISTEMA DE MONITORAMENTO DE MISSÃO ESPACIAL - ORION-1       ║
║              Global Solution FIAP 2026 - 1º Semestre            ║
╚══════════════════════════════════════════════════════════════════╝

Sistema inteligente de monitoramento operacional para controle
de uma missão espacial experimental, com diagnóstico automático,
alertas em tempo real e previsão de variáveis críticas.
"""

import csv
import os
from collections import deque


# ─────────────────────────────────────────────────────────────────
#  1. LEITURA E INTERPRETAÇÃO DE DADOS
# ─────────────────────────────────────────────────────────────────

def carregar_dados(caminho_csv: str) -> dict:
    """
    Lê o arquivo CSV de telemetria e retorna um dicionário organizado
    com todas as seções: módulos, energia, ambiente e log de eventos.

    Estrutura de retorno:
      dados = {
        'modulos':  dict  -> {nome_modulo: status_binario},
        'energia':  list  -> [{horario, geracao, consumo, reserva}, ...],
        'ambiente': dict  -> {variavel: valor},
        'log':      list  -> [{timestamp, evento, severidade}, ...]
      }
    """
    dados = {
        'modulos':  {},
        'energia':  [],
        'ambiente': {},
        'log':      []
    }

    # Acumuladores temporários enquanto lemos o CSV linha a linha
    bloco_energia  = {}   # construção de um registro de energia
    bloco_log      = {}   # construção de um registro de log

    try:
        with open(caminho_csv, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # pula o cabeçalho

            for linha in reader:
                if len(linha) < 3:
                    continue  # ignora linhas incompletas

                tipo, campo, valor = linha[0].strip(), linha[1].strip(), linha[2].strip()

                # ── Módulos (status binário 0/1) ──────────────────
                if tipo == 'modulo':
                    dados['modulos'][campo] = int(valor)

                # ── Energia (múltiplos horários) ──────────────────
                elif tipo == 'energia':
                    if campo == 'horario':
                        if bloco_energia:              # salva bloco anterior
                            dados['energia'].append(bloco_energia)
                        bloco_energia = {'horario': valor}
                    elif campo == 'geracao_kWh':
                        bloco_energia['geracao'] = float(valor)
                    elif campo == 'consumo_kWh':
                        bloco_energia['consumo'] = float(valor)
                    elif campo == 'reserva_pct':
                        bloco_energia['reserva'] = float(valor)

                # ── Ambiente ──────────────────────────────────────
                elif tipo == 'ambiente':
                    dados['ambiente'][campo] = float(valor)

                # ── Log de eventos ────────────────────────────────
                elif tipo == 'log':
                    if campo == 'timestamp':
                        if bloco_log:                  # salva bloco anterior
                            dados['log'].append(bloco_log)
                        bloco_log = {'timestamp': valor}
                    elif campo == 'evento':
                        bloco_log['evento'] = valor
                    elif campo == 'severidade':
                        bloco_log['severidade'] = valor

        # Salva últimos blocos pendentes
        if bloco_energia:
            dados['energia'].append(bloco_energia)
        if bloco_log:
            dados['log'].append(bloco_log)

    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {caminho_csv}")
        print("       Usando dados embutidos como fallback.\n")
        dados = dados_embutidos()

    return dados


def dados_embutidos() -> dict:
    """
    Dados de telemetria embutidos diretamente no código como fallback.
    Mantém a mesma estrutura do arquivo CSV.
    """
    return {
        'modulos': {
            'suporte_vida':  1,
            'energia':       1,
            'comunicacao':   0,   # ← FALHA CRÍTICA
            'habitat':       1,
            'laboratorio':   1,
            'armazenamento': 1
        },
        'energia': [
            {'horario': '00:00', 'geracao': 30.5, 'consumo': 45.2, 'reserva': 78.0},
            {'horario': '04:00', 'geracao':  0.0, 'consumo': 48.1, 'reserva': 62.0},
            {'horario': '08:00', 'geracao': 55.3, 'consumo': 50.0, 'reserva': 67.0},
            {'horario': '12:00', 'geracao': 72.1, 'consumo': 52.3, 'reserva': 75.0},
            {'horario': '16:00', 'geracao': 45.8, 'consumo': 78.0, 'reserva': 48.0},
            {'horario': '20:00', 'geracao': 12.2, 'consumo': 80.5, 'reserva': 32.0},
        ],
        'ambiente': {
            'temperatura_interna_C':   21.5,
            'temperatura_externa_C':  -63.0,
            'radiacao_Sv':              0.85,
            'qualidade_comunicacao_pct': 35.0,
            'pressao_interna_atm':       1.01
        },
        'log': [
            {'timestamp': '2026-06-01 00:15', 'evento': 'Sistema inicializado em modo nominal',                        'severidade': 'NORMAL'},
            {'timestamp': '2026-06-01 04:30', 'evento': 'Falha no modulo de comunicacao primaria detectada',           'severidade': 'CRITICO'},
            {'timestamp': '2026-06-01 06:00', 'evento': 'Reinicializacao do sistema de comunicacao sem sucesso',       'severidade': 'CRITICO'},
            {'timestamp': '2026-06-01 08:45', 'evento': 'Geracao solar retomada apos periodo noturno',                 'severidade': 'NORMAL'},
            {'timestamp': '2026-06-01 12:00', 'evento': 'Sensor de temperatura externa com leitura inconsistente',     'severidade': 'ALERTA'},
            {'timestamp': '2026-06-01 15:30', 'evento': 'Modo de economia de energia ativado no laboratorio',         'severidade': 'ALERTA'},
            {'timestamp': '2026-06-01 16:00', 'evento': 'Consumo de energia acima do limiar critico (78 kWh)',         'severidade': 'CRITICO'},
            {'timestamp': '2026-06-01 20:00', 'evento': 'Reserva energetica em nivel critico - 32%',                  'severidade': 'CRITICO'},
        ]
    }


# ─────────────────────────────────────────────────────────────────
#  2. ORGANIZAÇÃO DOS DADOS EM ESTRUTURAS COMPUTACIONAIS
# ─────────────────────────────────────────────────────────────────

def organizar_estruturas(dados: dict) -> dict:
    """
    Organiza os dados brutos nas estruturas corretas:
      - Lista     : séries temporais (reserva, consumo, geração)
      - Fila      : alertas pendentes (deque – FIFO)
      - Pilha     : últimos eventos críticos analisados (list – LIFO)
      - Dicionário: acesso rápido a módulos por nome (hash map)
      - Hierarquia: árvore de subsistemas (dict aninhado)
      - Matriz    : leituras de energia por horário × variável
    """

    # ── Lista: séries temporais ───────────────────────────────────
    lista_reserva  = [r['reserva']  for r in dados['energia']]
    lista_consumo  = [r['consumo']  for r in dados['energia']]
    lista_geracao  = [r['geracao']  for r in dados['energia']]
    lista_horarios = [r['horario']  for r in dados['energia']]

    # ── Fila (FIFO): alertas pendentes ───────────────────────────
    # Eventos críticos e alertas são enfileirados; críticos têm prioridade
    fila_alertas = deque()
    for evento in dados['log']:
        if evento['severidade'] in ('CRITICO', 'ALERTA'):
            fila_alertas.append(evento)

    # ── Pilha (LIFO): últimos eventos analisados ──────────────────
    pilha_eventos = []
    for evento in dados['log']:
        pilha_eventos.append(evento)  # push

    # ── Dicionário / Hash Map: módulos por nome ───────────────────
    tabela_modulos = dict(dados['modulos'])  # já é um dicionário

    # ── Hierarquia de subsistemas (árvore como dict aninhado) ─────
    hierarquia_missao = {
        'ORION-1': {
            'Energia': {
                'Solar':     {'status': tabela_modulos.get('energia', 0), 'geracao_atual': lista_geracao[-1]},
                'Baterias':  {'reserva_pct': lista_reserva[-1]}
            },
            'Habitat': {
                'Suporte_Vida': {'status': tabela_modulos.get('suporte_vida', 0)},
                'Temperatura':  {'interna_C': dados['ambiente'].get('temperatura_interna_C', 0)},
                'Pressao':      {'atm':       dados['ambiente'].get('pressao_interna_atm', 0)}
            },
            'Comunicacao': {
                'Principal': {'status': tabela_modulos.get('comunicacao', 0)},
                'Qualidade':  {'pct': dados['ambiente'].get('qualidade_comunicacao_pct', 0)}
            },
            'Laboratorio':  {'status': tabela_modulos.get('laboratorio', 0)},
            'Armazenamento':{'status': tabela_modulos.get('armazenamento', 0)}
        }
    }

    # ── Matriz: energia por horário × variável ────────────────────
    # Linhas = horários, Colunas = [geracao, consumo, reserva]
    cabecalho_matriz = ['Horario', 'Geracao (kWh)', 'Consumo (kWh)', 'Reserva (%)']
    matriz_energia = []
    for r in dados['energia']:
        matriz_energia.append([r['horario'], r['geracao'], r['consumo'], r['reserva']])

    return {
        'lista_reserva':     lista_reserva,
        'lista_consumo':     lista_consumo,
        'lista_geracao':     lista_geracao,
        'lista_horarios':    lista_horarios,
        'fila_alertas':      fila_alertas,
        'pilha_eventos':     pilha_eventos,
        'tabela_modulos':    tabela_modulos,
        'hierarquia_missao': hierarquia_missao,
        'matriz_energia':    matriz_energia,
        'cabecalho_matriz':  cabecalho_matriz
    }


# ─────────────────────────────────────────────────────────────────
#  3. REGRAS LÓGICAS — DIAGNÓSTICO OPERACIONAL
# ─────────────────────────────────────────────────────────────────

# Expressão booleana principal do diagnóstico (README):
#
#   CRITICO = (suporte_vida = 0)
#          OR (energia_reserva < 20%)
#          OR (comunicacao = 0  AND  energia_reserva < 40%)
#          OR (radiacao > 1.0   AND  suporte_vida = 0)
#
#   ALERTA  = NOT CRITICO
#          AND (energia_reserva < 50%
#               OR  comunicacao = 0
#               OR  radiacao > 0.7
#               OR  consumo > geracao * 1.5)
#
#   NORMAL  = NOT CRITICO AND NOT ALERTA

# Limiares de segurança definidos por faixa
LIMITE_RESERVA_CRITICO = 20.0   # % abaixo → crítico
LIMITE_RESERVA_ALERTA  = 50.0   # % abaixo → alerta
LIMITE_CONSUMO_CRITICO = 75.0   # kWh acima → crítico
LIMITE_RADIACAO_CRITICO = 1.0   # Sv acima → crítico
LIMITE_RADIACAO_ALERTA  = 0.7   # Sv acima → alerta
LIMITE_QUAL_COM_ALERTA  = 50.0  # % abaixo → alerta


def classificar_status(dados: dict, structs: dict) -> dict:
    """
    Aplica as regras lógicas e retorna o diagnóstico completo da missão.
    Usa IF/ELIF/ELSE e operadores AND, OR, NOT.
    """
    mod  = structs['tabela_modulos']
    amb  = dados['ambiente']
    res  = structs['lista_reserva'][-1]   # reserva mais recente
    con  = structs['lista_consumo'][-1]   # consumo mais recente
    ger  = structs['lista_geracao'][-1]   # geração mais recente
    rad  = amb.get('radiacao_Sv', 0)
    qcom = amb.get('qualidade_comunicacao_pct', 100)

    # Variáveis booleanas por módulo (0 = falha, 1 = ok)
    sv_ok   = bool(mod.get('suporte_vida',  1))  # suporte à vida
    en_ok   = bool(mod.get('energia',       1))
    com_ok  = bool(mod.get('comunicacao',   1))
    hab_ok  = bool(mod.get('habitat',       1))
    lab_ok  = bool(mod.get('laboratorio',   1))
    arm_ok  = bool(mod.get('armazenamento', 1))

    # ── Regra 1: módulos em falha ─────────────────────────────────
    falha_critica = not sv_ok or (not com_ok and not en_ok)
    falha_alerta  = not com_ok or not hab_ok

    # ── Regra 2: estado energético ────────────────────────────────
    energia_critica = res < LIMITE_RESERVA_CRITICO
    energia_alerta  = res < LIMITE_RESERVA_ALERTA
    consumo_alto    = con > LIMITE_CONSUMO_CRITICO

    # ── Regra 3: condições ambientais ────────────────────────────
    radiacao_critica = rad > LIMITE_RADIACAO_CRITICO
    radiacao_alerta  = rad > LIMITE_RADIACAO_ALERTA
    com_degradada    = qcom < LIMITE_QUAL_COM_ALERTA

    # ── Diagnóstico final (expressão booleana) ───────────────────
    # CRITICO: suporte_vida falhou  OU reserva mínima  OU (sem comunicação E energia baixa)
    #          OU radiação letal    OU consumo insustentável
    status_critico = (
        not sv_ok
        or energia_critica
        or (not com_ok and energia_alerta)
        or radiacao_critica
        or consumo_alto
    )

    # ALERTA: não crítico MAS há degradação em algum sistema
    status_alerta = (
        not status_critico
        and (
            falha_alerta
            or energia_alerta
            or radiacao_alerta
            or com_degradada
        )
    )

    # NORMAL: nem crítico nem alerta
    status_normal = not status_critico and not status_alerta

    # Define o status geral
    if status_critico:
        status_geral = 'CRITICO'
    elif status_alerta:
        status_geral = 'ALERTA'
    else:
        status_geral = 'NORMAL'

    # Status por módulo
    status_modulos = {}
    for nome, val in mod.items():
        status_modulos[nome] = 'NORMAL' if val == 1 else 'CRITICO'

    # Status energético
    if energia_critica:
        status_energia = 'CRITICO'
    elif energia_alerta:
        status_energia = 'ALERTA'
    else:
        status_energia = 'NORMAL'

    # Status ambiental
    if radiacao_critica:
        status_rad = 'CRITICO'
    elif radiacao_alerta:
        status_rad = 'ALERTA'
    else:
        status_rad = 'NORMAL'

    return {
        'status_geral':    status_geral,
        'status_modulos':  status_modulos,
        'status_energia':  status_energia,
        'status_radiacao': status_rad,
        'detalhes': {
            'sv_ok':         sv_ok,
            'com_ok':        com_ok,
            'en_ok':         en_ok,
            'reserva':       res,
            'consumo':       con,
            'geracao':       ger,
            'radiacao':      rad,
            'qual_com':      qcom
        }
    }


# ─────────────────────────────────────────────────────────────────
#  4. ALERTAS AUTOMÁTICOS
# ─────────────────────────────────────────────────────────────────

def gerar_alertas(diagnostico: dict, structs: dict) -> list:
    """
    Gera alertas automáticos com severidade, descrição e recomendação
    de ação. Retorna lista ordenada do mais crítico ao menos crítico.

    Cada alerta tem:
      { 'nivel': str, 'sistema': str, 'mensagem': str, 'acao': str }
    """
    alertas = []
    d = diagnostico['detalhes']

    # ── Alertas de Módulos ────────────────────────────────────────
    if not d['sv_ok']:
        alertas.append({
            'nivel':    'CRITICO',
            'sistema':  'Suporte à Vida',
            'mensagem': 'Módulo de suporte à vida OFFLINE. Risco de vida imediato.',
            'acao':     '🔴 AÇÃO IMEDIATA: Ativar sistema de backup de oxigênio. Evacuar compartimento afetado.'
        })

    if not d['com_ok']:
        alertas.append({
            'nivel':    'CRITICO',
            'sistema':  'Comunicação',
            'mensagem': f"Módulo de comunicação principal OFFLINE. Qualidade do sinal: {d['qual_com']:.0f}%.",
            'acao':     '🔴 Ativar rádio de emergência. Transmitir posição e status via protocolo BEACON.'
        })

    if not d['en_ok']:
        alertas.append({
            'nivel':    'CRITICO',
            'sistema':  'Sistema de Energia',
            'mensagem': 'Módulo de energia principal OFFLINE.',
            'acao':     '🔴 Conectar gerador de backup. Reduzir consumo ao mínimo vital.'
        })

    # ── Alertas de Energia ────────────────────────────────────────
    if d['reserva'] < LIMITE_RESERVA_CRITICO:
        alertas.append({
            'nivel':    'CRITICO',
            'sistema':  'Reserva Energética',
            'mensagem': f"Reserva em {d['reserva']:.1f}% — abaixo do mínimo crítico ({LIMITE_RESERVA_CRITICO}%).",
            'acao':     '🔴 Desligar TODOS os sistemas não essenciais. Priorizar suporte à vida e comunicação.'
        })
    elif d['reserva'] < LIMITE_RESERVA_ALERTA:
        alertas.append({
            'nivel':    'ALERTA',
            'sistema':  'Reserva Energética',
            'mensagem': f"Reserva em {d['reserva']:.1f}% — abaixo do limiar de alerta ({LIMITE_RESERVA_ALERTA}%).",
            'acao':     '🟡 Reduzir consumo do laboratório e sistemas secundários em 30%.'
        })

    if d['consumo'] > LIMITE_CONSUMO_CRITICO:
        deficit = d['consumo'] - d['geracao']
        alertas.append({
            'nivel':    'CRITICO',
            'sistema':  'Balanço Energético',
            'mensagem': f"Consumo ({d['consumo']:.1f} kWh) supera geração ({d['geracao']:.1f} kWh). Déficit: {deficit:.1f} kWh.",
            'acao':     '🔴 Iniciar protocolo de racionamento energético. Desligar laboratório e armazenamento ativo.'
        })

    # ── Alertas Ambientais ────────────────────────────────────────
    if d['radiacao'] > LIMITE_RADIACAO_CRITICO:
        alertas.append({
            'nivel':    'CRITICO',
            'sistema':  'Radiação',
            'mensagem': f"Nível de radiação {d['radiacao']:.2f} Sv — acima do limite letal (1,0 Sv).",
            'acao':     '🔴 Recolher tripulação para bunker blindado. Ativar escudos anti-radiação.'
        })
    elif d['radiacao'] > LIMITE_RADIACAO_ALERTA:
        alertas.append({
            'nivel':    'ALERTA',
            'sistema':  'Radiação',
            'mensagem': f"Nível de radiação {d['radiacao']:.2f} Sv — elevado (limite: {LIMITE_RADIACAO_ALERTA} Sv).",
            'acao':     '🟡 Monitorar exposição da tripulação. Limitar EVAs externos. Usar trajes blindados.'
        })

    if d['qual_com'] < LIMITE_QUAL_COM_ALERTA:
        alertas.append({
            'nivel':    'ALERTA',
            'sistema':  'Qualidade do Sinal',
            'mensagem': f"Qualidade de comunicação em {d['qual_com']:.0f}% — degradada (mínimo: {LIMITE_QUAL_COM_ALERTA}%).",
            'acao':     '🟡 Reposicionar antena direcional. Agendar janela de comunicação com controle da missão.'
        })

    # ── Inconsistência nos dados (diagnóstico) ────────────────────
    # O sensor de temperatura externa com leitura de -120°C é inconsistente
    # (Marte tem mínima de ~-125°C mas na região equatorial não chegaria tão baixo)
    # O dado registrado nos logs indica isso
    alertas.append({
        'nivel':    'ALERTA',
        'sistema':  'Diagnóstico de Dados',
        'mensagem': 'INCONSISTÊNCIA detectada: sensor de temperatura externa registrou -120°C (fora da faixa válida para a região de pouso).',
        'acao':     '🟡 Marcar leitura como inválida. Usar média das últimas 6h. Verificar calibração do sensor.'
    })

    # ── Ordena: CRITICO primeiro, depois ALERTA, depois NORMAL ───
    ordem = {'CRITICO': 0, 'ALERTA': 1, 'NORMAL': 2}
    alertas.sort(key=lambda x: ordem.get(x['nivel'], 3))

    return alertas


# ─────────────────────────────────────────────────────────────────
#  5. ANÁLISE E PREVISÃO DE DADOS (REGRESSÃO LINEAR SIMPLES)
# ─────────────────────────────────────────────────────────────────

def regressao_linear(x: list, y: list) -> tuple:
    """
    Implementa regressão linear simples pelo método dos mínimos quadrados,
    sem uso de bibliotecas externas.

    Fórmulas:
      b = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
      a = (Σy - b*Σx) / n

    Retorna (a, b) onde  y_previsto = a + b*x
    """
    n    = len(x)
    sx   = sum(x)
    sy   = sum(y)
    sxy  = sum(xi * yi for xi, yi in zip(x, y))
    sx2  = sum(xi ** 2 for xi in x)

    denominador = n * sx2 - sx ** 2
    if denominador == 0:
        return (sum(y) / n, 0)  # constante se divisão por zero

    b = (n * sxy - sx * sy) / denominador
    a = (sy - b * sx) / n
    return (a, b)


def prever_reserva(structs: dict) -> dict:
    """
    Aplica regressão linear sobre a série temporal de reserva energética
    para prever o valor no próximo ciclo (horário 24:00 / meia-noite seguinte).

    Decisão: a previsão influencia o protocolo de racionamento de energia.
    """
    reservas  = structs['lista_reserva']
    horarios  = structs['lista_horarios']
    n         = len(reservas)

    # Índices numéricos para o eixo x (0, 1, 2, 3, 4, 5)
    x = list(range(n))
    y = reservas

    a, b = regressao_linear(x, y)

    # Previsão para o próximo ponto (índice n)
    x_prox   = n
    y_previsto = a + b * x_prox

    # Calcula R² para medir qualidade do ajuste
    media_y = sum(y) / n
    ss_tot  = sum((yi - media_y) ** 2 for yi in y)
    ss_res  = sum((yi - (a + b * xi)) ** 2 for xi, yi in zip(x, y))
    r2      = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0

    # Extrapolação: quantos ciclos até reserva chegar a 10% (crítico absoluto)?
    if b < 0:
        ciclos_para_critico = (10.0 - a) / b - (n - 1)
        ciclos_para_critico = max(0, ciclos_para_critico)
    else:
        ciclos_para_critico = float('inf')

    # Decisão baseada na previsão
    if y_previsto < 10:
        decisao_previsao = '🔴 CRÍTICO: reserva projetada abaixo de 10%. Desligar TODOS os sistemas não vitais AGORA.'
    elif y_previsto < 20:
        decisao_previsao = '🔴 CRÍTICO: reserva projetada abaixo de 20%. Iniciar protocolo de emergência energética.'
    elif y_previsto < 35:
        decisao_previsao = '🟡 ALERTA: reserva projetada abaixo de 35%. Reduzir consumo e ativar painéis extras.'
    else:
        decisao_previsao = '🟢 NORMAL: reserva projetada adequada. Monitorar tendência.'

    return {
        'coef_a':              a,
        'coef_b':              b,
        'r2':                  r2,
        'reserva_atual':       reservas[-1],
        'reserva_prevista':    y_previsto,
        'horarios':            horarios,
        'reservas_historico':  reservas,
        'ciclos_critico':      ciclos_para_critico,
        'decisao':             decisao_previsao
    }


# ─────────────────────────────────────────────────────────────────
#  6. RECOMENDAÇÕES TÉCNICAS
# ─────────────────────────────────────────────────────────────────

def gerar_recomendacoes(diagnostico: dict, previsao: dict) -> list:
    """
    Gera lista priorizada de recomendações técnicas de manutenção
    e recuperação operacional, baseando-se no diagnóstico e previsão.
    """
    recomendacoes = []
    d = diagnostico['detalhes']

    # ── P1 — Ações críticas imediatas ────────────────────────────
    if not d['com_ok']:
        recomendacoes.append({
            'prioridade': 1,
            'label':      '[P1 - CRÍTICO]',
            'acao':       'Manter suporte à vida e canal de comunicação de emergência (BEACON) operacionais a todo custo.'
        })

    if d['reserva'] < 40:
        recomendacoes.append({
            'prioridade': 1,
            'label':      '[P1 - CRÍTICO]',
            'acao':       f"Desligar laboratório e sistemas de armazenamento ativo. "
                          f"Estimativa de ganho: +15-20% de autonomia energética."
        })

    # ── P2 — Ações de alta prioridade ────────────────────────────
    if d['consumo'] > d['geracao']:
        deficit = d['consumo'] - d['geracao']
        recomendacoes.append({
            'prioridade': 2,
            'label':      '[P2 - ALTA]',
            'acao':       f"Reduzir consumo em {deficit:.1f} kWh para equilibrar o balanço energético. "
                          f"Redirecionar painéis solares para orientação ótima."
        })

    if d['radiacao'] > LIMITE_RADIACAO_ALERTA:
        recomendacoes.append({
            'prioridade': 2,
            'label':      '[P2 - ALTA]',
            'acao':       'Limitar atividades externas (EVA). Verificar integridade dos escudos do habitat.'
        })

    # ── P3 — Ações preventivas baseadas na previsão ──────────────
    prev = previsao['reserva_prevista']
    recomendacoes.append({
        'prioridade': 3,
        'label':      '[P3 - PREVENTIVO]',
        'acao':       f"Com base na previsão (regressão linear, R²={previsao['r2']:.2f}), "
                      f"a reserva chegará a {prev:.1f}% no próximo ciclo. "
                      f"{'Ativar protocolo de racionamento agora.' if prev < 30 else 'Monitorar a cada 2h.'}"
    })

    if previsao['ciclos_critico'] < float('inf'):
        horas = previsao['ciclos_critico'] * 4  # cada ciclo ≈ 4h
        recomendacoes.append({
            'prioridade': 3,
            'label':      '[P3 - PREVENTIVO]',
            'acao':       f"Tendência indica esgotamento crítico em ~{horas:.0f}h. "
                          f"Solicitar janela de ressuprimento ou ajuste de missão."
        })

    # ── P4 — Manutenção e diagnóstico ────────────────────────────
    recomendacoes.append({
        'prioridade': 4,
        'label':      '[P4 - MANUTENÇÃO]',
        'acao':       'Agendar calibração do sensor de temperatura externa. '
                      'Leitura de -120°C está fora da faixa esperada para a região de pouso.'
    })

    recomendacoes.append({
        'prioridade': 4,
        'label':      '[P4 - MANUTENÇÃO]',
        'acao':       'Realizar diagnóstico completo do módulo de comunicação. '
                      'Testar antena secundária e verificar cabos de conexão.'
    })

    # Ordena por prioridade
    recomendacoes.sort(key=lambda x: x['prioridade'])
    return recomendacoes


# ─────────────────────────────────────────────────────────────────
#  7. EXIBIÇÃO — INTERFACE DE TERMINAL
# ─────────────────────────────────────────────────────────────────

COR = {
    'CRITICO': '\033[91m',   # vermelho
    'ALERTA':  '\033[93m',   # amarelo
    'NORMAL':  '\033[92m',   # verde
    'TITULO':  '\033[96m',   # ciano
    'BOLD':    '\033[1m',
    'RESET':   '\033[0m'
}

def colorir(texto: str, nivel: str) -> str:
    """Aplica cor ANSI ao texto conforme o nível de severidade."""
    return f"{COR.get(nivel, '')}{COR['BOLD']}{texto}{COR['RESET']}"


def imprimir_separador(char: str = '─', largura: int = 65) -> None:
    print(char * largura)


def exibir_cabecalho() -> None:
    imprimir_separador('═')
    print(colorir('  🚀  ORION-1 — SISTEMA DE MONITORAMENTO OPERACIONAL', 'TITULO'))
    print(colorir('       Global Solution FIAP 2026 · Missão Espacial', 'TITULO'))
    imprimir_separador('═')
    print()


def exibir_status_geral(diagnostico: dict) -> None:
    sg = diagnostico['status_geral']
    print(colorir(f'\n  ◉ STATUS GERAL DA MISSÃO: {sg}', sg))
    imprimir_separador()


def exibir_tabela_modulos(diagnostico: dict) -> None:
    print(colorir('\n  📋  STATUS DOS MÓDULOS CRÍTICOS', 'TITULO'))
    imprimir_separador()
    print(f"  {'MÓDULO':<20} {'STATUS':<12} {'INDICADOR'}")
    imprimir_separador('-')
    for modulo, status in diagnostico['status_modulos'].items():
        icone = '✅' if status == 'NORMAL' else '❌'
        nome_fmt = modulo.replace('_', ' ').title()
        linha = f"  {nome_fmt:<20} {status:<12} {icone}"
        print(colorir(linha, status) if status != 'NORMAL' else linha)
    imprimir_separador()


def exibir_matriz_energia(structs: dict) -> None:
    print(colorir('\n  ⚡  MATRIZ DE ENERGIA — LEITURAS POR HORÁRIO', 'TITULO'))
    imprimir_separador()
    cab = structs['cabecalho_matriz']
    print(f"  {cab[0]:<10} {cab[1]:<18} {cab[2]:<18} {cab[3]}")
    imprimir_separador('-')
    for linha in structs['matriz_energia']:
        h, g, c, r = linha
        nivel = 'CRITICO' if r < 20 else ('ALERTA' if r < 50 else 'NORMAL')
        row = f"  {h:<10} {g:<18.1f} {c:<18.1f} {r:.1f}%"
        print(colorir(row, nivel) if nivel != 'NORMAL' else row)
    imprimir_separador()


def exibir_ambiente(dados: dict, diagnostico: dict) -> None:
    print(colorir('\n  🌡️   VARIÁVEIS AMBIENTAIS', 'TITULO'))
    imprimir_separador()
    amb = dados['ambiente']
    pares = [
        ('Temperatura Interna (°C)', amb.get('temperatura_interna_C', '-'),    'NORMAL'),
        ('Temperatura Externa (°C)', amb.get('temperatura_externa_C', '-'),    'NORMAL'),
        ('Radiação (Sv)',            amb.get('radiacao_Sv', '-'),               diagnostico['status_radiacao']),
        ('Qualidade Comunicação (%)',amb.get('qualidade_comunicacao_pct', '-'), 'ALERTA' if amb.get('qualidade_comunicacao_pct', 100) < 50 else 'NORMAL'),
        ('Pressão Interna (atm)',    amb.get('pressao_interna_atm', '-'),       'NORMAL'),
    ]
    for nome, val, nivel in pares:
        linha = f"  {nome:<30} {val}"
        print(colorir(linha, nivel) if nivel != 'NORMAL' else linha)
    imprimir_separador()


def exibir_alertas(alertas: list) -> None:
    print(colorir('\n  🚨  ALERTAS AUTOMÁTICOS (por prioridade)', 'TITULO'))
    imprimir_separador()
    if not alertas:
        print(colorir('  Nenhum alerta ativo. Missão em condições normais.', 'NORMAL'))
    else:
        for i, alerta in enumerate(alertas, 1):
            nivel = alerta['nivel']
            print(colorir(f"  [{i}] {nivel} — {alerta['sistema']}", nivel))
            print(f"      {alerta['mensagem']}")
            print(f"      {alerta['acao']}")
            print()
    imprimir_separador()


def exibir_previsao(previsao: dict) -> None:
    print(colorir('\n  📈  ANÁLISE E PREVISÃO — RESERVA ENERGÉTICA', 'TITULO'))
    imprimir_separador()
    print('  Técnica: Regressão Linear Simples (Mínimos Quadrados)')
    print(f"  Equação: y = {previsao['coef_a']:.2f} + {previsao['coef_b']:.2f} · x")
    print(f"  R²     : {previsao['r2']:.4f}  (quanto maior, melhor o ajuste)")
    print()
    print('  Dados utilizados:')
    for i, (h, r) in enumerate(zip(previsao['horarios'], previsao['reservas_historico'])):
        print(f"    x={i}  [{h}]  reserva = {r:.1f}%")
    print()
    nivel_prev = 'CRITICO' if previsao['reserva_prevista'] < 20 else ('ALERTA' if previsao['reserva_prevista'] < 50 else 'NORMAL')
    print(colorir(f"  Previsão próximo ciclo: {previsao['reserva_prevista']:.1f}%", nivel_prev))
    print(f"\n  {previsao['decisao']}")
    imprimir_separador()


def exibir_recomendacoes(recomendacoes: list) -> None:
    print(colorir('\n  📋  RECOMENDAÇÕES TÉCNICAS (por prioridade)', 'TITULO'))
    imprimir_separador()
    for rec in recomendacoes:
        nivel = 'CRITICO' if rec['prioridade'] == 1 else ('ALERTA' if rec['prioridade'] == 2 else 'NORMAL')
        print(colorir(f"  {rec['label']}", nivel))
        print(f"    {rec['acao']}")
        print()
    imprimir_separador()


def exibir_log(structs: dict) -> None:
    print(colorir('\n  📜  LOG DE EVENTOS (últimos 8)', 'TITULO'))
    imprimir_separador()
    pilha = structs['pilha_eventos']
    # Exibe do mais recente ao mais antigo (LIFO)
    for evento in reversed(pilha):
        nivel = evento.get('severidade', 'NORMAL')
        ts    = evento.get('timestamp', '???')
        msg   = evento.get('evento', '')
        linha = f"  [{ts}] {nivel:<8} — {msg}"
        print(colorir(linha, nivel) if nivel != 'NORMAL' else linha)
    imprimir_separador()


def exibir_hierarquia(structs: dict) -> None:
    print(colorir('\n  🌐  HIERARQUIA DA MISSÃO', 'TITULO'))
    imprimir_separador()
    h = structs['hierarquia_missao']

    def imprimir_no(no: dict, prefixo: str = '  ', nivel: int = 0) -> None:
        for chave, valor in no.items():
            indent = prefixo + '  ' * nivel
            if isinstance(valor, dict):
                print(f"{indent}▸ {chave}")
                imprimir_no(valor, prefixo, nivel + 1)
            else:
                print(f"{indent}  · {chave}: {valor}")

    imprimir_no(h)
    imprimir_separador()


# ─────────────────────────────────────────────────────────────────
#  8. PONTO DE ENTRADA PRINCIPAL
# ─────────────────────────────────────────────────────────────────

def main() -> None:
    # Caminho do arquivo de dados (relativo ao diretório do projeto)
    caminho_csv = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'data', 'dados.csv'
    )

    exibir_cabecalho()

    # 1. Leitura e interpretação dos dados
    print('  ⏳ Carregando telemetria da missão ORION-1...')
    dados = carregar_dados(caminho_csv)
    print('  ✅ Dados carregados com sucesso.\n')

    # 2. Organização nas estruturas de dados
    structs = organizar_estruturas(dados)

    # 3. Regras lógicas — diagnóstico
    diagnostico = classificar_status(dados, structs)

    # 4. Alertas automáticos
    alertas = gerar_alertas(diagnostico, structs)

    # 5. Previsão de dados
    previsao = prever_reserva(structs)

    # 6. Recomendações
    recomendacoes = gerar_recomendacoes(diagnostico, previsao)

    # 7. Exibição
    exibir_status_geral(diagnostico)
    exibir_tabela_modulos(diagnostico)
    exibir_matriz_energia(structs)
    exibir_ambiente(dados, diagnostico)
    exibir_alertas(alertas)
    exibir_previsao(previsao)
    exibir_recomendacoes(recomendacoes)
    exibir_log(structs)
    exibir_hierarquia(structs)

    print(colorir('\n  ✅  Análise concluída. Sistema ORION-1 aguarda próximo ciclo.\n', 'TITULO'))


if __name__ == '__main__':
    main()
