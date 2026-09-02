import re
import unicodedata
import requests


# ============================================================
# CONFIGURAÇÕES
# ============================================================

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

HEADERS = {
    "User-Agent": "WebScrappingForlith/1.0",
    "Referer": "https://overpass-turbo.eu/"
}

# Quanto maior, mais rigoroso será o filtro.
MIN_SCORE = 5

# Quantos resultados imprimir.
MAX_RESULTADOS = 100


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(texto):
    """
    Normaliza texto para facilitar comparação e deduplicação.
    """
    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def primeiro_valor(tags, chaves):
    """
    Retorna o primeiro valor encontrado entre várias chaves.
    """
    for chave in chaves:
        valor = tags.get(chave)

        if valor and valor.strip():
            return valor.strip()

    return None


def obter_nome(tags):
    return primeiro_valor(
        tags,
        [
            "name",
            "official_name",
            "short_name"
        ]
    )


def obter_telefone(tags):
    return primeiro_valor(
        tags,
        [
            "phone",
            "contact:phone",
            "telephone",
            "contact:telephone"
        ]
    )


def obter_website(tags):
    return primeiro_valor(
        tags,
        [
            "website",
            "contact:website",
            "url"
        ]
    )


def obter_email(tags):
    return primeiro_valor(
        tags,
        [
            "email",
            "contact:email"
        ]
    )


def obter_redes_sociais(tags):
    redes = []

    campos = {
        "Instagram": [
            "contact:instagram",
            "instagram"
        ],
        "Facebook": [
            "contact:facebook",
            "facebook"
        ],
        "Twitter": [
            "contact:twitter",
            "twitter"
        ],
        "TikTok": [
            "contact:tiktok",
            "tiktok"
        ]
    }

    for rede, chaves in campos.items():
        valor = primeiro_valor(tags, chaves)

        if valor:
            redes.append(f"{rede}: {valor}")

    return redes


def obter_endereco(tags):
    partes = []

    rua = tags.get("addr:street")
    numero = tags.get("addr:housenumber")
    bairro = tags.get("addr:suburb")
    cidade = tags.get("addr:city")
    cep = tags.get("addr:postcode")

    if rua:
        if numero:
            partes.append(f"{rua}, {numero}")
        else:
            partes.append(rua)

    if bairro:
        partes.append(bairro)

    if cidade:
        partes.append(cidade)

    if cep:
        partes.append(f"CEP {cep}")

    if not partes:
        return None

    return " - ".join(partes)


def obter_coordenadas(elemento):
    """
    Obtém latitude/longitude de node, way ou relation.
    """

    if elemento.get("type") == "node":
        return (
            elemento.get("lat"),
            elemento.get("lon")
        )

    center = elemento.get("center")

    if center:
        return (
            center.get("lat"),
            center.get("lon")
        )

    return None, None


def obter_url_osm(elemento):
    """
    Gera o link para o objeto no OpenStreetMap.
    """

    tipo = elemento.get("type")
    osm_id = elemento.get("id")

    if not tipo or not osm_id:
        return None

    return f"https://www.openstreetmap.org/{tipo}/{osm_id}"


# ============================================================
# SCORE DO LEAD
# ============================================================

def calcular_score(tags, latitude, longitude):
    """
    Calcula a qualidade do lead.

    Pontuação:

    +2  não possui website no OSM
    +3  possui telefone
    +2  possui endereço
    +2  possui e-mail
    +1  possui rede social
    +1  possui coordenadas
    """

    score = 0

    website = obter_website(tags)
    telefone = obter_telefone(tags)
    email = obter_email(tags)
    endereco = obter_endereco(tags)
    redes = obter_redes_sociais(tags)

    if not website:
        score += 2

    if telefone:
        score += 3

    if endereco:
        score += 2

    if email:
        score += 2

    if redes:
        score += 1

    if latitude is not None and longitude is not None:
        score += 1

    return score


# ============================================================
# FILTRO DE LEADS
# ============================================================

