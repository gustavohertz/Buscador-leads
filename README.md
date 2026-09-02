# Web Scrapping Forlith — Documentação

## 1. Visão geral

O **Web Scrapping Forlith** é um projeto em Python para auxiliar na identificação de possíveis leads comerciais.

A ideia inicial do projeto é consultar dados públicos do **OpenStreetMap (OSM)** por meio da **Overpass API**, localizar estabelecimentos de uma determinada categoria em uma cidade e identificar registros que **não possuem um site informado no OpenStreetMap**.

O projeto foi pensado como uma primeira etapa de prospecção. A ausência de um campo `website` no OpenStreetMap **não prova** que o estabelecimento não possui site na Internet. Por isso, uma evolução importante é adicionar uma segunda etapa de verificação na Web.

### Objetivos

- Pesquisar estabelecimentos por cidade e categoria.
- Utilizar dados públicos do OpenStreetMap.
- Evitar dependência inicial de APIs comerciais.
- Identificar registros sem `website` cadastrado no OSM.
- Priorizar leads com informações de contato.
- Exibir os resultados diretamente no terminal.
- Manter o projeto simples, sem banco de dados nesta primeira versão.
- Preparar a arquitetura para futuras etapas de validação.

---

# 2. Tecnologias utilizadas

## Python

Linguagem principal do projeto.

Bibliotecas utilizadas:

- `requests` — comunicação HTTP com a Overpass API.
- `re` — expressões regulares para normalização e validações.
- `unicodedata` — normalização de textos.
- `urllib.parse` — tratamento de URLs.
- `typing` — anotações de tipos.

## OpenStreetMap

Fonte dos dados geográficos e cadastrais.

O OpenStreetMap é um projeto colaborativo de dados geográficos abertos.

## Overpass API

A Overpass API permite realizar consultas sobre os dados do OpenStreetMap utilizando a linguagem Overpass QL.

Endpoint utilizado pelo projeto:

```text
https://overpass-api.de/api/interpreter
```

---

# 3. Estrutura do projeto

Uma estrutura esperada para o projeto é:

```text
Web_Scrapping_forlith/
├── buscar.py
├── README.md
└── ...
```

A implementação atual concentra a lógica principal em:

```text
buscar.py
```

Em versões futuras, recomenda-se separar a aplicação em módulos:

```text
Web_Scrapping_forlith/
├── buscar.py
├── config.py
├── overpass.py
├── filtros.py
├── scoring.py
├── normalizacao.py
├── verificacao_web.py
├── models.py
├── requirements.txt
├── README.md
└── tests/
    ├── test_filtros.py
    ├── test_scoring.py
    └── test_normalizacao.py
```

Essa separação não é obrigatória para a versão inicial, mas facilita manutenção e testes.

---

# 4. Pré-requisitos

Recomenda-se utilizar:

- Linux/Fedora ou outro sistema Unix-like.
- Python 3.
- `pip`.
- Conexão com a Internet.

Verifique:

```bash
python3 --version
```

e:

```bash
python3 -m pip --version
```

---

# 5. Ambiente virtual

É recomendado utilizar um ambiente virtual para evitar conflitos entre dependências.

Crie:

```bash
python3 -m venv .venv
```

Ative:

```bash
source .venv/bin/activate
```

Depois:

```bash
python -m pip install --upgrade pip
```

Instale a dependência principal:

```bash
pip install requests
```

Caso seja criado um `requirements.txt`:

```bash
pip install -r requirements.txt
```

Um `requirements.txt` inicial pode conter:

```text
requests
```

---

# 6. Execução

Com o ambiente virtual ativado:

```bash
python buscar.py
```

Se o projeto estiver configurado para receber argumentos:

```bash
python buscar.py "Rio de Janeiro" "dentista"
```

A forma exata depende da implementação atual do `buscar.py`.

---

# 7. Configurações principais

A versão atual utiliza configurações semelhantes a:

