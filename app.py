# app.py — versão completa com login obrigatório

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
from datetime import date
from functools import wraps
import database as db

app = Flask(__name__)
app.secret_key = "biblioteca-escolar-2026"

db.init_db()

# ════════════════════════════════════════
#  USUÁRIOS DO SISTEMA
# ════════════════════════════════════════

USUARIOS = {
    "admin":         "admin123",
    "bibliotecario": "biblio2026",
    "professor":     "prof2026",
}

# ════════════════════════════════════════
#  DECORATOR — PROTEGE AS ROTAS
# ════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario" not in session:
            flash("Faça login para acessar o sistema.", "atencao")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ════════════════════════════════════════
#  LOGIN / LOGOUT
# ════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha   = request.form.get("senha", "").strip()
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            session["usuario"] = usuario
            flash(f"Bem-vindo, {usuario}!", "sucesso")
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha incorretos.", "erro")
    return render_template("login.html")


@app.route("/logout")
def logout():
    usuario = session.pop("usuario", None)
    flash(f"Até logo, {usuario}!", "atencao")
    return redirect(url_for("login"))

# ════════════════════════════════════════
#  INÍCIO — protegida
# ════════════════════════════════════════

@app.route("/")
@login_required
def index():
    stats = db.obter_stats()
    return render_template("index.html", stats=stats)

# ════════════════════════════════════════
#  LIVROS — protegidas
# ════════════════════════════════════════

@app.route("/livros")
@login_required
def livros():
    busca = request.args.get("busca", "").lower()
    lista = db.listar_livros()
    if busca:
        lista = [
            l for l in lista
            if busca in l["titulo"].lower()
            or busca in l["autor"].lower()
        ]
    return render_template("livros.html", livros=lista, busca=busca)


@app.route("/livros/novo", methods=["POST"])
@login_required
def livros_novo():
    titulo     = request.form.get("titulo", "").strip()
    autor      = request.form.get("autor", "").strip()
    isbn       = request.form.get("isbn", "").strip()
    quantidade = int(request.form.get("quantidade", 1))
    if not titulo or not autor:
        flash("Preencha os campos obrigatórios.", "erro")
        return redirect(url_for("livros"))
    db.inserir_livro(titulo, autor, isbn, quantidade)
    flash("Livro cadastrado com sucesso!", "sucesso")
    return redirect(url_for("livros"))


@app.route("/livros/editar/<int:id_>", methods=["POST"])
@login_required
def livros_editar(id_):
    titulo     = request.form.get("titulo", "").strip()
    autor      = request.form.get("autor", "").strip()
    isbn       = request.form.get("isbn", "").strip()
    quantidade = int(request.form.get("quantidade", 1))
    if not titulo or not autor:
        flash("Preencha os campos obrigatórios.", "erro")
        return redirect(url_for("livros"))
    db.atualizar_livro(id_, titulo, autor, isbn, quantidade)
    flash("Livro atualizado com sucesso!", "sucesso")
    return redirect(url_for("livros"))


@app.route("/livros/deletar/<int:id_>")
@login_required
def livros_deletar(id_):
    db.deletar_livro(id_)
    flash("Livro excluído.", "atencao")
    return redirect(url_for("livros"))

# ════════════════════════════════════════
#  ALUNOS — protegidas
# ════════════════════════════════════════

@app.route("/alunos")
@login_required
def alunos():
    busca = request.args.get("busca", "").lower()
    lista = db.listar_alunos()
    if busca:
        lista = [
            a for a in lista
            if busca in a["nome"].lower()
            or busca in a["matricula"].lower()
            or busca in a["turma"].lower()
        ]
    return render_template("alunos.html", alunos=lista, busca=busca)


@app.route("/alunos/novo", methods=["POST"])
@login_required
def alunos_novo():
    nome      = request.form.get("nome", "").strip()
    matricula = request.form.get("matricula", "").strip()
    turma     = request.form.get("turma", "").strip()
    telefone  = request.form.get("telefone", "").strip()
    if not nome or not matricula or not turma:
        flash("Preencha os campos obrigatórios.", "erro")
        return redirect(url_for("alunos"))
    try:
        db.inserir_aluno(nome, matricula, turma, telefone)
        flash("Aluno cadastrado com sucesso!", "sucesso")
    except ValueError as e:
        flash(str(e), "erro")
    return redirect(url_for("alunos"))


@app.route("/alunos/editar/<int:id_>", methods=["POST"])
@login_required
def alunos_editar(id_):
    nome      = request.form.get("nome", "").strip()
    matricula = request.form.get("matricula", "").strip()
    turma     = request.form.get("turma", "").strip()
    telefone  = request.form.get("telefone", "").strip()
    if not nome or not matricula or not turma:
        flash("Preencha os campos obrigatórios.", "erro")
        return redirect(url_for("alunos"))
    try:
        db.atualizar_aluno(id_, nome, matricula, turma, telefone)
        flash("Aluno atualizado com sucesso!", "sucesso")
    except ValueError as e:
        flash(str(e), "erro")
    return redirect(url_for("alunos"))


@app.route("/alunos/deletar/<int:id_>")
@login_required
def alunos_deletar(id_):
    db.deletar_aluno(id_)
    flash("Aluno excluído.", "atencao")
    return redirect(url_for("alunos"))

# ════════════════════════════════════════
#  EMPRÉSTIMOS — protegidas
# ════════════════════════════════════════

@app.route("/emprestimos")
@login_required
def emprestimos():
    busca = request.args.get("busca", "").lower()
    lista = db.listar_emprestimos()
    if busca:
        lista = [
            e for e in lista
            if busca in e["titulo_livro"].lower()
            or busca in e["nome_aluno"].lower()
        ]
    todos_livros       = db.listar_livros()
    livros_disponiveis = [l for l in todos_livros if l["disponivel"] > 0]
    todos_alunos       = db.listar_alunos()
    return render_template(
        "emprestimos.html",
        emprestimos=lista,
        livros=livros_disponiveis,
        alunos=todos_alunos,
        busca=busca
    )


@app.route("/emprestimos/novo", methods=["POST"])
@login_required
def emprestimos_novo():
    livro_id = int(request.form.get("livro_id"))
    aluno_id = int(request.form.get("aluno_id"))
    hoje = date.today().strftime("%d/%m/%Y")
    try:
        db.inserir_emprestimo(livro_id, aluno_id, hoje)
        flash("Empréstimo registrado com sucesso!", "sucesso")
    except ValueError as e:
        flash(str(e), "erro")
    return redirect(url_for("emprestimos"))


@app.route("/emprestimos/devolver/<int:id_>")
@login_required
def emprestimos_devolver(id_):
    hoje = date.today().strftime("%d/%m/%Y")
    db.registrar_devolucao(id_, hoje)
    flash("Devolução registrada com sucesso!", "sucesso")
    return redirect(url_for("emprestimos"))

# ════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True)