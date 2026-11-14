# Tutorial: Docker Compose do zero (app Python + Redis)

**Objetivo:** dois serviços. Ao subir, a `app` (Python) conecta no `redis`, imprime `PONG` e termina.
O exercício 2 constrói em cima disso.

**Regras do jogo:** quem escreve os arquivos é você. Cada passo tem **o que fazer**, **uma dica**
e **o que você deve ver**. Se travar, abra as dicas em ordem: 🟢 dica → 🟡 dica maior → 🔴 trecho curto.

Estrutura final do projeto:

```
projeto/
├── docker-compose.yml
└── app/
    ├── Dockerfile
    └── main.py
```

---

## Passo 1: Conceitos

- **Imagem**: um "molde" que não muda (o SO, as dependências e o seu código). **Container**: uma instância dessa imagem rodando. É como classe e objeto.
- **Dockerfile**: a receita que gera **uma** imagem. **docker-compose.yml**: descreve **vários** containers e como eles se ligam.
- **Serviço**: cada container declarado no Compose (aqui são `app` e `redis`).
- **Rede**: o Compose cria uma rede padrão onde cada serviço acha o outro **pelo nome do serviço**.
- **Volume**: um armazenamento gerenciado pelo Docker que existe fora do container. Por isso continua lá quando o container é recriado.