```python
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

MIN_SCORE = 5

MAX_RESULTADOS = 100
```

## OVERPASS_URL

Define o servidor Overpass utilizado para realizar as consultas.

Exemplo:

```python
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
```

## MIN_SCORE

Define a pontuação mínima necessária para um resultado aparecer.

Exemplo:

```python
MIN_SCORE = 5
```

Quanto maior esse valor, mais restritivo será o filtro.

## MAX_RESULTADOS

Limita a quantidade máxima de resultados exibidos.

Exemplo:

```python
MAX_RESULTADOS = 100
```

Isso ajuda a evitar uma quantidade excessiva de informações no terminal.

---

# 8. Consulta Overpass

A consulta principal utilizada pelo projeto segue o conceito:

```overpass
[out:json][timeout:120];

area
  ["name"~"^{cidade_regex}$",i]
  ["boundary"="administrative"]
  ["admin_level"="8"]
  ->.searchArea;

nwr
  ["amenity"="{categoria}"]
  ["name"]
  (area.searchArea);

out center tags;
```

## Explicação

### `[out:json]`

Solicita que a resposta seja retornada em JSON.

Isso facilita o processamento no Python.

### `[timeout:120]`

Define um limite de tempo de 120 segundos para a consulta.

### `area`

Seleciona uma área administrativa.

### `name`

Procura a cidade pelo nome.

A consulta utiliza expressão regular com comparação case-insensitive.

### `boundary="administrative"`

Restringe a busca a limites administrativos.

### `admin_level="8"`

No contexto brasileiro, esse nível é usado para representar municípios em muitos dados administrativos do OSM.

### `nwr`

Significa:

- `node`
- `way`
- `relation`

Ou seja, permite encontrar os três tipos de objetos do OpenStreetMap.

### `amenity`

Filtra pela categoria do estabelecimento.

Por exemplo:

```text
amenity=dentist
```

### `name`

Exige que o objeto possua nome.

### `out center tags`

Retorna as tags do objeto e, quando necessário, um centro para objetos que não sejam simples nodes.

---

# 9. Comunicação com a Overpass API

A requisição deve utilizar cabeçalhos apropriados.

Exemplo:

```python
HEADERS = {
    "User-Agent": "WebScrappingForlith/1.0",
    "Referer": "https://overpass-turbo.eu/"
}
```

A consulta é enviada com:

```python
requests.post(
    OVERPASS_URL,
    data={"data": query},
    headers=HEADERS,
    timeout=180
)
```

## Por que usar User-Agent?

Serviços públicos precisam conseguir identificar a aplicação que está fazendo requisições.

Um User-Agent explícito também ajuda no diagnóstico de problemas.

## Por que apareceu HTTP 406?

Na implementação inicial, a requisição à Overpass API retornou:

```text
HTTP 406
```

A utilização de cabeçalhos adequados e o envio da consulta como formulário:

```python
data={"data": query}
```

resolveram o problema.

---

# 10. Dados coletados

O projeto tenta aproveitar informações disponíveis nas tags do OpenStreetMap.

Entre elas:

- nome;
- telefone;
- website;
- e-mail;
- endereço;
- redes sociais;
- latitude;
- longitude;
- identificador OSM;
- URL do objeto no OpenStreetMap.

Nem todos os estabelecimentos terão todas essas informações.

Isso é normal em dados colaborativos.

---

# 11. Website

Uma das principais regras do projeto é identificar registros que não possuem website informado no OSM.

Exemplo conceitual:

```python
if not website:
    ...
```

Entretanto, existe uma limitação muito importante:

> `website` vazio no OpenStreetMap não significa que o estabelecimento não possui website.

Pode simplesmente significar que nenhum colaborador cadastrou essa informação.

### Exemplo de falso positivo

Um estabelecimento conhecido pode aparecer sem `website` no OSM mesmo possuindo um site oficial.

Portanto, o resultado deve ser interpretado como:

```text
"não possui website cadastrado no OSM"
```

