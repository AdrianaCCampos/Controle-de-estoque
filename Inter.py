# Bibliotecas importadas

from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json


# Aplicação do flask e chave secreta para gerenciar as sessões
app = Flask(__name__)
app.secret_key = 'your_secret_key'

#importando dados sensiveis do banco de dados
config_path = r'C:\Users\Adriana\Documents\FECAF\Protecao\config.json'

with open(config_path) as config_file:
    config = json.load(config_file)


# Configuração e conexao com o banco
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = \
    '{SGBD}://{usuario}:{senha}@{servidor}/{database}'.format(
        SGBD='mysql+mysqlconnector',
        usuario=config['DB_USER'],
        senha=config['DB_PASSWORD'],
        servidor=config['DB_HOST'],
        database=config['DB_NAME']
    )

# a interação com o banco de dados
db = SQLAlchemy(app)

# Modelagem de dados, com a tabela produtos
class Produtos(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.Date, nullable=False)
    produto = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=True)
    quantidade = db.Column(db.Integer, nullable=False)
    quantidade_minima = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Produto {self.produto}>"

# Modelagem de dados, com a tabela usuarios
class Usuarios(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(200), nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Usuario {self.nome}>"

# Função para atualizar as senhas existentes no banco de dados
def atualizar_senhas():
    with app.app_context():
        usuarios = Usuarios.query.all()
        for usuario in usuarios:
            usuario.senha = generate_password_hash(usuario.senha)
            db.session.add(usuario)
        db.session.commit()
        print("Senhas atualizadas com sucesso!")

# Página inicial
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return redirect('/')
    return render_template('log.html')

# Tela de login
@app.route('/login', methods=['POST'])
def login():
    nome = request.form.get('nome')
    senha = request.form.get('senha')

    print(f"Tentativa de login: nome={nome}, senha={senha}")

    usuario = Usuarios.query.filter_by(nome=nome).first()

    if usuario:
        print(f"Usuário encontrado: {usuario}")
        print(f"Hash da senha armazenado: {usuario.senha}")
        if check_password_hash(usuario.senha, senha):
            print("Senha correta")
            session['perfil'] = usuario.perfil
            return redirect('/usuarios')
        else:
            print("Senha incorreta")
            flash('Usuário ou senha inválida!')
            return redirect(url_for('home'))
    else:
        print("Usuário não encontrado")
        flash('Usuário ou senha inválida!')
        return redirect(url_for('home'))

# Tela de acessos
@app.route('/usuarios')
def usuarios():
    produtos_abaixo_minimo = Produtos.query.filter(Produtos.quantidade < Produtos.quantidade_minima).all()
    return render_template('usuarios.html', produtos_abaixo_minimo=produtos_abaixo_minimo)

# Tela de cadastro de estoque
@app.route('/estoque', methods=['GET', 'POST'])
def estoque():
    if request.method == 'POST':
        data = request.form.get('data')
        produto = request.form.get('produto')
        tipo = request.form.get('tipo')
        valor = request.form.get('valor')
        quantidade = request.form.get('quantidade')
        quantidade_minima = request.form.get('minima')

        # Inserindo produtos no banco de dados
        novo_produto = Produtos(data=data, produto=produto, tipo=tipo,
                                valor=valor, quantidade=quantidade, quantidade_minima=quantidade_minima)
        db.session.add(novo_produto)
        db.session.commit()

        flash("Dados inseridos com sucesso!")
        return redirect('/estoque')

    return render_template('estoque.html')

# Tela para visualização de produtos
@app.route('/estoqueatual')
def estoque_atual():
    atual = Produtos.query.order_by(Produtos.data)
    return render_template('estoqueatual.html', titulo="Estoque Atual", todos_produtos=atual)

# Tela de cadastro de usuários
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    # Verifica se o usuário é administrador
    if 'perfil' not in session or session['perfil'] != 'administrador':
        flash("Acesso negado! Apenas administradores podem cadastrar novos usuários.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        perfil = request.form.get('perfil')

        if not nome or not senha or not perfil:
            flash("Todos os campos são obrigatórios!")
            return redirect(url_for('cadastro'))

        # Gerar a criptografia da senha antes de salvar
        senha_hash = generate_password_hash(senha)
        print(f"Senha original: {senha}, Hash gerado: {senha_hash}")

        # Inserindo novo usuário no banco de dados
        novo_usuario = Usuarios(nome=nome, senha=senha_hash, perfil=perfil)

        db.session.add(novo_usuario)
        db.session.commit()

        flash("Novo usuário cadastrado com sucesso!")
        return redirect('/usuarios')

    return render_template('cadastro.html')

@app.route('/usuarioatual', methods=['GET'])
def usuarios_atual():
    if 'perfil' not in session or session['perfil'] != 'administrador':
        flash("Acesso negado! Apenas administradores podem acessar!")
        return redirect(url_for('home'))

    users = Usuarios.query.order_by(Usuarios.id)
    return render_template('usuarioatual.html', titulo="Relação de Usuários", todos_usuarios=users)

# Executa a aplicação
if __name__ == "__main__":
    app.run(debug=True)
