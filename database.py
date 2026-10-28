# database.py
# Responsável por toda a comunicação com o banco de dados SQLite
# Cria as tabelas e fornece funções de CRUD para livros, alunos e empréstimos

import sqlite3
from contextlib import closing

# Nome do arquivo do banco de dados
DB_NAME = "biblioteca.db"


def get_connection():
    """
    Abre e retorna uma conexão com o banco de dados.
    row_factory permite acessar colunas pelo nome (ex: row["titulo"])
    em vez de pelo índice (ex: row[0]).
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Cria as tabelas do banco caso ainda não existam.
    Chamada uma vez ao iniciar o servidor Flask.
    """
    with closing(get_connection()) as conn:
        cursor = conn.cursor()

        # Tabela de Livros
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS livros (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo     TEXT    NOT NULL,
                autor      TEXT    NOT NULL,
                isbn       TEXT,
                quantidade INTEGER NOT NULL DEFAULT 1,
                disponivel INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Tabela de Alunos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT NOT NULL,
                matricula TEXT NOT NULL UNIQUE,
                turma     TEXT NOT NULL,
                telefone  TEXT
            )
        """)

        # Tabela de Empréstimos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                livro_id        INTEGER NOT NULL,
                aluno_id        INTEGER NOT NULL,
                data_emprestimo TEXT    NOT NULL,
                data_devolucao  TEXT,
                devolvido       INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (livro_id) REFERENCES livros(id),
                FOREIGN KEY (aluno_id) REFERENCES alunos(id)
            )
        """)

        conn.commit()


# ════════════════════════════════════════
#  FUNÇÕES — LIVROS
# ════════════════════════════════════════

def listar_livros():
    """Retorna todos os livros ordenados pelo título."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM livros ORDER BY titulo ASC")
        return cur.fetchall()


def obter_livro(id_):
    """Retorna um livro específico pelo ID."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM livros WHERE id = ?", (id_,))
        return cur.fetchone()


def inserir_livro(titulo, autor, isbn, quantidade):
    """
    Insere um novo livro.
    disponivel começa igual à quantidade total.
    """
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO livros (titulo, autor, isbn, quantidade, disponivel)
            VALUES (?, ?, ?, ?, ?)
        """, (titulo, autor, isbn, quantidade, quantidade))
        conn.commit()


def atualizar_livro(id_, titulo, autor, isbn, quantidade):
    """
    Atualiza os dados de um livro.
    Recalcula a disponibilidade com base na diferença de quantidade.
    """
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT quantidade, disponivel FROM livros WHERE id = ?", (id_,)
        )
        row = cur.fetchone()
        if not row:
            return

        diff = quantidade - row["quantidade"]
        nova_disp = max(0, row["disponivel"] + diff)

        cur.execute("""
            UPDATE livros
            SET titulo = ?, autor = ?, isbn = ?, quantidade = ?, disponivel = ?
            WHERE id = ?
        """, (titulo, autor, isbn, quantidade, nova_disp, id_))
        conn.commit()


def deletar_livro(id_):
    """Remove um livro pelo ID."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM livros WHERE id = ?", (id_,))
        conn.commit()


# ════════════════════════════════════════
#  FUNÇÕES — ALUNOS
# ════════════════════════════════════════

def listar_alunos():
    """Retorna todos os alunos ordenados pelo nome."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM alunos ORDER BY nome ASC")
        return cur.fetchall()


def obter_aluno(id_):
    """Retorna um aluno específico pelo ID."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM alunos WHERE id = ?", (id_,))
        return cur.fetchone()


def inserir_aluno(nome, matricula, turma, telefone):
    """
    Insere um novo aluno.
    Lança exceção se a matrícula já existir (UNIQUE).
    """
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO alunos (nome, matricula, turma, telefone)
                VALUES (?, ?, ?, ?)
            """, (nome, matricula, turma, telefone))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Matrícula já cadastrada para outro aluno.")


def atualizar_aluno(id_, nome, matricula, turma, telefone):
    """Atualiza os dados de um aluno."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE alunos
                SET nome = ?, matricula = ?, turma = ?, telefone = ?
                WHERE id = ?
            """, (nome, matricula, turma, telefone, id_))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Matrícula já cadastrada para outro aluno.")


def deletar_aluno(id_):
    """Remove um aluno pelo ID."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM alunos WHERE id = ?", (id_,))
        conn.commit()


# ════════════════════════════════════════
#  FUNÇÕES — EMPRÉSTIMOS
# ════════════════════════════════════════

def listar_emprestimos():
    """
    Retorna todos os empréstimos usando JOIN para trazer
    o título do livro e o nome do aluno juntos.
    """
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                e.*,
                l.titulo  AS titulo_livro,
                a.nome    AS nome_aluno,
                a.turma   AS turma_aluno
            FROM emprestimos e
            JOIN livros l ON e.livro_id = l.id
            JOIN alunos a ON e.aluno_id = a.id
            ORDER BY e.data_emprestimo DESC
        """)
        return cur.fetchall()


def inserir_emprestimo(livro_id, aluno_id, data_emprestimo):
    """
    Registra um empréstimo e reduz a disponibilidade do livro.
    Lança exceção se o livro não estiver disponível.
    """
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT disponivel FROM livros WHERE id = ?", (livro_id,)
        )
        row = cur.fetchone()
        if not row or row["disponivel"] <= 0:
            raise ValueError("Livro não disponível para empréstimo.")

        cur.execute(
            "UPDATE livros SET disponivel = disponivel - 1 WHERE id = ?",
            (livro_id,)
        )
        cur.execute("""
            INSERT INTO emprestimos (livro_id, aluno_id, data_emprestimo, devolvido)
            VALUES (?, ?, ?, 0)
        """, (livro_id, aluno_id, data_emprestimo))
        conn.commit()


def registrar_devolucao(emprestimo_id, data_devolucao):
    """
    Marca o empréstimo como devolvido e
    devolve +1 na disponibilidade do livro.
    """
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT livro_id FROM emprestimos WHERE id = ?", (emprestimo_id,)
        )
        row = cur.fetchone()
        if not row:
            return

        cur.execute("""
            UPDATE emprestimos
            SET devolvido = 1, data_devolucao = ?
            WHERE id = ?
        """, (data_devolucao, emprestimo_id))
        cur.execute(
            "UPDATE livros SET disponivel = disponivel + 1 WHERE id = ?",
            (row["livro_id"],)
        )
        conn.commit()


# ════════════════════════════════════════
#  ESTATÍSTICAS
# ════════════════════════════════════════

def obter_stats():
    """Retorna contagens para exibir na tela inicial."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM livros")
        total_livros = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM alunos")
        total_alunos = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM emprestimos WHERE devolvido = 0")
        abertos = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM emprestimos WHERE devolvido = 1")
        devolvidos = cur.fetchone()["total"]

        return {
            "total_livros": total_livros,
            "total_alunos": total_alunos,
            "abertos": abertos,
            "devolvidos": devolvidos,
        }