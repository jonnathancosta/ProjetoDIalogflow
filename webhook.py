from flask import Flask, request, jsonify
import logging
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
import random
import datetime
from datetime import timedelta
from email.message import EmailMessage
import smtplib


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url)

def format_cpf(cpf):
    return ''.join(filter(str.isdigit, cpf))

def valida_cpf(cpf):
    """Verifica se o CPF tem 11 dígitos."""
    return len(cpf) == 11

def format_response_for_dialogflow(texts="", session_info=None):
    """Formata a resposta no formato esperado pelo Dialogflow."""
    return {
        "fulfillment_response": {
            "messages": [{"text": {"text": [texts]}}]
        },
        "session_info": session_info or {}
    }

def generate_auth_code():
    auth_code = random.randint(100000, 999999)
    timestamp_now = datetime.datetime.now()
    valid_until = timestamp_now + timedelta(minutes=3)
   
    return {
        "auth_code": str(auth_code),
        "valid_until": valid_until.strftime('%Y-%m-%d %H:%M:%S')
    }
    
def validar_token(session_params):
    
    """Função para validar o código digitado pelo usuário."""
    token_info= session_params.get("token_info", "")
    token_cliente = session_params.get("token_cliente", '')
    token_enviado = token_info["auth_code"]
    
    if  not token_info["auth_code"]:
        return jsonify(format_response_for_dialogflow(
            "Erro:Código não fornecido.",
            {"parameters": {"status_retorno": "erro", "msg_erro": "Dados ausentes"}}
        ))

    # Verifica se o e-mail está registrado no dicionário de código
    valid_until = datetime.datetime.strptime(token_info["valid_until"], '%Y-%m-%d %H:%M:%S')
    current_time = datetime.datetime.now()

    # Verifica se o código expirou
    if current_time > valid_until:
        
        session = {
            "parameters": {
                "token_info": None, 
                "token_cliente":None,
                "token": "Expirado"
            }
        }
        return jsonify(format_response_for_dialogflow(session_info=session))

    # Verifica se o código digitado está correto
    if token_cliente == token_enviado:
        
        
        
        session = {
            "parameters": {
                "token": True,
                "token_cliente": None
            }
        }
        
        return jsonify(format_response_for_dialogflow(session_info=session
        ))
    else:
        return jsonify(format_response_for_dialogflow(
            "Código incorreto. Tente novamente.",
            {"parameters": {"token_cliente": None,"token": False}}))
        
def send_email(to_email, auth_code):
    
    email = os.getenv('email')
    senha = os.getenv('senha')
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = email
    sender_password = senha  # Use uma senha de aplicativo do Google

    subject = "Seu código de autenticação"
    body = f"Olá,\n\nSeu código de autenticação é: {auth_code}.\nEle é válido por 3 minutos.\n\nAtenciosamente,\nCCAI Platform"

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("E-mail enviado com sucesso!")
            return "E-mail enviado com sucesso!"
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")  # Agora exibe o erro
        return f"Erro ao enviar e-mail: {e}"
    
    logging.info(f"Enviando e-mail para {email} com o código {auth_code}")
    
def reset_webhook(session_params):
    
    session_params.get('cpf_cliente', "")
    
    session_info = {
            "parameters": {
                "status_retorno": "CPF resetado", 
                "validar_cpf": None, 
                "cpf_cliente": None
            }
        }
    return (format_response_for_dialogflow("Por favor, digite o CPf novamente", session_info))

def reset_email(session_params):

    session_params.get('email_cliente', '')

    session = {
            "parameters": {
                "status_retorno": " Email resetado",
                "usuario_cadastrado": None,
                "email_cliente": None
            }
        }
    return (format_response_for_dialogflow(session_info = session))

def trocar_email(session_params):
    cpf = session_params.get('cpf_cliente', '')
    email = session_params.get('email_cliente', '')
    nome = session_params.get('nome_cliente', '')

    try:
        with engine.connect() as connection:
            query = text("SELECT nome, email FROM clientes WHERE cpf = :cpf")
            result = connection.execute(query, {"cpf": cpf})
            cliente = result.mappings().first()  # Retorna o primeiro resultado como dicionário

        if cliente:
            try:
                with engine.connect() as connection:
                    query = text("UPDATE clientes SET email = :email WHERE cpf = :cpf")
                    connection.execute(query, {"cpf": cpf, "email": email})
                    connection.commit()

                session = {
                    "parameters": {
                        "nome_cliente": nome,
                        "cpf_cliente": cpf,
                        "email_cliente": email
                    }
                }

                return jsonify(format_response_for_dialogflow(session_info=session))

            except Exception as e:
                return jsonify({"fulfillmentText": f"Erro ao atualizar o e-mail: {str(e)}"})

        else:
            return jsonify({"fulfillmentText": "CPF não encontrado. Não foi possível atualizar o e-mail."})

    except Exception as e:
        return jsonify({"fulfillmentText": f"Erro ao buscar cliente: {str(e)}"})
    
