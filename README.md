[README (1).md](https://github.com/user-attachments/files/28777493/README.1.md)
# 🚀 ORION-1 — Sistema de Monitoramento de Missão Espacial
**Global Solution FIAP 2026 · 1º Semestre**

---

## 👥 Equipe

| Nome | RM |
|---|---|
| *(Marcos Benevenuto)* | rm570834 |


---

## 📌 Resumo do Problema e Cenário

A missão **ORION-1** é uma missão espacial experimental em fase de operação nominal. O sistema recebe dados de telemetria a cada 4 horas e deve identificar situações críticas, gerar alertas automáticos e fornecer recomendações para manter a tripulação e os equipamentos em segurança.

No ciclo analisado, foram detectados:
- **Falha crítica**: módulo de comunicação principal offline desde 04:30
- **Degradação energética**: reserva em queda progressiva, chegando a 32% às 20:00
- **Radiação elevada**: 0.85 Sv (acima do limiar de alerta de 0.7 Sv)
- **Inconsistência de dados**: sensor de temperatura externa registrou -120°C (valor fora da faixa válida para a região de pouso equatorial de Marte)

---

## 🏗️ Estruturas de Dados Utilizadas

| Estrutura | Aplicação no sistema | Justificativa |
|---|---|---|
| **Lista** | Séries temporais de reserva, consumo e geração de energia | Acesso por índice e iteração para análise temporal e regressão linear |
| **Fila (deque)** | Alertas pendentes enfileirados por ordem de chegada | FIFO garante que alertas mais antigos sejam processados primeiro |
| **Pilha (list)** | Registro dos últimos eventos críticos | LIFO exibe o evento mais recente primeiro no log |
| **Dicionário / Hash Map** | `tabela_modulos`: acesso rápido ao status de cada módulo por nome | O(1) para leitura; ideal quando consultamos módulos frequentemente pelo nome |
| **Hierarquia (dict aninhado)** | Árvore de subsistemas da missão ORION-1 | Representa a relação pai-filho entre sistemas (Energia → Solar, Baterias) |
| **Matriz (lista de listas)** | Leituras de energia por horário × variável | Permite indexar `matriz[linha][coluna]` para acesso a qualquer medição |

---

## 🔢 Regras Lógicas Principais

### Expressão Booleana do Diagnóstico

```
STATUS_CRITICO = (NOT suporte_vida)
              OR (reserva < 20%)
              OR (NOT comunicacao AND reserva < 50%)
              OR (radiacao > 1.0)
              OR (consumo > 75 kWh)

STATUS_ALERTA = NOT STATUS_CRITICO
             AND (NOT comunicacao
                  OR reserva < 50%
                  OR radiacao > 0.7
                  OR qualidade_com < 50%)

STATUS_NORMAL = NOT STATUS_CRITICO AND NOT STATUS_ALERTA
```

### Regras em linguagem simples

1. **Regra 1 (AND + NOT)**: Se a comunicação está offline **E** a reserva está abaixo de 50%, o status é CRÍTICO — porque sem comunicação e sem energia não há como acionar socorro.
2. **Regra 2 (OR + comparação)**: Se o consumo supera 75 kWh **OU** a reserva cai abaixo de 20%, o sistema entra em modo crítico de energia.
3. **Regra 3 (NOT + AND)**: Um alerta de radiação é gerado quando a leitura está entre 0.7 e 1.0 Sv — não crítico, mas exige ação preventiva.

---

## 📈 Técnica de Previsão Utilizada

**Regressão Linear Simples (Mínimos Quadrados)** — implementada do zero, sem bibliotecas.

### Metodologia

Usamos os 6 pontos de leitura de reserva energética (às 00:00, 04:00, 08:00, 12:00, 16:00 e 20:00) como variável dependente `y`, e os índices 0-5 como variável independente `x`.

**Fórmulas:**
```
b = (n·Σxy - Σx·Σy) / (n·Σx² - (Σx)²)
a = (Σy - b·Σx) / n
y_previsto = a + b·x
```

**Resultado:**
- Equação: `y = 79.19 + (-7.54) · x`
- R² = 0.6510
- **Previsão para o próximo ciclo: 33.9%**

### Influência na decisão

A previsão identificou que a reserva chegará a ~34% no próximo ciclo e, no ritmo atual, atingirá o nível crítico absoluto em ~17 horas. Isso disparou as recomendações P3 de protocolo de racionamento imediato.

---

## ▶️ Como Executar

```bash
# Pré-requisito: Python 3.8+
python src/sistema.py
```

Não são necessárias bibliotecas externas. O código usa apenas a biblioteca padrão do Python (`csv`, `os`, `collections`).

---

## 📥 Exemplo de Entrada e Saída

### Entrada (data/dados.csv — último ciclo)

```
tipo,campo,valor
modulo,comunicacao,0
energia,horario,20:00
energia,geracao_kWh,12.2
energia,consumo_kWh,80.5
energia,reserva_pct,32
ambiente,radiacao_Sv,0.85
```

### Saída (resumo)

```
◉ STATUS GERAL DA MISSÃO: CRITICO

[1] CRITICO — Comunicação
    Módulo de comunicação principal OFFLINE. Qualidade do sinal: 35%.
    🔴 Ativar rádio de emergência. Transmitir posição via BEACON.

[2] CRITICO — Balanço Energético
    Consumo (80.5 kWh) supera geração (12.2 kWh). Déficit: 68.3 kWh.
    🔴 Iniciar protocolo de racionamento energético.

Previsão próximo ciclo: 33.9%
🟡 ALERTA: reserva projetada abaixo de 35%.
```

---

## 🛡️ Recomendações Geradas

| Prioridade | Ação |
|---|---|
| P1 - CRÍTICO | Manter suporte à vida e BEACON operacionais |
| P1 - CRÍTICO | Desligar laboratório e armazenamento ativo |
| P2 - ALTA | Reduzir consumo em 68.3 kWh. Redirecionar painéis solares |
| P2 - ALTA | Limitar EVAs. Verificar escudos do habitat |
| P3 - PREVENTIVO | Reserva chegará a 33.9% no próximo ciclo. Monitorar a cada 2h |
| P3 - PREVENTIVO | Esgotamento crítico em ~17h. Solicitar ressuprimento |
| P4 - MANUTENÇÃO | Calibrar sensor de temperatura externa (-120°C inválido) |
| P4 - MANUTENÇÃO | Diagnóstico do módulo de comunicação |

---

## 🔗 Vídeo de Apresentação

https://youtu.be/BCPg_ev7-mI

---

## 💡 Conclusões e Aprendizados

- A aplicação de estruturas de dados clássicas (listas, filas, pilhas, dicionários) em um cenário realista evidencia a importância de escolher a estrutura certa para cada problema.
- A regressão linear simples, mesmo sem bibliotecas avançadas, fornece previsões úteis para tomada de decisão operacional.
- O tratamento de inconsistências nos dados (sensor com leitura inválida) é tão importante quanto os dados corretos — sistemas críticos precisam de diagnóstico de qualidade de dados.
- A organização em funções bem definidas facilita manutenção, teste e extensão do sistema.