def filtrar_lead(elemento):
    """
    Decide se um estabelecimento deve ser considerado
    um lead relevante.
    """

    tags = elemento.get("tags", {})

    nome = obter_nome(tags)

    # --------------------------------------------------------
    # 1. Precisa ter nome
    # --------------------------------------------------------

    if not nome:
        return False

    # --------------------------------------------------------
    # 2. Se possui website cadastrado no OSM,
    #    não é interessante para nossa busca.
    # --------------------------------------------------------

    website = obter_website(tags)

    if website:
        return False

    # --------------------------------------------------------
    # 3. Precisa ter algum meio de contato/localização.
    #
    #    Sem telefone E sem endereço = praticamente inútil.
    # --------------------------------------------------------

    telefone = obter_telefone(tags)
    endereco = obter_endereco(tags)

    if not telefone and not endereco:
        return False

    # --------------------------------------------------------
    # 4. Coordenadas
    # --------------------------------------------------------

    latitude, longitude = obter_coordenadas(elemento)

    # --------------------------------------------------------
    # 5. Score
    # --------------------------------------------------------

    score = calcular_score(
        tags,
        latitude,
        longitude
    )

    if score < MIN_SCORE:
        return False

    return True


# ============================================================
# DEDUPLICAÇÃO
# ============================================================

def chave_deduplicacao(elemento):
    """
    Cria uma chave para identificar estabelecimentos
    potencialmente duplicados.
    """

    tags = elemento.get("tags", {})

    nome = obter_nome(tags)
    endereco = obter_endereco(tags)
    telefone = obter_telefone(tags)

    nome = normalizar_texto(nome)
    endereco = normalizar_texto(endereco)
    telefone = normalizar_texto(telefone)

    # Preferimos telefone quando disponível.
    if telefone:
        return (
            "telefone",
            nome,
            telefone
        )

    # Caso contrário usamos nome + endereço.
    return (
        "endereco",
        nome,
        endereco
    )


def remover_duplicados(elementos):
    vistos = set()
    resultado = []

    for elemento in elementos:

        chave = chave_deduplicacao(elemento)

        if chave in vistos:
            continue

        vistos.add(chave)
        resultado.append(elemento)

    return resultado


# ============================================================
# BUSCA NO OVERPASS
# ============================================================

def buscar_estabelecimentos(cidade, categoria):

    cidade_regex = re.escape(cidade)

    query = f"""
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
    """

    print()
    print("=" * 70)
    print("Consultando OpenStreetMap / Overpass...")
    print("=" * 70)

    try:

        resposta = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=180
        )

        resposta.raise_for_status()

        dados = resposta.json()

        return dados.get("elements", [])

    except requests.exceptions.Timeout:

        print()
        print("ERRO: a consulta demorou demais.")
        return []

    except requests.exceptions.HTTPError as erro:

        print()
        print("ERRO HTTP:", erro)

        if resposta.text:
            print(resposta.text[:1000])

        return []

    except requests.exceptions.RequestException as erro:

        print()
        print("ERRO de conexão:", erro)

        return []

    except ValueError:

        print()
        print("ERRO: resposta da API não é um JSON válido.")

        return []


# ============================================================
# PREPARAR LEADS
# ============================================================