e não como:

```text
"não possui website"
```

A segunda afirmação exige uma verificação externa.

---

# 12. Filtros

A aplicação utiliza filtros para melhorar a qualidade dos resultados.

## Nome obrigatório

Registros sem nome são descartados.

Conceito:

```python
if not name:
    continue
```

Isso evita resultados pouco úteis para prospecção.

---

## Website cadastrado no OSM

Se existe website no registro:

```python
if website:
    continue
```

O registro pode ser descartado porque o objetivo inicial é encontrar potenciais leads sem website cadastrado.

---

## Telefone ou endereço

A aplicação exige pelo menos uma forma básica de identificação/contato:

```text
telefone OU endereço
```

Isso reduz registros incompletos.

---

# 13. Sistema de pontuação

O projeto utiliza um score para priorizar resultados.

Pontuação atual:

| Critério | Pontos |
|---|---:|
| Sem website no OSM | +2 |
| Possui telefone | +3 |
| Possui endereço | +2 |
| Possui e-mail | +2 |
| Possui rede social | +1 |
| Possui coordenadas | +1 |

Pontuação máxima:

```text
11 pontos
```

O resultado só é exibido quando:

```text
score >= MIN_SCORE
```

Com:

```python
MIN_SCORE = 5
```

---

# 14. Por que usar score?

Nem todos os leads possuem a mesma qualidade.

Por exemplo:

```text
Lead A
Nome: Clínica X
Telefone: presente
Endereço: presente
E-mail: presente
Coordenadas: presentes
Score: alto
```

é mais interessante do que:

```text
Lead B
Nome: Loja Y
Telefone: ausente
Endereço: ausente
Score: baixo
```

O score permite ordenar ou filtrar resultados sem precisar criar regras extremamente complexas.

---

# 15. Normalização

O projeto utiliza normalização para evitar duplicidades.

Exemplos:

```text
"Clínica São José"
"clinica sao jose"
"CLÍNICA SÃO JOSÉ"
```

podem representar o mesmo estabelecimento.

A normalização pode:

1. converter para minúsculas;
2. remover acentos;
3. remover espaços extras;
4. remover caracteres desnecessários.

Exemplo conceitual:

```python
def normalizar(texto):
    ...
```

---

# 16. Deduplicação

O mesmo estabelecimento pode aparecer mais de uma vez no resultado do OSM.

A aplicação utiliza informações como:

- nome;
- telefone;
- endereço.

para tentar identificar duplicatas.

Exemplo conceitual:

```text
nome_normalizado + telefone_normalizado
```

ou:

```text
nome_normalizado + endereço_normalizado
```

Isso evita apresentar repetidamente o mesmo lead.

---

# 17. Coordenadas

O OpenStreetMap fornece informações geográficas.

Normalmente:

```text
latitude
longitude
```

podem ser utilizadas para localizar o estabelecimento.

Essas coordenadas também podem ser úteis futuramente para:

- gerar links para mapas;
- calcular distâncias;
- agrupar leads;
- pesquisar regiões específicas;
- cruzar dados com outras fontes.

---

# 18. URLs do OpenStreetMap

Um resultado pode possuir um identificador como:

```text
node/123456789
```

ou:

```text
way/123456789
```

A aplicação pode transformar isso em uma URL navegável do OpenStreetMap.

Isso facilita a conferência manual do lead.

---

# 19. Tratamento de erros

Consultas a serviços externos podem falhar.

Exemplos:

```text
ConnectionError
Timeout
HTTP 429
HTTP 500
HTTP 502
HTTP 503
```

Por isso, requisições devem possuir timeout:

```python
timeout=180
```

Também é importante verificar a resposta:

```python
response.raise_for_status()
```

ou tratar explicitamente os códigos HTTP.

---

# 20. Limites da Overpass API

A Overpass API é um serviço público e compartilhado.

Não deve ser tratada como uma API privada ilimitada.

Problemas possíveis:

- consultas demoradas;
- rate limiting;
- indisponibilidade temporária;
- excesso de carga;
- timeout;
- respostas muito grandes.

Boas práticas:

- limitar consultas;
- evitar loops com centenas de requisições desnecessárias;
- utilizar filtros específicos;
- utilizar timeout;
- armazenar resultados quando fizer sentido;
- respeitar as políticas do serviço.

---

# 21. Por que não utilizar Google Places inicialmente?

Uma alternativa seria utilizar serviços comerciais de localização e Places.

Porém, para este projeto, a primeira implementação prioriza dados abertos.

### Vantagens do OSM/Overpass

- dados abertos;
- sem necessidade de chave comercial para a consulta pública utilizada;
- possibilidade de consultar diferentes tipos de objetos;
- grande cobertura geográfica;
- independência de um fornecedor comercial.

### Desvantagens

- cobertura varia conforme região;
- dados podem estar desatualizados;
- campos podem estar incompletos;
- ausência de website não significa ausência de website real;
- serviços públicos possuem limites;
- qualidade depende da comunidade.

---

# 22. Arquitetura atual

A arquitetura simplificada é:

```text
                 ┌─────────────────────┐
                 │      Usuário        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     buscar.py       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Overpass API     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   OpenStreetMap     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Filtros + Score +   │
                 │    Deduplicação     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      Terminal       │
                 └─────────────────────┘
```

---

# 23. O que o projeto faz atualmente

Fluxo:

```text
1. Recebe cidade
2. Recebe categoria
3. Localiza a área administrativa
4. Consulta estabelecimentos no OSM
5. Recebe dados em JSON
6. Extrai informações relevantes
7. Descarta registros sem nome
8. Descarta registros que possuem website cadastrado no OSM
9. Exige telefone ou endereço
10. Calcula score
11. Remove duplicatas
12. Ordena/filtra resultados
13. Exibe os leads
```

---

# 24. O que o projeto ainda NÃO faz

É importante deixar claro que a primeira versão não comprova se um estabelecimento realmente não possui site.

Ela apenas verifica:

```text
website cadastrado no OpenStreetMap
```

Ainda não existe necessariamente uma etapa que faça:

```text
Google/Bing/DuckDuckGo/Web
        ↓
pesquisa pelo estabelecimento
        ↓
encontra possíveis domínios
        ↓
verifica se existe site oficial
```

Essa etapa é recomendada como evolução.

---

# 25. Segunda etapa recomendada: verificação real do website

Uma arquitetura mais completa seria:

```text
             OpenStreetMap
                   │
                   ▼
           ┌───────────────┐
           │ Lista de leads│
           └───────┬───────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Verificação Web  │
          └────────┬─────────┘
                   │
          ┌────────┴─────────┐
          ▼                  ▼
      Encontrou?          Não encontrou?
          │                  │
          ▼                  ▼
      descartar          candidato
```

O objetivo seria reduzir falsos positivos.

---

# 26. Verificação de domínio

Uma abordagem futura pode tentar identificar o site oficial por:

- nome do estabelecimento;
- telefone;
- endereço;
- cidade;
- domínio encontrado;
- correspondência de informações.

Não é suficiente simplesmente encontrar qualquer página com o mesmo nome.

Por exemplo:

```text
"Clínica Saúde"
```

pode existir em várias cidades.

A validação deve considerar múltiplos sinais.

---

# 27. Validação de um possível site

Um domínio pode ser considerado mais confiável quando existem sinais como:

- nome compatível;
- telefone compatível;
- endereço compatível;
- cidade compatível;
- página institucional;
- informações de contato;
- domínio coerente com a organização.

Isso permite reduzir falsos positivos.

---

# 28. Cuidados com scraping

A segunda etapa, caso utilize páginas externas, deve respeitar:

- `robots.txt` quando aplicável;
- termos de uso;
- limites de requisição;
- privacidade;
- legislação aplicável;
- ausência de autenticação/bypass;
- identificação adequada do cliente quando necessário.