def consultar_cpf(session_params):
    
    cpf = format_cpf(session_params.get('cpf_cliente', ''))

    if not valida_cpf(cpf):
        retorno =jsonify(format_response_for_dialogflow(
            "CPF inválido! Deseja tentar novamente?",
            {"parameters": {"status_retorno": "Invalido", "msg_erro": "deu ruim", "cpf_cliente": None}}
        ))
        return(retorno)
    
    try:
        with engine.connect() as connection:
            query = text("SELECT nome, email FROM clientes WHERE cpf = :cpf")
            result = connection.execute(query, {"cpf": cpf})
            cliente = result.mappings().first()  # Retorna o primeiro resultado como dicionário

        if cliente:
            # Cliente encontrado no banco
            session = {
                "parameters": {
                    "cpf_cliente": cpf,
                    "usuario_cadastrado": True,
                    "email_cliente": cliente["email"],
                    "nome_cliente": cliente["nome"]
                }
            }
            return jsonify(format_response_for_dialogflow(session_info=session))

        else:
            # Cliente NÃO encontrado no banco
            session = {
                "parameters": {
                    "cpf_cliente": cpf,
                    "usuario_cadastrado": False
                }
            }
            return jsonify(format_response_for_dialogflow(session_info=session))

    except Exception as ex:
        # Em caso de erro na conexão ou na consulta
        return jsonify(format_response_for_dialogflow(
            "Ocorreu um erro ao acessar o banco de dados.",
            {"parameters": {"status_retorno": "erro", "msg_erro": str(ex), "cpf_cliente": cpf}}
        ))

def cadastrar_cliente(session_params):
    """Função para cadastrar um novo cliente."""
    nome = session_params.get('nome_cliente', '')
    cpf = format_cpf(session_params.get('cpf_cliente', ''))
    email = session_params.get('email_cliente', '')

    if not nome or not email:
        return jsonify(format_response_for_dialogflow(
            "Erro: Nome e e-mail são obrigatórios!",
            {"parameters": {"status_retorno": "Erro nos dados"}}
        ))

    if not valida_cpf(cpf):
        return jsonify(format_response_for_dialogflow(
            "CPF inválido! Deseja tentar novamente?",
            {"parameters": {"status_retorno": "CPF inválido", "msg_erro": "deu ruim", "cpf_cliente": None}}
        ))

    try:
        with engine.connect() as connection:
            query = text("INSERT INTO clientes (nome, cpf, email) VALUES (:nome, :cpf, :email)")
            connection.execute(query, {"nome": nome, "cpf": cpf, "email": email})
            connection.commit()

            session_info = {
                "parameters": {
                    "nome_cliente": nome,
                    "cpf_cliente": cpf,
                    "email_cliente": email
                }
            }
            return jsonify(format_response_for_dialogflow(session_info))

    except Exception as e:
        return jsonify({"fulfillmentText": f"Erro ao inserir cliente: {str(e)}"})

def validar_cpf(session_params):
    """Função para validar um CPF e enviar código de autenticação."""
    try:
        cpf = format_cpf(session_params.get('cpf_cliente', ''))

        if not valida_cpf(cpf):
            return jsonify(format_response_for_dialogflow(
                "CPF em formato inválido!",
                {"parameters": {"status_retorno": "invalid"}}
            ))

        try:
            with engine.connect() as connection:
             query = text("SELECT nome, email FROM clientes WHERE cpf = :cpf")
             result = connection.execute(query, {"cpf": cpf})
             cliente = result.mappings().first()
        
            if not cliente:
                retorno = jsonify(format_response_for_dialogflow("CPF não encontrado. Deseja se cadastrar ou tentar novamente? "))
                return(retorno)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
            nome = cliente['nome'] 
            email = cliente['email']
            token = generate_auth_code()
            send_email(email, token['auth_code'])
            
            session = {
                "parameters": {
                    "token_info": token,
                    "email": email,
                    "nome_cliente": nome,
                    "logou": True
                }
            }
            return jsonify(format_response_for_dialogflow(session_info=session))
    
        except Exception as ex:
            print(ex)
        # Em caso de erro na conexão ou na consulta
            return jsonify(format_response_for_dialogflow(
            "Ocorreu um erro ao acessar o banco de dados.",
            {"parameters": {"status_retorno": "erro", "msg_erro": str(ex), "cpf_cliente": cpf}}
            ))  
    except Exception as ex:
        log_erro = str(ex)
        session = {
            "parameters": {"msg_erro": log_erro, "cpf_cliente": None}
        }
        return jsonify(format_response_for_dialogflow("Erro ao validar CPF. Tente novamente.", session_info= session))