📚 [Imagem](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/) ·
[Container](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) ·
[Rede no Compose](https://docs.docker.com/compose/how-tos/networking/) ·
[Volumes](https://docs.docker.com/reference/compose-file/volumes/)

**O que fazer:** crie as pastas e cole este esqueleto em `docker-compose.yml`:

```yaml
services:
  app:
    # TODO: de onde vem a imagem? (build a partir de ./app)
    # TODO: variável de ambiente com o host do Redis
    # TODO: só iniciar quando o redis estiver saudável

  redis:
    # TODO: qual imagem oficial usar?
    # TODO: healthcheck (como saber se está PRONTO?)
    # TODO: montar um volume onde o Redis guarda os dados

# TODO: declarar o volume nomeado aqui embaixo
```

💡 **Dica:** a linha `version:` no topo é obsoleta e o Compose atual a ignora
([doc](https://docs.docker.com/reference/compose-file/version-and-name/)).

✅ **O que ver:** a estrutura de pastas criada. Os serviços ainda estão vazios, então `docker compose config` pode reclamar. Isso é esperado.

❓ **Checkpoint:** por que a app vai usar `redis` como host em vez de `localhost`?

---

## Passo 2: O código da app e o Dockerfile

**O que fazer:**

1. Em `app/main.py`: leia o host do Redis de uma variável de ambiente (por exemplo `REDIS_HOST`), conecte com a
   biblioteca `redis`, faça o PING e imprima o resultado.
2. Em `app/Dockerfile`, escreva estas 5 instruções, nesta ordem, e entenda o papel de cada uma:
   - `FROM`: a imagem base (use uma imagem oficial do Python, de preferência a variante `slim`)
   - `WORKDIR`: a pasta de trabalho dentro do container
   - `RUN`: instala a dependência `redis` com o pip
   - `COPY`: copia o `main.py` para dentro da imagem
   - `CMD`: o comando que roda quando o container inicia

💡 **Dica:** na biblioteca redis-py, `ping()` retorna `True`, e não o texto `"PONG"`. Você vai precisar decidir como
imprimir `PONG` a partir disso ([doc do cliente redis-py](https://redis.io/docs/latest/develop/clients/redis-py/)).

💡 **Dica 2:** use `os.environ` para ler a variável. Nunca escreva `"localhost"` fixo no código.

📚 [Referência do Dockerfile](https://docs.docker.com/reference/dockerfile/) ·
[Imagem oficial do Python](https://hub.docker.com/_/python)

<details><summary>🟢 Dica</summary>
Instale a dependência <b>antes</b> de copiar o código. Assim o Docker reaproveita o cache dessa camada quando só o código muda.
</details>

<details><summary>🟡 Dica maior</summary>
O <code>CMD</code> prefere o formato JSON (lista de strings), por exemplo <code>["programa", "arg"]</code>.
Para a conexão, os parâmetros principais são <code>host</code> e <code>port</code> (a porta padrão do Redis é 6379).
</details>

<details><summary>🔴 Trecho (main.py, parcial)</summary>

```python
import os, redis
host = os.environ["REDIS_HOST"]
r = redis.Redis(host=host, port=6379)
# agora: chame o ping e imprima PONG
```
</details>

✅ **O que ver:** ainda nada rodando. Se quiser, teste o build sozinho com `docker build -t teste-app ./app`, que deve terminar sem erro.

---

## Passo 3: Compose com os dois serviços e a variável de ambiente

**O que fazer:** preencha no `docker-compose.yml`:

- `app`: `build` apontando para `./app` e `environment` com `REDIS_HOST` igual ao **nome do serviço** do Redis.
- `redis`: `image` com a imagem oficial (por exemplo `redis:7-alpine`).

Depois rode:

```
docker compose up --build
```

💡 **Dica:** não precisa declarar rede. O Compose cria uma rede padrão e coloca os dois serviços nela.

📚 [Rede no Compose](https://docs.docker.com/compose/how-tos/networking/) ·
[`environment`](https://docs.docker.com/reference/compose-file/services/#environment) ·
[`build`](https://docs.docker.com/reference/compose-file/build/) ·
[Imagem oficial do Redis](https://hub.docker.com/_/redis)

<details><summary>🟢 Dica</summary>
<code>environment</code> aceita tanto mapa (<code>CHAVE: valor</code>) quanto lista (<code>- CHAVE=valor</code>).
</details>

<details><summary>🔴 Trecho</summary>

```yaml
  app:
    build: ./app
    environment:
      REDIS_HOST: redis
```
</details>

✅ **O que ver:** os logs do `redis` (`Ready to accept connections`), uma linha `app-1  | PONG` e depois
`app-1 exited with code 0`. O Redis continua rodando, e isso é normal. Saia com `Ctrl+C`.

⚠️ **Pode acontecer:** um `ConnectionError` na app, porque ela iniciou antes do Redis estar pronto. É isso que o próximo passo resolve.

---

## Passo 4: Healthcheck e `depends_on` com condição

**O que fazer:**

1. No `redis`, adicione um `healthcheck` que roda `redis-cli ping` (com `interval`, `timeout` e `retries`).
2. Na `app`, adicione `depends_on` com `condition: service_healthy`.

💡 **Dica:** `depends_on` sozinho só espera o container **iniciar**. Quem faz esperar ele ficar **pronto** é a
condição `service_healthy`.

📚 [Ordem de inicialização](https://docs.docker.com/compose/how-tos/startup-order/) ·
[`healthcheck`](https://docs.docker.com/reference/compose-file/services/#healthcheck) ·
[`depends_on`](https://docs.docker.com/reference/compose-file/services/#depends_on)

<details><summary>🟢 Dica</summary>
O <code>test</code> do healthcheck pode ser uma lista começando com <code>"CMD"</code>, seguida do comando e dos argumentos.
</details>

<details><summary>🔴 Trecho (só a app)</summary>

```yaml
    depends_on:
      redis:
        condition: service_healthy
```
</details>

✅ **O que ver:** `docker compose ps` mostra o redis como `(healthy)`, e a app só sobe depois disso.

### 🔨 Quebre de propósito

O Redis sobe muito rápido, então a corrida pode não aparecer sozinha. Force a situação:

1. **Atraso no Redis:** adicione temporariamente `command: sh -c "sleep 5 && redis-server"` no `redis`.
   - Com `depends_on` **simples** (`- redis`), a app tenta conectar cedo demais e você deve ver `ConnectionError`.
   - Com `condition: service_healthy`, a app espera e imprime `PONG`.
2. **Healthcheck errado:** troque o teste por um comando que **sai com código diferente de 0**, por exemplo
   `["CMD", "redis-cli", "-p", "1", "ping"]` (porta errada, conexão recusada).
   Você deve ver o redis ficar `unhealthy` e a app **não subir**, com `dependency failed to start: container ... is unhealthy`.
   O tempo até falhar é aproximadamente `interval × retries`.

   ⚠️ **Pegadinha:** `redis-cli pingg` (comando inexistente) **não** serve. O `redis-cli` imprime
   `ERR unknown command`, mas sai com código 0. O Docker só olha o código de saída do teste, então considera saudável.

Desfaça as quebras antes de seguir.

---

## Passo 5: Volume (o dado sobrevive?)

**O que fazer:**

1. No `redis`, monte um volume nomeado em `/data` (a pasta onde a imagem oficial guarda os dados).
2. Declare esse volume na seção `volumes:` do topo do arquivo.
3. Ative a persistência AOF passando `--appendonly yes` para o `redis-server` via `command`.

💡 **Dica:** sem volume, os dados vivem dentro do container. `docker compose down` remove o container e leva os dados junto.

📚 [Volumes no Compose](https://docs.docker.com/reference/compose-file/volumes/) ·
[Persistência no Redis](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/) ·
[Imagem do Redis (seção sobre persistência)](https://hub.docker.com/_/redis)

<details><summary>🟢 Dica</summary>
A sintaxe curta de volume é <code>nome_do_volume:/caminho/no/container</code>.
</details>

**Prova:**

```
docker compose up -d
docker compose exec redis redis-cli SET teste "sobrevivi"
docker compose down
docker compose up -d
docker compose exec redis redis-cli GET teste
```

✅ **O que ver:** `"sobrevivi"`. Para comparar, rode `docker compose down -v`, depois `up -d` e o `GET` de novo. Agora você deve ver `(nil)`.

⚠️ **Pegadinhas:**
- **Sem terminal (tty)**, por exemplo num script, o `redis-cli` imprime uma **linha vazia** para nil. O texto `(nil)` só aparece num terminal interativo ou com `--no-raw`. Para não haver dúvida, use `EXISTS teste`, que devolve 0 ou 1.
- **Git Bash no Windows** converte caminhos como `/data` para `C:/Program Files/Git/data`. Use `MSYS_NO_PATHCONV=1 docker compose exec redis ls /data` ou `docker compose exec redis sh -c "ls /data"`.

🧪 **Desafio:** remova o volume nomeado e repita a prova. A imagem oficial declara `VOLUME /data`, então o Docker cria um volume **anônimo** (nome de hash). Cada `up` depois de um `down` cria um container novo com **outro** volume anônimo, e o dado fica órfão no volume antigo. Confira com `docker inspect` e `docker volume ls`.

---

## Passo 6: Comandos para inspecionar e limpar

| Comando | Para quê |
|---|---|
| `docker compose ps -a` | lista os serviços, o status, o health e o código de saída |
| `docker compose logs app` | logs de um serviço (`-f` acompanha ao vivo) |
| `docker compose exec redis sh` | abre um shell dentro de um container que está rodando |
| `docker compose exec redis redis-cli` | abre o cliente do Redis direto |
| `docker volume ls` | mostra os volumes (procure o seu) |
| `docker compose down` | para e remove os containers e a rede (o volume fica) |
| `docker compose down -v` | faz o mesmo e **apaga os volumes** (cuidado: os dados vão junto) |

📚 [Referência da CLI do `docker compose`](https://docs.docker.com/reference/cli/docker/compose/)

💡 **Dica:** `exec` só funciona com container **rodando**. Como a `app` termina logo, use `docker compose run --rm app` para executá-la de novo.

⚠️ **Cuidado:** `docker volume prune` e `docker system prune` afetam a **máquina inteira**, inclusive volumes de outros projetos. Para limpar só este projeto, use `docker compose down -v`. Volumes anônimos órfãos, como os do desafio do passo 5, **não** são removidos pelo `down -v`, porque já não estão ligados a nenhum container do projeto. Remova um a um com `docker volume rm <hash>`, depois de confirmar com `docker volume inspect`.

✅ **O que ver:** você consegue responder sem chutar onde está cada coisa: container, rede e volume.

---
