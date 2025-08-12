
### Documentação: Webhook do Bot de Vendas de Jogos

Este projeto. desenvolvido em janeido de 2025, é um webhook em **Flask** projetado para interagir com o **Dialogflow CX**. Ele simula um assistente virtual para uma loja de jogos, permitindo aos usuários consultar, cadastrar, autenticar e realizar compras de jogos. O objetivo principal foi explorar a dinâmica e a arquitetura de interação entre um webhook de back-end e um agente do Dialogflow CX.

-----

### Estrutura e Funcionalidades do Back-end (Flask)

O servidor Flask atua como o cérebro da lógica de negócio. Ele recebe requisições do Dialogflow e executa as ações necessárias, como acessar o banco de dados ou enviar e-mails.

#### Tecnologias Utilizadas

  * **Flask**: Framework web para criar a API que atende às requisições do Dialogflow.
  * **SQLAlchemy**: ORM (Object-Relational Mapper) que facilita a conexão e a manipulação de um banco de dados MySQL.
  * **python-dotenv**: Carrega variáveis de ambiente de um arquivo `.env` para gerenciar credenciais de forma segura.
  * **smtplib**: Biblioteca padrão do Python para enviar e-mails de autenticação.

#### Funções Principais

As funções abaixo são acionadas pela rota `/webhook` com base na `tag` enviada pelo Dialogflow.

  * `consultar_cpf(session_params)`: Valida e busca um cliente no banco de dados pelo CPF. Retorna os dados do cliente, se encontrado.
  * `cadastrar_cliente(session_params)`: Insere um novo cliente na tabela `clientes`. Requer nome, CPF e e-mail.
  * `validar_cpf(session_params)`: Encontra o cliente pelo CPF, gera um código de autenticação único e o envia para o e-mail cadastrado.
  * `validar_token(session_params)`: Verifica se o código de autenticação fornecido pelo usuário corresponde ao que foi enviado. Também valida o tempo de expiração do código (3 minutos).
  * `trocar_email(session_params)`: Atualiza o e-mail de um cliente existente no banco de dados.
  * `buscar_jogo(session_params)`: Pesquisa jogos específicos ou retorna o catálogo completo, se solicitado.
  * `valor_total(session_params)`: Calcula o subtotal e o valor total de uma lista de jogos que o cliente deseja comprar, salvando o carrinho na sessão do Dialogflow.
  * `format_response_for_dialogflow()`: Função utilitária para formatar as respostas no padrão JSON exigido pelo Dialogflow.

-----

### Configuração de Ambiente

Para rodar o projeto, é necessário um arquivo `.env` na raiz do projeto com as seguintes variáveis de ambiente:

```
# String de conexão com o banco de dados MySQL
DATABASE_URL="mysql+pymysql://<usuario>:<senha>@<host>/<database>"

# Credenciais de e-mail para envio dos tokens
email="<seu_email_remetente>"
senha="<sua_senha_de_app>"
```

**Importante**: A `senha` deve ser uma **senha de aplicativo** gerada na sua conta de e-mail (por exemplo, no Google).

-----

### Estrutura de Integração Front-end

A interface do chatbot é implementada em uma página web usando o widget **`df-messenger`** do Google, que se conecta diretamente ao agente do Dialogflow.

#### Código HTML de Exemplo

O código a seguir deve ser adicionado ao corpo de uma página web para exibir o widget do chatbot.

```html
<link rel="stylesheet" href="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/themes/df-messenger-default.css">
<script src="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js"></script>
<df-messenger
  project-id="NOME_DO_PROJETO"
  agent-id="NOME_DO_AGENTE"
  language-code="pt-br"
  max-query-length="-1">
  <df-messenger-chat-bubble
    chat-title="Mario">
  </df-messenger-chat-bubble>
</df-messenger>
<style>
  df-messenger {
    z-index: 999;
    position: fixed;
    --df-messenger-font-color: #000;
    --df-messenger-font-family: Google Sans;
    --df-messenger-chat-background: #4d5564;
    --df-messenger-message-user-background: #0eb2e954;
    --df-messenger-message-bot-background: #a71111;
    bottom: 16px;
    right: 16px;
  }
</style>
```

Para usar este código, substitua `NOME_DO_PROJETO` e `NOME_DO_AGENTE` pelos IDs correspondentes do seu agente no Dialogflow. As tags `<style>` podem ser modificadas para personalizar a aparência do widget.