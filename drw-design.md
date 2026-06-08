# Dynamic Research Workflows Design

## Objetivo

Construir o Dynamic Research Workflows (DRW) como um servico independente em `/home/matheus/Documentos/laboratorio/drw`, rodando em producao real na VPS, privado via Tailscale e consumido pelo OpenCode atraves de um MCP HTTP/SSE.

O DRW nao tera UI/TUI propria. Ele sera uma infraestrutura de pesquisa e execucao para agentes: recebe objetivos, gera workflows dinamicos, executa workers em paralelo controlado, persiste artifacts, verifica blocos intermediarios, refina lacunas e entrega relatorios finais.

## Escopo De Producao

- Rodar como servico privado na VPS.
- Expor MCP HTTP/SSE apenas via Tailscale.
- Usar autenticacao OAuth existente das CLIs, sem exigir OpenRouter ou API token de LLM.
- Usar Codex CLI como provider padrao configurado.
- Permitir providers plugaveis: Codex, OpenCode, Hermes e Claude.
- Executar tarefas leves com `asyncio`.
- Executar CLIs, scripts bloqueantes e tarefas de risco em subprocessos isolados.
- Persistir estado em PostgreSQL.
- Persistir artifacts em filesystem local na V1, com interface preparada para S3-compatible storage no futuro.

## Arquitetura Geral

```text
OpenCode / Codex / CLI
  |
  v
DRW MCP Server HTTP/SSE via Tailscale
  |
  v
Workflow Director
  |
  v
Workflow Classifier
  |
  v
Workflow Template
  |
  v
Workflow Generator
  |
  v
Validated Workflow DSL + WorkflowPolicy
  |
  v
Workflow Runtime
  |
  +--> Async Worker Pool
  |
  +--> Isolated Process Pool
  |
  v
Per-Block Verification / Critic / Refinement
  |
  v
Local Artifact Store
  |
  v
Final Report
```

## Componentes

### MCP Server

Expoe ferramentas privadas para agentes e CLIs:

- `start_workflow`: inicia uma execucao a partir de um objetivo.
- `get_workflow_status`: retorna status resumido de um workflow.
- `list_artifacts`: lista artifacts gerados por workflow/run.
- `read_artifact`: le um artifact especifico.
- `list_reports`: lista relatorios finais.
- `read_report`: le um relatorio final.

O servidor deve bindar somente na interface/IP Tailscale e exigir token simples mesmo em rede privada.

### Workflow Director

Responsavel por receber o objetivo, aplicar politica padrao, validar escopo inicial e acionar o Workflow Generator.

Ele nao executa workers diretamente. Seu papel e coordenar o ciclo de alto nivel e manter o sistema previsivel.

### Workflow Classifier E Templates

Antes de chamar o generator, o DRW classifica o objetivo em uma familia de workflow e seleciona um template base.

Templates iniciais:

- `research`: pesquisa tecnica, comparacao de ferramentas, deep research.
- `code_migration`: investigacao e plano para migracao/refatoracao de codigo.
- `security_review`: revisao de seguranca, threat modeling e findings priorizados.
- `market_analysis`: analise de mercado, concorrentes, oportunidades e MVP.

O template define a estrutura esperada do workflow, steps permitidos e politicas padrao. O LLM nao cria o workflow do zero; ele preenche e adapta um template validado.

Essa decisao reduz erro, custo e variancia do generator.

### Workflow Generator

Transforma o objetivo em uma Workflow DSL validada por Pydantic.

Regra central: workflows nao devem ser hardcoded, mas tambem nao devem ser DSL livre. O generator usa um `LLMProvider` para adaptar um template escolhido, mas o resultado so entra no runtime depois de validacao estrutural, checagem de `StepType` e aplicacao de `WorkflowPolicy`.

### Workflow Runtime

Interpreta a DSL, agenda steps, controla dependencias, concorrencia, retries, timeouts e checkpoints.

O runtime deve aceitar que o workflow solicite muitos workers, mas nunca deve executar tudo simultaneamente sem respeitar a politica.

### Async Worker Pool

Executa tarefas I/O-bound leves como:

- leitura de documentacao;
- requests HTTP;
- consultas GitHub;
- leitura de fontes publicas permitidas;
- parsing e normalizacao;
- escrita leve de artifacts.

Esses workers rodam como tarefas `asyncio`, controladas por semaforos e limites por tipo de step.

### Isolated Process Pool

Executa tarefas bloqueantes, pesadas ou arriscadas em subprocessos isolados:

- `codex` CLI;
- `opencode` CLI;
- `hermes`;
- scripts externos;
- tarefas CPU-bound;
- operacoes que possam travar o event loop.

Cada subprocesso deve ter timeout, working directory isolado, captura de stdout/stderr, exit code persistido e logs mascarados.

### Verifier, Critic E Refinement

A validacao nao acontece apenas no final. Cada bloco importante segue o ciclo:

```text
Worker
  |
  v
Verifier
  |
  v
Critic
  |
  v
Refinement
```

O Verifier checa corretude, fontes, schema e completude minima. O Critic desafia conclusoes, vieses, lacunas e contradicoes. O Refinement corrige o bloco dentro dos limites da politica.

O relatorio final consolida blocos ja verificados, em vez de tentar auditar tudo tardiamente.

### Event Bus Interno

O runtime emite eventos internos para desacoplar execucao, auditoria, metricas e futuras notificacoes.

Exemplos de eventos:

- `workflow.started`
- `workflow.completed`
- `workflow.failed`
- `step.started`
- `step.completed`
- `worker.started`
- `worker.completed`
- `artifact.created`
- `verification.failed`
- `refinement.requested`

V1 nao usa Kafka, RabbitMQ ou broker externo. O Event Bus e interno/in-process, com persistencia dos eventos relevantes no PostgreSQL.

Isso prepara notificacoes, dashboards, metricas e auditoria sem introduzir infraestrutura pesada agora.

## Providers

O core nao deve depender diretamente de Codex, OpenCode, Hermes ou Claude.

Contrato conceitual:

```text
LLMProvider
  generate(prompt, schema, context, policy)
  run_agent_task(task, context, policy)
```

Implementacoes previstas:

- `CodexProvider`: provider padrao configurado, usando Codex CLI autenticado por OAuth.
- `OpenCodeProvider`: fallback/alternativa usando OpenCode CLI.
- `HermesProvider`: executor especializado disponivel na VPS.
- `ClaudeProvider`: provider futuro se houver CLI/OAuth disponivel.

O DRW nao armazena API keys de LLM. As CLIs devem estar autenticadas previamente no usuario Linux que roda o servico.

## Workflow DSL

Modelos principais:

```text
Workflow
  id
  name
  objective
  policy
  steps[]

Step
  id
  type
  config
  depends_on[]
  concurrency
  timeout_seconds
  retry_policy
```

Na V1, `Step.type` deve ser fechado e validado com `Literal`, sem permitir que o LLM invente novos steps.

Tipos permitidos na V1:

```text
StepType = Literal[
  "parallel_research",
  "aggregation",
  "verification",
  "critic",
  "refinement",
  "report",
  "cli_agent_task"
]
```

Tipos iniciais de step:

- `parallel_research`
- `cli_agent_task`
- `aggregation`
- `verification`
- `critic`
- `refinement`
- `report`

## WorkflowPolicy

`WorkflowPolicy` e obrigatoria para impedir explosao de workers, tempo, artifacts e chamadas CLI.

Campos iniciais:

```text
WorkflowPolicy
  max_workers
  max_parallel_workers
  max_runtime_minutes
  max_artifacts
  max_cli_invocations
  max_refinement_rounds
  max_estimated_cost
```

Mesmo sem API paga no V1, `max_estimated_cost` fica no contrato para suportar providers pagos no futuro. No V1, os limites mais importantes sao runtime, concorrencia, artifacts e invocacoes CLI.

## Persistencia

### PostgreSQL

Persistir:

- workflows;
- runs;
- steps;
- worker executions;
- events;
- artifact metadata;
- reports metadata;
- checkpoints;
- subprocess exit codes.

### Local Artifact Store

V1 usa filesystem local:

```text
storage/
  artifacts/
  reports/
  logs/
```

Interface preparada:

```text
ArtifactStore
  LocalArtifactStore
  S3ArtifactStore
```

`S3ArtifactStore` sera implementacao futura para MinIO/S3-compatible storage sem mudar runtime/workers.

### Artifact Lineage

Artifacts devem carregar linhagem para rastreabilidade.

Campos obrigatorios de metadata:

```text
ArtifactMetadata
  id
  workflow_id
  run_id
  step_id
  worker_id
  parent_ids[]
  type
  source
  path
  created_at
```

Isso permite responder de onde veio cada conclusao, qual worker produziu o dado e quais artifacts foram usados como base.

## Seguranca

