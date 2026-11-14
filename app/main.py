from flask import Flask, render_template, request

import storage

app = Flask(__name__)


def pagina(status=200, **contexto):
    return render_template("index.html", **contexto), status


@app.get("/")
def formulario():
    return pagina()


@app.post("/")
def salvar():
    chave = request.form.get("chave", "")
    valor = request.form.get("valor", "")

    if not chave.strip() or not valor.strip():
        return pagina(400, erro="Preencha a chave e o valor.", chave=chave, valor=valor)

    try:
        storage.salvar(chave, valor)
    except ValueError:
        return pagina(400, erro="Chave ou valor inválido.", chave=chave, valor=valor)
    except ConnectionError:
        app.logger.exception("Redis indisponível")
        return pagina(503, erro="Não foi possível salvar, tente novamente", chave=chave, valor=valor)

    return pagina(sucesso=f"Salvo com sucesso: {chave}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