def preparar_leads(elementos):

    leads = []

    for elemento in elementos:

        if not filtrar_lead(elemento):
            continue

        tags = elemento.get("tags", {})

        nome = obter_nome(tags)

        telefone = obter_telefone(tags)
        email = obter_email(tags)
        website = obter_website(tags)
        endereco = obter_endereco(tags)

        redes = obter_redes_sociais(tags)

        latitude, longitude = obter_coordenadas(elemento)

        score = calcular_score(
            tags,
            latitude,
            longitude
        )

        lead = {
            "nome": nome,
            "telefone": telefone,
            "email": email,
            "website": website,
            "endereco": endereco,
            "redes": redes,
            "latitude": latitude,
            "longitude": longitude,
            "score": score,
            "osm_url": obter_url_osm(elemento),
            "tipo": elemento.get("type"),
            "id": elemento.get("id")
        }

        leads.append(lead)

    # --------------------------------------------------------
    # Remove duplicados
    # --------------------------------------------------------

    leads_por_chave = {}

    for lead in leads:

        chave = (
            normalizar_texto(lead["nome"]),
            normalizar_texto(lead["telefone"]),
            normalizar_texto(lead["endereco"])
        )

        # Se já existe, mantém o de maior score.
        if chave not in leads_por_chave:

            leads_por_chave[chave] = lead

        elif lead["score"] > leads_por_chave[chave]["score"]:

            leads_por_chave[chave] = lead

    leads = list(leads_por_chave.values())

    # --------------------------------------------------------
    # Ordena pelos melhores leads
    # --------------------------------------------------------

    leads.sort(
        key=lambda lead: lead["score"],
        reverse=True
    )

    return leads


# ============================================================
# IMPRESSÃO
# ============================================================

def imprimir_lead(lead, numero):

    print()
    print("-" * 70)

    print(f"[{numero}] {lead['nome']}")

    print(f"    Score: {lead['score']}")

    if lead["telefone"]:
        print(f"    Telefone: {lead['telefone']}")

    if lead["email"]:
        print(f"    E-mail: {lead['email']}")

    if lead["endereco"]:
        print(f"    Endereço: {lead['endereco']}")

    if lead["redes"]:
        print("    Redes sociais:")

        for rede in lead["redes"]:
            print(f"        - {rede}")

    if lead["latitude"] is not None:
        print(
            f"    Coordenadas: "
            f"{lead['latitude']}, "
            f"{lead['longitude']}"
        )

    if lead["osm_url"]:
        print(f"    OSM: {lead['osm_url']}")

    print("    Website no OSM: NÃO INFORMADO")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("WEB SCRAPING FORLITH")
    print("Busca de estabelecimentos sem website cadastrado")
    print("=" * 70)

    cidade = input("\nCidade: ").strip()
    categoria = input("Categoria OSM (ex: restaurant): ").strip()

    if not cidade:

        print("ERRO: cidade não informada.")
        return

    if not categoria:

        print("ERRO: categoria não informada.")
        return

    elementos = buscar_estabelecimentos(
        cidade,
        categoria
    )

    if not elementos:

        print()
        print("Nenhum resultado encontrado.")
        return

    print()
    print(f"Objetos encontrados pelo OSM: {len(elementos)}")

    # --------------------------------------------------------
    # Filtragem
    # --------------------------------------------------------

    leads = preparar_leads(elementos)

    print(
        f"Leads relevantes após filtros: "
        f"{len(leads)}"
    )

    if not leads:

        print()
        print("Nenhum lead passou pelos filtros.")
        print()
        print("Tente:")
        print("  - diminuir MIN_SCORE")
        print("  - usar outra categoria")
        print("  - usar outra cidade")

        return

    # --------------------------------------------------------
    # Limite
    # --------------------------------------------------------

    resultados = leads[:MAX_RESULTADOS]

    print()
    print("=" * 70)
    print(
        f"EXIBINDO {len(resultados)} "
        f"LEADS DE MAIOR QUALIDADE"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Mostrar resultados
    # --------------------------------------------------------

    for numero, lead in enumerate(resultados, start=1):

        imprimir_lead(
            lead,
            numero
        )

    # --------------------------------------------------------
    # Resumo
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)

    print(
        f"Encontrados no OSM: {len(elementos)}"
    )

    print(
        f"Leads após filtros: {len(leads)}"
    )

    print(
        f"Exibidos: {len(resultados)}"
    )

    print(
        f"Score mínimo: {MIN_SCORE}"
    )

    print()
    print(
        "IMPORTANTE:"
    )

    print(
        "O fato de o OSM não possuir um website "
        "não significa que o estabelecimento realmente "
        "não tenha website."
    )

    print(
        "A próxima etapa deve verificar isso na internet."
    )


if __name__ == "__main__":
    main()