O objetivo é coletar informações públicas de forma responsável.

---

# 29. Privacidade

O projeto trabalha com informações potencialmente públicas, mas isso não significa que qualquer uso seja automaticamente apropriado.

Evite coletar:

- senhas;
- tokens;
- dados de autenticação;
- documentos pessoais;
- dados privados;
- informações que não sejam necessárias para a finalidade do projeto.

Priorize dados comerciais públicos, como:

- nome do estabelecimento;
- telefone comercial;
- endereço comercial;
- website;
- e-mail comercial;
- redes sociais comerciais.

---

# 30. Segurança de credenciais

Nunca coloque tokens ou senhas diretamente no código.

Evite:

```python
TOKEN = "meu-token-super-secreto"
```

Prefira variáveis de ambiente:

```bash
export API_TOKEN="..."
```

e no Python:

```python
import os

token = os.getenv("API_TOKEN")
```

Nunca faça commit de arquivos contendo credenciais.

Adicione ao `.gitignore`:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

# 31. Git

O projeto está sendo versionado com Git.

Verificar estado:

```bash
git status
```

Ver commits:

```bash
git log --oneline
```

Ver branches:

```bash
git branch
```

Ver repositórios remotos:

```bash
git remote -v
```

---

# 32. Primeiro commit

Exemplo:

```bash
git add .
git commit -m "feat: implementa buscador inicial de leads"
```

Depois:

```bash
git push --set-upstream origin master
```

Depois que o upstream estiver configurado:

```bash
git push
```

---

# 33. Autenticação do GitHub

O GitHub não aceita mais senha normal para operações Git via HTTPS.

Ao executar:

```bash
git push
```

e aparecer:

```text
Username for 'https://github.com':
```

utilize o usuário do GitHub.

Quando aparecer:

```text
Password for 'https://usuario@github.com':
```

não utilize a senha normal da conta.

Para HTTPS, utilize um **Personal Access Token (PAT)**.

Outra alternativa é configurar autenticação por SSH.

Nunca compartilhe um token em:

- commits;
- código-fonte;
- screenshots;
- chats;
- README;
- arquivos públicos.

---

# 34. SSH para GitHub

Uma evolução recomendada é utilizar SSH.

Verifique se já existem chaves:

```bash
ls -la ~/.ssh
```

Procure por arquivos como:

```text
id_ed25519
id_ed25519.pub
```

Caso ainda não tenha uma chave, pode ser criada com:

```bash
ssh-keygen -t ed25519 -C "seu-email"
```

Depois a chave pública:

```bash
cat ~/.ssh/id_ed25519.pub
```

pode ser adicionada às configurações da conta GitHub.

Depois disso, o remote pode utilizar o formato SSH:

```text
git@github.com:gustavohertz/Buscador-leads.git
```

Isso evita digitar um token em cada operação.

---

# 35. `.gitignore`

Um `.gitignore` recomendado:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
.venv/
venv/
env/

# Environment variables
.env
.env.*

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.temp
```

---

# 36. Testes

A aplicação deve evoluir para testes automatizados.

Áreas importantes:

## Normalização

Testar:

```text
Clínica São José
clinica sao jose
CLÍNICA SÃO JOSÉ
```

e verificar se resultam na mesma chave normalizada.

## Score

Testar diferentes combinações:

```text
telefone + endereço
telefone + e-mail
endereço + social
```

## Filtros

Testar:

- sem nome;
- com website;
- sem telefone;
- sem endereço;
- score abaixo do mínimo;
- score acima do mínimo.

## Deduplicação

Testar dois registros que representam o mesmo estabelecimento.

---

# 37. Exemplo de teste

Com `pytest`, um teste poderia ser:

```python
def test_lead_sem_website_pode_ser_priorizado():
    lead = {
        "name": "Clínica Exemplo",
        "phone": "+55 21 99999-9999",
        "address": "Rua Exemplo, 100",
        "website": None,
    }

    assert lead["website"] is None
