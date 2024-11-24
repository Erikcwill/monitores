import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
import re

# Token do seu bot
TOKEN = '8153777066:AAF1OdVHv6KC3yy2p-dNhPgQQcAONrCwFa8'
bot = telegram.Bot(token=TOKEN)

# Dicionário para armazenar as mensagens recebidas temporariamente
mensagens_recebidas = {}

def filtrar_pontos_zerados_por_cidade(texto):
    # 1. Separar o texto em blocos por rota ou monitor usando cabeçalhos como "ROTA X" ou "Монитор"
    blocos = re.split(r'(?=🔵ROTA \d+🔵|Монитор #[\d]+)', texto)

    # Dicionário para armazenar pontos por cidade/rota, pontos de fundo e reservas
    cidades_pontos = {}
    pontos_de_fundo = []
    pontos_reservas = []
    cidade_atual = None

    for bloco in blocos:
        # Capturar o nome do bloco (primeira linha do bloco)
        linhas = bloco.split("\n")
        rota_nome = linhas[0].strip()

        # Remover qualquer palavra que apareça junto com "ROTA"
        rota_nome = re.sub(r'(🔵ROTA \d+🔵).*', r'\1', rota_nome)

        # Verificar se há mudança de cidade (Itajai ou Navegantes)
        if 'ITAJAI' in bloco:
            cidade_atual = 'ITAJAI'
            continue
        elif 'NAVEGANTES' in bloco:
            cidade_atual = 'NAVEGANTES'
            continue

        pontos_unidos = []
        ponto_atual = ""

        # Unir linhas relacionadas ao mesmo ponto
        for linha in linhas[1:]:
            if linha.startswith(("🅿️", "🏆", "🛻")):
                if ponto_atual:
                    pontos_unidos.append(ponto_atual.strip())
                ponto_atual = linha
            else:
                ponto_atual += " " + linha

        # Adicionar o último ponto acumulado
        if ponto_atual:
            pontos_unidos.append(ponto_atual.strip())

        # Filtrar os pontos que terminam com "- 0❗️" (considerando emojis como 🅿️, 🏆, e 🛻)
        regex = re.compile(r'.* - 0❗️.*')
        pontos_zerados = [ponto for ponto in pontos_unidos if regex.search(ponto)]

        # Separar os pontos de fundo, reservas e rotas
        for ponto in pontos_zerados:
            if "Reserva" in ponto:
                pontos_reservas.append(ponto)
            elif "🌞" in ponto and "💼" in ponto:
                if rota_nome not in cidades_pontos:
                    cidades_pontos[rota_nome] = {'ITAJAI': [], 'NAVEGANTES': []} if cidade_atual else []
                if cidade_atual:
                    cidades_pontos[rota_nome][cidade_atual].append(ponto)
                else:
                    cidades_pontos[rota_nome].append(ponto)
            else:
                pontos_de_fundo.append(ponto)

    # Montar a resposta final separada por rota, monitor, reservas e pontos de fundo
    resposta = "🚨 Pontos zerados encontrados:\n\n"
    emoji_cidade = "🏙️"
    if 'ITAJAI' in texto or 'NAVEGANTES' in texto:
        if 'ITAJAI' in texto:
            resposta += f"{emoji_cidade} ITAJAI:\n"
            pontos_itajai_existem = False
            for rota, pontos in cidades_pontos.items():
                if pontos['ITAJAI']:  # Somente incluir rotas que têm pontos zerados em ITAJAI
                    pontos_itajai_existem = True
                    resposta += f"\n{rota}:\n"
                    for ponto in pontos['ITAJAI']:
                        ponto_limpo = re.sub(r'(\s?🌞.*|💼.*|🎉.*|https?:\/\/\S+|\(.*?\))', '', ponto).strip()
                        if "- 0❗️" not in ponto_limpo:
                            ponto_limpo += " - 0❗️"
                        resposta += f"{ponto_limpo}\n"
            if not pontos_itajai_existem:
                resposta += "Nenhum ponto zerado!\n"

        resposta += "\n"

        if 'NAVEGANTES' in texto:
            resposta += f"{emoji_cidade} NAVEGANTES:\n"
            pontos_navegantes_existem = False
            for rota, pontos in cidades_pontos.items():
                if pontos['NAVEGANTES']:  # Somente incluir rotas que têm pontos zerados em NAVEGANTES
                    pontos_navegantes_existem = True
                    resposta += f"\n{rota}:\n"
                    for ponto in pontos['NAVEGANTES']:
                        ponto_limpo = re.sub(r'(\s?🌞.*|💼.*|🎉.*|https?:\/\/\S+|\(.*?\))', '', ponto).strip()
                        if "- 0❗️" not in ponto_limpo:
                            ponto_limpo += " - 0❗️"
                        resposta += f"{ponto_limpo}\n"
            if not pontos_navegantes_existem:
                resposta += "Nenhum ponto zerado!\n"

        resposta += "\n"
    else:
        for rota, pontos in cidades_pontos.items():
            if pontos:  # Somente incluir rotas que têm pontos zerados
                resposta += f"\n{rota}:\n"
                for ponto in pontos:
                    # Filtrando para remover quantidades e deixar apenas o nome do ponto e emojis necessários
                    ponto_limpo = re.sub(r'(\s?🌞.*|💼.*|🎉.*|https?:\/\/\S+|\(.*?\))', '', ponto).strip()
                    # Garantir que todos os pontos terminem com "- 0❗️"
                    if "- 0❗️" not in ponto_limpo:
                        ponto_limpo += " - 0❗️"
                    resposta += f"{ponto_limpo}\n"

    # Adicionar "Pontos de Fundo" como uma seção separada, se houver
    if pontos_de_fundo:
        resposta += "\n🔵PONTOS DE FUNDO🔵\n"
        for ponto in pontos_de_fundo:
            # Filtrar para remover quantidades e deixar apenas o nome do ponto e emojis necessários
            ponto_limpo = re.sub(r'(\s?🌞.*|💼.*|🎉.*|https?:\/\/\S+|\(.*?\))', '', ponto).strip()
            # Garantir que todos os pontos terminem com "- 0❗️"
            if "- 0❗️" not in ponto_limpo:
                ponto_limpo += " - 0❗️"
            resposta += f"{ponto_limpo}\n"

    # Adicionar "Reservas" como uma seção separada, se houver
    if pontos_reservas:
        resposta += "\n🔵RESERVAS🔵\n"
        for ponto in pontos_reservas:
            # Filtrar para remover quantidades e deixar apenas o nome do ponto e emojis necessários
            ponto_limpo = re.sub(r'(\s?🌞.*|💼.*|🎉.*|https?:\/\/\S+|\(.*?\))', '', ponto).strip()
            # Garantir que todos os pontos terminem com "- 0❗️"
            if "- 0❗️" not in ponto_limpo:
                ponto_limpo += " - 0❗️"
            resposta += f"{ponto_limpo}\n"

    # Remover linhas vazias adicionais da resposta
    resposta = re.sub(r'\n{3,}', '\n\n', resposta).strip()

    return resposta if len(cidades_pontos) > 0 or len(pontos_de_fundo) > 0 or len(pontos_reservas) > 0 else "Nenhum ponto está zerado no momento."