- MCP exposto somente via Tailscale.
- Token simples obrigatorio para MCP.
- Secrets em `.env` ou Docker secrets.
- Nenhum secret versionado.
- Logs devem mascarar tokens, prompts sensiveis e variaveis de ambiente criticas.
- Subprocessos com timeout obrigatorio.
- Workdir isolado por run/worker.
- Allowlist de comandos para execucao controlada.
- Workers podem criar artifacts e rodar comandos permitidos, mas nao alteram projetos/codigo sem permissao explicita no workflow.

## Observabilidade

- Logs estruturados JSON.
- Eventos persistidos por workflow, step e worker.
- Metricas minimas:
  - duracao por step;
  - numero de workers;
  - retries;
  - falhas;
  - artifacts gerados;
  - invocacoes CLI;
  - subprocess exit codes.
- OpenTelemetry Collector opcional no Compose.
- LangSmith nao e obrigatorio no V1 porque o backend principal e CLI/OAuth, nao chamada direta via LangChain API.

## Deploy Na VPS

Docker Compose inicial:

- `drw-mcp`
- `postgres`
- `backup` opcional
- `otel-collector` opcional

Requisitos da VPS:

- Tailscale ativo.
- Codex CLI instalado e autenticado no usuario do servico.
- OpenCode CLI instalado/autenticado se usado como fallback.
- Hermes disponivel se usado como executor.
- Backups para PostgreSQL e `storage/`.

## Fluxo De Uso

```text
OpenCode chama MCP: start_workflow(objective)
  |
DRW classifica o objetivo e escolhe um template
  |
DRW gera Workflow DSL adaptada com provider padrao
  |
Runtime valida DSL e aplica WorkflowPolicy
  |
Scheduler executa async workers e subprocess workers
  |
Cada bloco passa por Verifier/Critic/Refinement
  |
Artifacts sao persistidos localmente
  |
Report final fica disponivel via MCP
```

## Ordem De Implementacao

1. Criar estrutura do projeto Python.
2. Definir modelos Pydantic de workflow, policy, artifacts e reports.
3. Definir `StepType` fechado e templates iniciais.
4. Criar Workflow Classifier e selecao de template.
5. Criar interfaces de storage e `LocalArtifactStore` com lineage.
6. Criar persistencia PostgreSQL para estado, eventos e metadata.
7. Criar Event Bus interno.
8. Criar provider interface e `CodexProvider` via subprocess.
9. Criar subprocess manager com timeout, logs e workdir isolado.
10. Criar runtime async com scheduler e limites por policy.
11. Criar workers iniciais para pesquisa e CLI tasks.
12. Criar verifier/critic/refinement por bloco.
13. Criar MCP HTTP/SSE com tools basicas.
14. Criar Docker Compose dev/prod.
15. Configurar OpenCode para consumir o MCP via Tailscale.

## Fora Do Escopo Inicial

- UI/TUI propria.
- MinIO obrigatorio.
- Knowledge Graph.
- Memory Layer.
- Vector Database.
- Multi-Agent Debate.
- Self Improving Workflows.
- Auto Workflow Evolution.
- Kubernetes.
- Microservicos separados por componente.
- Execucao irrestrita em repositorios.
- API publica fora da Tailscale.
- Dependencia obrigatoria de OpenRouter ou API token LLM.

## Riscos E Mitigacoes

| Risco | Mitigacao |
| --- | --- |
| Workflow Generator criar tarefas demais | `WorkflowPolicy` obrigatoria e scheduler com limites |
| LLM inventar tipos de step invalidos | `StepType` fechado e templates por classe de workflow |
| Codex/OpenCode travar subprocesso | timeout, kill e persistencia de exit code |
| VPS pequena ficar sem memoria | async por padrao, subprocess so para tarefas pesadas, concorrencia baixa |
| Artifact crescer demais | `max_artifacts`, limpeza e reports compactos |
| Conclusao sem rastreabilidade | `ArtifactMetadata.parent_ids`, `step_id` e `worker_id` obrigatorios |
| Provider CLI mudar formato de saida | validacao Pydantic e retry com prompt de reparo |
| Secrets vazarem em logs | mascaramento e proibicao de logar env completo |
| Falha no meio de workflow longo | checkpoints e retomada por run/step |

## Criterios De Sucesso

- OpenCode consegue iniciar um workflow via MCP privado.
- O DRW classifica um objetivo, escolhe template e gera uma DSL validada.
- O runtime executa workers async e subprocess workers respeitando `WorkflowPolicy`.
- Artifacts e report final sao persistidos em `storage/`.
- Artifacts registram lineage com parent artifacts, step e worker.
- O status do workflow e consultavel via MCP.
- Uma falha de worker nao derruba o servico inteiro.
- Um workflow interrompido deixa checkpoints suficientes para diagnostico e retomada futura.