```

O teste real deve utilizar as funções existentes no projeto.

---

# 38. Melhorias futuras

## Curto prazo

- Criar `requirements.txt`.
- Separar configurações.
- Adicionar testes.
- Melhorar tratamento de erros.
- Melhorar saída no terminal.
- Permitir argumentos via CLI.
- Permitir múltiplas categorias.
- Salvar resultados em CSV.

## Médio prazo

- Verificar websites externamente.
- Validar domínio.
- Detectar redes sociais.
- Calcular distância entre leads.
- Criar cache.
- Implementar retry com backoff.
- Registrar logs.

## Longo prazo

- Banco PostgreSQL/PostGIS.
- Interface web.
- API REST.
- Dashboard.
- Histórico de leads.
- Atualização automática.
- Sistema de classificação mais sofisticado.

---

# 39. Exportação CSV

Uma evolução simples seria gerar:

```text
leads.csv
```

com colunas:

```text
name
phone
email
website
address
latitude
longitude
social
score
osm_url
```

Isso permitiria abrir os dados no LibreOffice Calc, Excel ou importar em outro sistema.

---

# 40. Banco de dados

Quando o volume aumentar, um banco pode ser útil.

Uma opção:

```text
PostgreSQL + PostGIS
```

Estrutura conceitual:

```text
Lead
├── id
├── nome
├── telefone
├── email
├── website
├── endereco
├── latitude
├── longitude
├── score
├── osm_id
├── criado_em
└── atualizado_em
```

Com PostGIS, a localização poderia ser armazenada como geometria.

---

# 41. Cache

Uma melhoria importante é evitar consultar repetidamente os mesmos dados.

Fluxo:

```text
Consulta
   │
   ▼
Existe no cache?
 ┌─┴─┐
Sim Não
 │   │
 ▼   ▼
usa consulta Overpass
cache
```

Isso reduz:

- tráfego;
- tempo;
- carga no serviço;
- risco de rate limiting.

---

# 42. Retry

Falhas temporárias podem ser tratadas com tentativas controladas.

Exemplo conceitual:

```text
Tentativa 1
   ↓
falhou
   ↓
espera
   ↓
Tentativa 2
   ↓
falhou
   ↓
espera mais
   ↓
Tentativa 3
```

O intervalo deve aumentar progressivamente.

Isso é chamado de **exponential backoff**.

---

# 43. Logging

Em vez de utilizar somente `print`, uma aplicação maior pode utilizar:

```python
import logging
```

Isso permite separar:

```text
INFO
WARNING
ERROR
DEBUG
```

Exemplo:

```text
INFO: Consultando Rio de Janeiro
INFO: 87 estabelecimentos encontrados
WARNING: Consulta demorou 45 segundos
INFO: 23 leads após filtragem
```

---

# 44. CLI

Uma interface de linha de comando pode tornar o programa mais profissional.

Exemplo desejado:

```bash
python buscar.py \
    --cidade "Rio de Janeiro" \
    --categoria dentist \
    --min-score 5 \
    --max-resultados 100
```

Outra possibilidade:

```bash
python buscar.py --help
```

mostrar:

```text
usage: buscar.py [-h] --cidade CIDADE --categoria CATEGORIA

Busca potenciais leads utilizando OpenStreetMap.

options:
  --cidade
  --categoria
  --min-score
  --max-resultados
```

Para isso, pode ser utilizado o módulo padrão:

```python
argparse
```

---

# 45. Exemplo de fluxo completo

Uma execução ideal seria:

```text
$ python buscar.py --cidade "Rio de Janeiro" --categoria dentist

Consultando OpenStreetMap...
Área encontrada.

Consultando estabelecimentos...
87 registros encontrados.

Aplicando filtros...
42 registros possuem informações suficientes.

Calculando score...
31 registros atingiram a pontuação mínima.

Removendo duplicatas...
28 leads únicos.