def buscar_jogo(session_params):
    
    jogo = session_params.get("jogo", "")
    plataforma = session_params.get("plataforma", "")
    
    if plataforma == "catalogo":
        with engine.connect() as connection:
            query = text("SELECT jogo, plataforma, quantidade, valor FROM jogos")
            result = connection.execute(query)
            resultado = result.mappings().all()
            
        resposta = "🎮 Jogos disponíveis:\n\n"
        for jogo in resultado:
                resposta += (
                    f"📌 Nome: {jogo['jogo']}\n"
                    f"🎮 Plataforma: {jogo['plataforma']}\n"
                    f"📦 Quantidade: {jogo['quantidade']}\n"
                    f"💰 Valor: R$ {jogo['valor']:.2f}\n"
                    "----------------------\n"
                )

        resposta += "Gostaria de comprar algum? 🛒"
        
        session = {
            "parameters": {
                "plataforma": None
            }
        }
        
        return jsonify(format_response_for_dialogflow(resposta, session_info=session))


    try:
        with engine.connect() as connection:
            query = text("SELECT jogo, plataforma, valor FROM jogos WHERE jogo = :jogo AND plataforma = :plataforma")
            result = connection.execute(query, {"jogo": jogo, "plataforma": plataforma})
            resultado = result.mappings().first()

        if not resultado:
            return jsonify(format_response_for_dialogflow(
                "Infelizmente não temos esse jogo disponível. Gostaria de consultar o nosso catalogo ou tentar buscar outro jogo?",
                 {"parameters":{"jogo": None, "plataforma": None}}
            ))

        session = {
            "parameters": {
                "valor": resultado["valor"]
            }
        }

        resposta = f"O jogo {resultado['jogo']} custa: R$ {resultado['valor']} Gostaria de comprar?"
        
        return jsonify(format_response_for_dialogflow(resposta, session_info=session))

    except Exception as ex:
        log_erro = str(ex)
        session = {
            "parameters": {"msg_erro": log_erro, "cpf_cliente": None}
        }
        return jsonify(format_response_for_dialogflow("Erro ao buscar jogo.", session_info=session))
            
def valor_total(session_params):
    jogos = session_params.get("jogo", "")
    plataforma = session_params.get("plataforma", "")
    valor = float(session_params.get("valor", 0))
    quantidade = int(session_params.get("quantidade", 0))
    
    valor_total_item = valor * quantidade

    lista_jogos = session_params.get("lista_jogos", [])

    # Verifica se já existe o mesmo jogo e plataforma na lista
    jogo_existente = next(
        (item for item in lista_jogos if item["jogos"] == jogos and item["plataforma"] == plataforma),
        None
    )

    if jogo_existente:
        # Atualiza quantidade e valor total
        jogo_existente["quantidade"] += quantidade
        jogo_existente["valor_total"] = jogo_existente["valor"] * jogo_existente["quantidade"]
    else:
        # Adiciona novo jogo
        lista_jogos.append({
            "jogos": jogos,
            "plataforma": plataforma,
            "quantidade": quantidade,
            "valor": valor,
            "valor_total": valor_total_item
        })

    total_compra = sum(item["valor_total"] for item in lista_jogos)

    # Monta a resposta para o usuário
    text = ""
    for item in lista_jogos:
        text += (
            f"🕹 Jogo: {item['jogos']} \n"
            f"💻 Plataforma: {item['plataforma']} \n"
            f"📦 Quantidade: {item['quantidade']} \n"
            f"💰 Valor: {item['valor']:.2f} \n"
        )
    
    text += f"💳 Valor total: {total_compra:.2f} \n Quer adicionar mais alguma coisa? 😃🔥"

    session = {
        "parameters": {
            "valor_total": valor_total_item,
            "lista_jogos": lista_jogos,
            "total_compra": total_compra
        }
    }
    
    return jsonify(format_response_for_dialogflow(text, session_info=session))
          
            
@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook principal que recebe as requisições do Dialogflow."""
    data = request.get_json(silent=True)

    if not data or 'fulfillmentInfo' not in data:
        return jsonify({"error": "Requisição inválida"}), 400

    tag = data['fulfillmentInfo'].get('tag')
    session_params = data.get('sessionInfo', {}).get('parameters', {})

    if tag == "cadastrar_cliente":
        return cadastrar_cliente(session_params)
    
    if tag == "reset_email":
        return reset_email(session_params)
    
    if tag == "trocar_email":
        return trocar_email(session_params)
    
    if tag == "consultar_cpf":
        return consultar_cpf(session_params)
    
    if tag == "reset_webhook":
       return reset_webhook(session_params)
    
    if tag == "validar_cpf":
        return validar_cpf(session_params)
    
    if tag == "validar_token":
        return validar_token(session_params)
    
    if tag == "buscar_jogo":
        return buscar_jogo(session_params)
    
    if tag == "valor_total":
        return valor_total(session_params)

    return jsonify({"error": "Tag inválida"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8080)