def filtrar_pontos_maiores(texto):
    # Separar o texto em blocos por rota ou monitor usando cabeçalhos como "ROTA X" ou "Монитор"
    blocos = re.split(r'(?=🔵ROTA \d+🔵|Монитор #[\d]+)', texto)

    # Dicionário para armazenar pontos por rota
    cidades_pontos = {}
    cidade_atual = None

    for bloco in blocos:
        # Capturar o nome do bloco (primeira linha do bloco)
        linhas = bloco.split("\n")
        rota_nome = linhas[0].strip()

        # Remover qualquer palavra que apareça junto com "ROTA"
        rota_nome = re.sub(r'(🔵ROTA \d+🔵).*', r'\1', rota_nome)

        # Verificar se há mudança de cidade (Itajai ou Navegantes)
        if 'ITAJAI' in bloco:
            cidade_atual = 'ITAJAI'
            continue
        elif 'NAVEGANTES' in bloco:
            cidade_atual = 'NAVEGANTES'
            continue

        pontos_unidos = []
        ponto_atual = ""

        # Unir linhas relacionadas ao mesmo ponto
        for linha in linhas[1:]:
            if linha.startswith(("🅿️", "🏆", "🛻")):
                if ponto_atual:
                    pontos_unidos.append(ponto_atual.strip())
                ponto_atual = linha
            else:
                ponto_atual += " " + linha

        # Adicionar o último ponto acumulado
        if ponto_atual:
            pontos_unidos.append(ponto_atual.strip())

        # Capturar todos os pontos com suas quantidades
        regex = re.compile(r'- (\d+)')  # Regex para capturar a quantidade no final
        pontos_com_quantidade = [
            (ponto, int(regex.search(ponto).group(1))) for ponto in pontos_unidos if regex.search(ponto)
        ]

        # Armazenar os pontos por rota
        if pontos_com_quantidade:
            if rota_nome not in cidades_pontos:
                cidades_pontos[rota_nome] = []
            cidades_pontos[rota_nome].extend(pontos_com_quantidade)

    # Montar a resposta final com os 5 maiores pontos
    resposta = "📈 Pontos com maior quantidade de patinetes:\n\n"
    todos_pontos = [
        (rota, ponto, quantidade) for rota, pontos in cidades_pontos.items() for ponto, quantidade in pontos
    ]
    maiores_pontos = sorted(todos_pontos, key=lambda x: x[2], reverse=True)[:5]  # Ordena e pega os 5 maiores

    # Agrupar por rota
    rotas_maiores = {}
    for rota, ponto, quantidade in maiores_pontos:
        if rota not in rotas_maiores:
            rotas_maiores[rota] = []
        rotas_maiores[rota].append((ponto, quantidade))

    for rota, pontos in rotas_maiores.items():
        resposta += f"{rota}:\n"
        for ponto, quantidade in pontos:
            ponto_limpo = re.sub(r'(\s?🌞.*|💼.*|🎉.*|https?:\/\/\S+|\(.*?\))', '', ponto).strip()
            resposta += f" 🅿️🏆{ponto_limpo} - {quantidade}\n"

    return resposta.strip() if maiores_pontos else "Nenhum ponto com quantidade significativa encontrado."