Resultados:

1. Clínica Exemplo
   Telefone: +55 ...
   Endereço: ...
   Score: 10
   OSM: ...

2. Consultório Exemplo
   Telefone: +55 ...
   Endereço: ...
   Score: 8
   OSM: ...
```

---

# 46. Problemas conhecidos

## OSM incompleto

Nem todos os estabelecimentos estão cadastrados.

## Website ausente

Pode existir um website que não foi cadastrado no OSM.

## Dados desatualizados

Telefone, endereço ou outros dados podem ter mudado.

## Duplicatas

Estabelecimentos podem possuir múltiplos objetos no OSM.

## Categoria

Um estabelecimento pode estar classificado de maneira diferente da esperada.

## Overpass

A consulta pode sofrer timeout ou indisponibilidade.

---

# 47. Falso positivo

Um dos principais problemas atuais é:

```text
website OSM = vazio
```

ser interpretado incorretamente como:

```text
site real = inexistente
```

A interpretação correta é:

```text
website OSM = vazio
        ↓
potencial lead
        ↓
verificação externa
        ↓
site encontrado?
        ├── sim → não é lead
        └── não → lead confirmado
```

Essa mudança conceitual é importante para a evolução do projeto.

---

# 48. Qualidade do lead

Uma versão futura pode separar os leads em níveis:

```text
A — alta confiança
B — média confiança
C — baixa confiança
```

Exemplo:

### A

- telefone confirmado;
- endereço confirmado;
- nenhum website encontrado;
- informações consistentes.

### B

- telefone;
- endereço;
- website não confirmado.

### C

- somente nome;
- poucos dados complementares.

Isso é mais informativo do que apenas um número.

---

# 49. Verificação de site oficial

Uma implementação futura pode utilizar mecanismos de busca para pesquisar combinações como:

```text
"Nome do estabelecimento" "Cidade"
```

e:

```text
"Nome do estabelecimento" telefone
```

Depois, os resultados podem ser comparados com:

- nome;
- telefone;
- endereço;
- cidade.

É importante não considerar automaticamente o primeiro resultado como site oficial.

---

# 50. Possível arquitetura futura

```text
                         ┌────────────────────┐
                         │      CLI/Web        │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │    Lead Service    │
                         └─────────┬──────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
       ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
       │   OpenStreetMap│ │ Website Checker│ │ Social Checker │
       └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  ▼
                         ┌────────────────────┐
                         │  Lead Validation   │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ PostgreSQL/PostGIS │
                         └────────────────────┘
