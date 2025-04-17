import telebot
import random
import requests

# Substitua pelo token do seu bot do Telegram
TOKEN = "7751026582:AAFdXUMrw6tI1SVYu6K0BQZRXt6Rtvqwre0"
bot = telebot.TeleBot(TOKEN)

# Dicionário para armazenar o estado de cada usuário
user_states = {}

# Função para gerar o número do cartão a partir de uma BIN
def generate_card_number(bin_input):
    card_number = bin_input
    while len(card_number) < 15:
        card_number += str(random.randint(0, 9))

    digits = [int(x) for x in card_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = sum(digits) * 9 % 10
    card_number += str(checksum)

    return card_number

# Função para gerar data de validade
def generate_expiry_date(month=None, year=None):
    if month is None:
        month = random.randint(1, 12)
    if year is None:
        year = random.randint(2024, 2029)
    return f"{month:02}/{year:02}"

# Função para gerar CVV
def generate_cvv(cvv=None):
    return cvv if cvv else str(random.randint(100, 999))

# Função para buscar informações da BIN
def fetch_bin_info(bin_input):
    url = f"https://lookup.binlist.net/{bin_input}"
    headers = {"Accept-Version": "3"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

# Responde ao comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bem-vindo! Use o comando /gen para gerar números de cartão de crédito.")

# Responde ao comando /gen
@bot.message_handler(commands=['gen'])
def start_generation(message):
    chat_id = message.chat.id
    user_states[chat_id] = {"step": 1}  # Define o primeiro passo
    bot.reply_to(message, "Primeiro, envie a BIN ou matriz para gerar o cartão.")

# Recebe mensagens e executa as etapas do fluxo
@bot.message_handler(func=lambda msg: msg.chat.id in user_states)
def handle_steps(message):
    chat_id = message.chat.id
    state = user_states[chat_id]

    # Etapa 1: Recebe a BIN/matriz
    if state["step"] == 1:
        bin_input = message.text.strip()
        if not bin_input.isdigit() or len(bin_input) < 6:
            bot.reply_to(message, "Por favor, envie uma BIN válida com pelo menos 6 dígitos.")
            return

        state["bin"] = bin_input
        state["step"] = 2
        bot.reply_to(message, (
            "Agora, escolha a data de validade:\n"
            "1️⃣ Digite uma data no formato MM/AAAA\n"
            "2️⃣ Ou envie a palavra *aleatório* para gerar automaticamente."
        ))

    # Etapa 2: Recebe a data de validade
    elif state["step"] == 2:
        expiry_date = message.text.strip()
        if expiry_date.lower() == "aleatório":
            state["expiry_date"] = generate_expiry_date()
            state["step"] = 3
            bot.reply_to(message, (
                "A data de validade foi gerada aleatoriamente.\n"
                "Agora escolha o CVV:\n"
                "1️⃣ Envie *aleatório* para gerar automaticamente.\n"
                "2️⃣ Ou envie um CVV de 3 dígitos."
            ))
        else:
            try:
                month, year = map(int, expiry_date.split('/'))
                if 1 <= month <= 12 and year >= 2024:
                    state["expiry_date"] = f"{month:02}/{year}"
                    state["step"] = 3
                    bot.reply_to(message, (
                        "Data de validade definida!\n"
                        "Agora escolha o CVV:\n"
                        "1️⃣ Envie *aleatório* para gerar automaticamente.\n"
                        "2️⃣ Ou envie um CVV de 3 dígitos."
                    ))
                else:
                    bot.reply_to(message, "Por favor, envie uma data válida no formato MM/AAAA acima de 2024.")
            except ValueError:
                bot.reply_to(message, "Formato inválido. Por favor, use MM/AAAA ou envie *aleatório*.")

    # Etapa 3: Recebe o CVV
    elif state["step"] == 3:
        cvv_input = message.text.strip()
        if cvv_input.lower() == "aleatório":
            state["cvv"] = generate_cvv()
        elif cvv_input.isdigit() and len(cvv_input) == 3:
            state["cvv"] = cvv_input
        else:
            bot.reply_to(message, "Por favor, envie um CVV válido (3 dígitos) ou *aleatório*.")
            return

        # Gera o cartão e consulta informações da BIN
        bin_input = state["bin"]
        card_number = generate_card_number(bin_input)
        expiry_date = state["expiry_date"]
        cvv = state["cvv"]
        bin_info = fetch_bin_info(bin_input)

        # Formata as informações da BIN
        bin_details = ""
        if bin_info:
            bin_details = (
                f"🌍 País: {bin_info.get('country', {}).get('name', 'Desconhecido')}\n"
                f"🏦 Banco: {bin_info.get('bank', {}).get('name', 'Desconhecido')}\n"
                f"💳 Tipo: {bin_info.get('type', 'Desconhecido').capitalize()}\n"
                f"⭐ Nível: {bin_info.get('brand', 'Desconhecido')}\n"
            )
        else:
            bin_details = "❌ Não foi possível obter informações da BIN."

        # Envia o resultado
        bot.reply_to(message, (
            f"Cartão Gerado:\n"
            f"💳 Número: {card_number}\n"
            f"📅 Validade: {expiry_date}\n"
            f"🔒 CVV: {cvv}\n\n"
            f"Informações da BIN:\n{bin_details}\n"
            f"Obrigado por usar o gerador!"
        ))
        del user_states[chat_id]  # Remove o estado do usuário após concluir

# Inicia o bot
bot.polling()