# Função para exibir os botões "Filtrar zerados" e "Top 5 maiores"
def perguntar_acao(update, context):
    chat_id = update.message.chat_id
    mensagem_texto = update.message.text
    mensagens_recebidas[chat_id] = mensagem_texto
    
    keyboard = [
        [InlineKeyboardButton("Filtrar zerados", callback_data='filtrar_zerados')],
        [InlineKeyboardButton("Top 5 maiores", callback_data='filtrar_maiores')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('O que você gostaria de fazer com a mensagem recebida?', reply_markup=reply_markup)

# Função que processa a resposta ao clicar nos botões
def callback_botao(update, context):
    query = update.callback_query
    query.answer()
    
    chat_id = query.message.chat_id
    mensagem = mensagens_recebidas.get(chat_id)
    
    if query.data == 'filtrar_zerados' and mensagem:
        pontos_zerados = filtrar_pontos_zerados_por_cidade(mensagem)
        query.edit_message_text(text=pontos_zerados)
    elif query.data == 'filtrar_maiores' and mensagem:
        pontos_maiores = filtrar_pontos_maiores(mensagem)
        query.edit_message_text(text=pontos_maiores)
    else:
        query.edit_message_text(text="Nenhuma mensagem foi recebida para processar.")

def start(update, context):
    update.message.reply_text("Bot de Monitoramento Iniciado! Envie a mensagem completa para filtrar os pontos zerados ou os maiores.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Comando /start
    dp.add_handler(CommandHandler("start", start))

    # Handler para mensagens de texto
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, perguntar_acao))

    # Handler para o clique nos botões
    dp.add_handler(CallbackQueryHandler(callback_botao))

    # Iniciar o polling
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