```

---

# 51. Princípios de desenvolvimento

O projeto deve seguir alguns princípios:

## Simplicidade

Começar com uma implementação pequena e funcional.

## Separação de responsabilidades

Consulta, filtragem, scoring e apresentação devem poder ser separados.

## Testabilidade

Funções devem ser pequenas e testáveis.

## Tratamento de falhas

Serviços externos podem falhar.

## Não confiar cegamente nos dados

Dados públicos podem estar incompletos ou desatualizados.

## Respeito aos serviços utilizados

Não realizar consultas excessivas ou abusivas.

---

# 52. Checklist para novas versões

Antes de considerar uma versão pronta:

```text
[ ] Código executa sem erros
[ ] Dependências documentadas
[ ] requirements.txt atualizado
[ ] .gitignore configurado
[ ] Nenhuma credencial no código
[ ] Tratamento de timeout
[ ] Tratamento de HTTP errors
[ ] Deduplicação funcionando
[ ] Score funcionando
[ ] Filtros testados
[ ] README atualizado
[ ] Git status limpo
[ ] Commit criado
[ ] Push realizado
```

---

# 53. Comandos Git úteis

Ver estado:

```bash
git status
```

Ver alterações:

```bash
git diff
```

Adicionar arquivos:

```bash
git add .
```

Criar commit:

```bash
git commit -m "feat: ..."
```

Enviar:

```bash
git push
```

Atualizar:

```bash
git pull
```

Ver histórico:

```bash
git log --oneline --decorate --graph
```

Ver remote:

```bash
git remote -v
```

Ver branch atual:

```bash
git branch --show-current
```

---

# 54. Diagnóstico do GitHub

Caso apareça:

```text
Could not resolve host: github.com
```

é provável que seja DNS/rede.

Teste:

```bash
ping -c 4 8.8.8.8
```

Depois:

```bash
getent hosts github.com
```

E:

```bash
ping -c 4 github.com
```

Para testar HTTPS:

```bash
curl -I https://github.com
```

Caso DNS funcione mas o Git continue falhando, verificar configurações de proxy:

```bash
git config --global --get http.proxy
git config --global --get https.proxy
```

Também:

```bash
env | grep -i proxy
```

Para diagnosticar a comunicação do Git:

```bash
GIT_CURL_VERBOSE=1 git ls-remote https://github.com/gustavohertz/Buscador-leads.git
```

Esse comando é útil porque testa acesso ao repositório sem realizar `push`.

---

# 55. Fluxo Git recomendado

Para trabalhar normalmente:

```bash
git status
```

```bash
git add .
```

```bash
git commit -m "feat: adiciona ..."
```

```bash
git push
```

Antes de uma alteração maior:

```bash
git status
git branch
git pull
```

Depois:

```bash
git add .
git commit
git push
```

---

# 56. Próximos passos recomendados

A evolução mais lógica do projeto é:

### Etapa 1 — concluída

Consulta básica ao OpenStreetMap.

### Etapa 2 — concluída/parcial

Filtros, score e deduplicação.

### Etapa 3

Exportação para CSV.

### Etapa 4

Verificação real de websites.

### Etapa 5

Melhor classificação de leads.

### Etapa 6

Testes automatizados.

### Etapa 7

Cache e retry.

### Etapa 8

Persistência em PostgreSQL/PostGIS.

### Etapa 9

API REST.

### Etapa 10

Interface web/dashboard.

---

# 57. Resumo técnico

O projeto atualmente pode ser resumido como:

```text
Python
  │
  ├── requests
  │
  ▼
Overpass API
  │
  ▼
OpenStreetMap
  │
  ▼
Dados JSON
  │
  ├── Normalização
  ├── Filtros
  ├── Score
  └── Deduplicação
  │
  ▼
Potenciais leads
```

O ponto mais importante para a próxima evolução é separar:

```text
"não possui website cadastrado no OSM"
```

de:

```text
"não possui website na Internet"
```

A primeira informação pode ser obtida diretamente do OSM. A segunda exige uma etapa adicional de verificação.

---

# 58. Conclusão

O Web Scrapping Forlith possui uma base simples e adequada para um protótipo de geração de leads utilizando dados abertos.

A escolha do OpenStreetMap + Overpass permite começar sem depender de uma API comercial de Places.

A implementação atual deve ser vista como um **filtro inicial de candidatos**, e não como uma confirmação definitiva de que um estabelecimento não possui site.

A arquitetura pode evoluir gradualmente para:

```text
OSM
 ↓
Filtro
 ↓
Score
 ↓
Verificação Web
 ↓
Validação
 ↓
Classificação
 ↓
CSV / Banco
 ↓
API
 ↓
Dashboard
```

Essa abordagem mantém o projeto simples no início e permite adicionar complexidade apenas quando houver necessidade.

---

## Licença e uso dos dados

Antes de distribuir ou utilizar comercialmente dados obtidos do OpenStreetMap, consulte a documentação e os termos/licenças aplicáveis ao OpenStreetMap e ao serviço Overpass utilizado.

A documentação oficial do OpenStreetMap deve ser considerada a referência para as condições de uso dos dados.

---

## Documento

Projeto: **Web Scrapping Forlith**

Arquivo principal: `buscar.py`

Objetivo: **identificação e priorização de potenciais leads utilizando dados públicos do OpenStreetMap.**
