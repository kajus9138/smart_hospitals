# PRD - Smart Hospitals - Fase 2: ontologia da análise exploratória para agentes de IA

Este documento descreve só o que muda em relação à fase 1 (`.taskmaster/docs/prd.txt`, já entregue).
Tudo o que não for citado aqui continua valendo como está: módulo de dados, as quatro tools do MCP,
visualizações do dashboard, publicação no Streamlit Community Cloud e quality gates.

## 1. Contexto
A análise exploratória da fase 1 (`notebooks/analise_dengue_sp.ipynb`, registrada no Basic Memory em
"Notebook de análise exploratória - decisões") produziu conhecimento que o agente de IA hoje não enxerga.
O MCP server devolve números (Rt, p_rt1, nível de alerta, `casos_est` com intervalo), mas não diz como
interpretá-los: o que conta como surto, em que semanas o pico costuma ocorrer, quanto o Rt antecipa a curva
ou por que os casos notificados da última semana parecem uma queda. Esse conhecimento está espalhado entre
o texto do notebook, as notas de decisão e o código do módulo de dados.

A fase 2 organiza esse conhecimento numa **ontologia leve**, um arquivo versionado que pode ser carregado
no contexto de um agente, para que ele interprete as respostas do MCP com os mesmos conceitos, regras e
achados que orientaram o dashboard.

## 2. Objetivo
Entregar um arquivo YAML versionado no repositório com os conceitos, as relações, as regras de cálculo e os
achados empíricos da análise exploratória, pronto para ser incluído no contexto de um agente de IA, além de
testes que garantem que ele continua consistente com o código.

## 3. Usuário-alvo
- **Primário:** o agente de IA hospitalar que consome o MCP server (o mesmo caso de uso da fase 1: o tomador
  de decisões pergunta pela tendência de dengue para planejar compras).
- **Secundário:** quem configura o agente, que carrega o arquivo no system prompt ou no contexto do agente.

O agente consumidor continua fora do escopo; a demonstração usa um cliente existente (ex.: Claude Code) com
o arquivo carregado no contexto.

## 4. Escopo (nesta versão)
- Arquivo `docs/ontologia/dengue_sp.yaml`, em português, escrito à mão, com estas seções:
  - **metadados**: nome, versão, fonte dos dados (InfoDengue, São Paulo capital, geocódigo), origem
    (notebook e notas do Basic Memory), `data_referencia` (2026-10-04) e `valido_ate_se` (202640);
  - **conceitos** (classes): Município, SemanaEpidemiológica, Ano, CasosNotificados, CasosEstimados
    (nowcast), IntervaloDoNowcast, NúmeroDeReprodução (Rt), ProbabilidadeRtMaiorQue1 (p_rt1),
    NívelDeAlerta (verde, amarelo, laranja, vermelho), Incidência por 100 mil, Tendência (alta, estável,
    queda), ComparativoSazonal, AnoDeSurto, JanelaSazonal, AtrasoDeNotificação. Cada conceito traz
    definição curta, unidade e faixa de valores (quando houver), coluna de origem no snapshot e a tool do
    MCP que o expõe;
  - **relações** entre conceitos (ex.: CasosEstimados `estima` CasosNotificados; IntervaloDoNowcast
    `delimita` CasosEstimados; Rt `antecipa` crescimento de CasosEstimados; Tendência `derivada_de` Rt e
    p_rt1; AnoDeSurto `classifica` Ano);
  - **regras** (determinísticas, iguais às do código):
    - tendência das últimas 4 semanas: `alta` se Rt médio > 1,1 e p_rt1 médio > 0,7; `queda` se
      Rt médio < 0,9; senão `estavel`;
    - mapeamento do nível de alerta (1 a 4 → verde a vermelho);
    - comparativo sazonal usa só anos anteriores ao de referência;
    - variação semanal sobre `casos_est`; intervalo do nowcast só existe onde `casos_est_max > casos_est_min`;
    - valor ausente nunca vira 0 (`None` significa "não informado");
    - o sistema não faz previsão numérica de casos futuros;
  - **achados** empíricos da análise, cada um com `id`, afirmação, evidência numérica, método, seção do
    notebook de origem, `valido_ate_se`, limitações e implicação para o agente. Achados a registrar:
    - cobertura: 875 SEs de 2010-01-03 a 2026-10-04, sem semanas faltando; anos com 53 SEs (2014, 2020, 2025);
    - lacunas: só `casos_est_max` tem valores vazios (40 semanas, em 2015, 2024 e 2025);
    - intervalo do nowcast só nas 10 SEs mais recentes (202631 a 202640); nas consolidadas min = max;
    - surtos: limiar de 2× a mediana anual dos anos completos (46.406 casos/ano); anos de surto 2014, 2015,
      2019, 2023, 2024 e 2025; 2024 ficou uma ordem de grandeza acima dos demais (~1,26 mi casos estimados);
    - sazonalidade: SEs 10 a 19 (março a meados de maio) concentram ~44% dos casos do ano (mediana dos anos
      completos); o segundo semestre é sempre baixo; surtos deslocam a curva para cima sem mudar a janela;
    - Rt e p_rt1 como sinais antecipados: Spearman de 0,31 a 0,44 com o crescimento log de `casos_est`
      1 a 8 semanas à frente, maior entre 3 e 5 semanas (tabela por lag); indicam direção, não quantidade;
    - Rt = 0 nas 5 primeiras SEs de 2010 (aquecimento do estimador), excluídas da análise;
    - distribuição dos alertas: 53% das semanas em verde; 2024 praticamente todo em vermelho;
    - atraso de notificação: na SE 202640, 352 notificados contra 1.161 estimados (intervalo 582 a 3.114);
      notificados recentes dão falsa impressão de queda;
  - **orientações ao agente**: como usar os conceitos para responder (ex.: citar sempre a
    `data_referencia`; usar `casos_est` com intervalo, não notificados, nas semanas recentes; tratar Rt e
    p_rt1 como direção da tendência; contextualizar a semana atual com a janela sazonal e o comparativo
    sazonal; não transformar correlação em previsão numérica).
