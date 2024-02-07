from Bot.create_event import criar_evento_interativo
from Bot.list_events import listar_eventos
import spacy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

def interpretar_entrada(texto, vectorizer, nb_classifier):
    # Carregar o modelo de idioma em português
    nlp = spacy.load("pt_core_news_sm")
    
    # Processar o texto de entrada
    doc = nlp(texto)
    
    # Extrair tokens do texto
    tokens = [token.text for token in doc]

    # Transformar os tokens usando o vetorizador
    vetor_caracteristicas = vectorizer.transform([" ".join(tokens)])

    # Fazer a previsão usando o modelo treinado
    previsao = nb_classifier.predict(vetor_caracteristicas)

    return previsao[0]

def main():
    print("Olá! Eu sou o seu assistente virtual. Em que posso ajudar hoje?")

    # ID do calendário onde os eventos serão listados ou adicionados
    calendar_id = '042bd9f9c7757f611d765a6b8fb84c7911246aa7d2ee6ce260dbc19953048450@group.calendar.google.com'

    # Carregar o vetorizador e o modelo treinado
    vectorizer = joblib.load("vectorizer.joblib")
    nb_classifier = joblib.load("nb_classifier.joblib")

    while True:
        entrada = input("Digite sua solicitação: ")
        
        # Interpretar a entrada do usuário
        intencao = interpretar_entrada(entrada, vectorizer, nb_classifier)
        
        # Executar a ação correspondente com base na intenção identificada
        if intencao == "listar_eventos":
            eventos = listar_eventos(calendar_id)
            print(eventos)
        elif intencao == "criar_evento":
            resultado = criar_evento_interativo(calendar_id)
            print(resultado)
        elif entrada.lower() == 'sair':
            print("Até logo!")
            break
        else:
            print("Desculpe, não entendi a sua solicitação.")

if __name__ == "__main__":
    main()