- Testes em `tests/test_ontologia.py`:
  - o arquivo carrega e tem todas as seções e campos obrigatórios; `id` de conceitos, regras e achados é único;
  - relações só apontam para conceitos definidos;
  - limiares e mapeamentos batem com o código (`RT_ALTA`, `RT_QUEDA`, `P_RT1_ALTA`, `LEVEL_MAP`);
  - colunas citadas existem em `REQUIRED_COLUMNS` e tools citadas existem no MCP server;
  - validade: o teste falha se a SE mais recente do snapshot for posterior a `valido_ate_se`, forçando a
    revisão dos achados no mesmo PR que atualizar o snapshot.
- `pyyaml` declarado no grupo `dev` (hoje só chega como dependência transitiva).
- README: seção curta explicando o que é a ontologia e como carregá-la no contexto de um agente.
- Basic Memory: nota de decisão (formato, entrega, achados estáticos e alternativas descartadas).

## 5. Fora de escopo (explicitamente)
- Ontologia formal em OWL/RDF, raciocinador, SPARQL ou banco de grafos.
- Expor a ontologia pelo MCP server (resource ou prompt). Nesta fase ela é só um arquivo no repositório.
- Recalcular os achados automaticamente a partir do snapshot. Os achados são estáticos e têm data de validade.
- Incluir a situação corrente (valores da semana atual) como achado: ela vem das tools do MCP.
- Mudanças no notebook, no dashboard, no módulo de dados ou nas tools do MCP.
- Previsão numérica de casos, novos municípios ou novas doenças.
- Servidor na rede local, Docker e atualização automática do snapshot (adiados para uma fase posterior).

## 6. Requisitos funcionais
- RF03: O repositório contém `docs/ontologia/dengue_sp.yaml` com as seções metadados, conceitos, relações,
  regras, achados e orientações ao agente, conforme a seção 4.
- RF04: Cada achado traz afirmação, evidência numérica, método, seção do notebook de origem,
  `valido_ate_se`, limitações e implicação para o agente.
- RF05: Cada conceito que corresponde a um dado traz a coluna do snapshot e a(s) tool(s) do MCP que o expõem.
- RF06: As regras reproduzem exatamente os limiares e mapeamentos do módulo de dados.
- RF07: O README explica como carregar o arquivo no contexto de um agente (ex.: anexar ao system prompt ou
  ao `CLAUDE.md` de um cliente).

## 7. Requisitos não funcionais
- RNF05: Tamanho. O arquivo cabe com folga no contexto de um agente: até ~20 KB (≈ 5 mil tokens).
- RNF06: Legibilidade. Escrito para ser lido por LLM e por humanos: português, frases curtas, comentários
  YAML onde ajudarem; identificadores em `snake_case` sem acento; rótulos legíveis com acento.
- RNF07: Rastreabilidade. Todo número citado num achado aparece numa saída do notebook na versão versionada.
- RNF08: Consistência. Os testes da seção 4 rodam na execução padrão do `uv run pytest --cov` e no pre-commit.
- RNF09: Qualidade. Ruff, mypy e cobertura mínima de 80% no módulo de dados e no MCP server mantidos.

## 8. Arquitetura
Sem mudança na stack nem no runtime: é um artefato de dados versionado, mais testes.

    notebook (achados) + notas do Basic Memory (decisões) + módulo de dados (regras)
                                    |
                     docs/ontologia/dengue_sp.yaml  <-- tests/test_ontologia.py
                                    |                   (consistência com código e snapshot)
                       contexto do agente de IA  +  tools do MCP server (valores atuais)

Esboço da estrutura do arquivo:

    metadados:
      nome: ontologia-dengue-sp
      versao: 1.0.0
      data_referencia: 2026-10-04
      valido_ate_se: 202640
    conceitos:
      - id: rt
        rotulo: Número de reprodução (Rt)
        definicao: ...
        coluna: Rt
        tools: [situacao_atual, tendencia, serie_historica]
    relacoes:
      - {de: rt, tipo: antecipa, para: casos_estimados}
    regras:
      - id: tendencia_alta
        expressao: "media(Rt, 4) > 1.1 e media(p_rt1, 4) > 0.7"
    achados:
      - id: janela_sazonal
        afirmacao: "As SEs 10 a 19 concentram ~44% dos casos do ano."
        evidencia: {semanas: [10, 19], percentual_mediano: 44}
        metodo: "peso de cada SE no total anual; mediana dos anos completos"
        origem: "notebook, seção 3"
        valido_ate_se: 202640
        implicacao: "..."
    orientacoes_agente:
      - "Cite sempre a data_referencia devolvida pelas tools."

## 9. Critérios de aceite
- O arquivo DEVE existir em `docs/ontologia/dengue_sp.yaml`, ser YAML válido e conter todos os conceitos,
  regras e achados listados na seção 4.
- `uv run pytest --cov` DEVE passar, incluindo `tests/test_ontologia.py`; mudar um limiar no código sem
  mudar a ontologia (ou o contrário) DEVE fazer o teste falhar.
- Ruff e mypy DEVEM passar.
- Um cliente com o arquivo no contexto e o MCP conectado DEVE responder à pergunta do caso de uso da fase 1
  citando a data de referência, a tendência e pelo menos um achado (ex.: janela sazonal ou atraso de
  notificação), sem dar previsão numérica de casos.

## 10. Riscos e validações
- Achados desatualizados depois de atualizar o snapshot: mitigado por `valido_ate_se` e pelo teste de validade,
  que obriga a revisar a ontologia no PR do novo snapshot.
- Divergência entre ontologia e código: mitigada pelos testes de consistência (limiares, níveis, colunas, tools).
- Agente tratar correlação como previsão: regra e orientação explícitas de "sem previsão numérica"; achados de
  correlação trazem a limitação junto.
- Arquivo grande demais ou prolixo para o contexto: limite de tamanho do RNF05; revisar se passar.
- Números do notebook mudarem ao reexecutá-lo: a ontologia cita os valores da versão versionada do notebook
  (snapshot até a SE 202640).

## 11. Premissas
- O notebook versionado e as notas do Basic Memory são a fonte de verdade dos achados.
- O snapshot versionado continua sendo atualizado sob demanda, por PR.
- O agente consumidor aceita texto/YAML no contexto (system prompt, `CLAUDE.md` ou anexo).

## 12. Métricas de sucesso
- Demonstração: com a ontologia no contexto, o agente responde ao caso de uso da fase 1 usando as tools e
  justificando a resposta com conceitos e achados da ontologia.
- Testes de consistência passando e cobrindo todos os limiares e mapeamentos do módulo de dados.
- Arquivo dentro do limite de tamanho, sem números que não apareçam nas saídas do notebook.
