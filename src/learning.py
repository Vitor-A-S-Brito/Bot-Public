from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import joblib


# Seu conjunto de treinamento original
conjunto_treinamento = [
    (['Liste', 'meus', 'eventos'], {'intent': 'listar_eventos'}),
    (['Quais', 'são', 'meus', 'próximos', 'compromissos', '?'], {'intent': 'listar_eventos'}),
    (['Mostre', 'os', 'eventos', 'do', 'meu', 'calendário'], {'intent': 'listar_eventos'}),
    (['Exibir', 'eventos', 'marcados'], {'intent': 'listar_eventos'}),
    (['Gostaria', 'de', 'ver', 'meus', 'eventos'], {'intent': 'listar_eventos'}),
    (['Poderia', 'mostrar', 'minhas', 'reuniões'], {'intent': 'listar_eventos'}),
    (['Mostre', 'minha', 'agenda', 'para', 'esta', 'semana'], {'intent': 'listar_eventos'}),
    (['Quais', 'são', 'os', 'eventos', 'agendados', 'para', 'hoje', '?'], {'intent': 'listar_eventos'}),
    (['Crie', 'um', 'novo', 'evento'], {'intent': 'criar_evento'}),
    (['agende', 'para', 'mim'], {'intent': 'criar_evento'}),
    (['Quero', 'marcar', 'um', 'compromisso'], {'intent': 'criar_evento'}),
    (['Adicione', 'um', 'evento', 'ao', 'meu', 'calendário'], {'intent': 'criar_evento'}),
    (['Gostaria', 'de', 'criar', 'um', 'evento'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'amanhã'], {'intent': 'criar_evento'}),
    (['crie', 'para', 'mim', 'um', 'evento'], {'intent': 'criar_evento'}),
    (['criar', 'evento'], {'intent': 'criar_evento'}),
    (['marcar', 'evento'], {'intent': 'criar_evento'}),
    (['agendar', 'compromisso'], {'intent': 'criar_evento'}),
    (['Marque', 'compromisso', 'para', 'mim', 'dia', '02'], {'intent': 'criar_evento'}),
    (['para', 'amanha', 'agende'], {'intent': 'criar_evento'}),
    (['marque', 'para', 'mim'], {'intent': 'criar_evento'}),
]

# Extrair tokens e contextos do conjunto de treinamento
tokens_treino = [exemplo[0] for exemplo in conjunto_treinamento]
contextos_treino = [exemplo[1]['intent'] for exemplo in conjunto_treinamento]

# Dividir os dados em conjuntos de treinamento e teste (por exemplo, 80% treinamento, 20% teste)
tokens_treino, tokens_teste, contextos_treino, contextos_teste = train_test_split(tokens_treino, contextos_treino, test_size=0.2, random_state=42)

# Criar uma lista de strings a partir dos tokens
tokens_treino_str = [' '.join(tokens) for tokens in tokens_treino]
tokens_teste_str = [' '.join(tokens) for tokens in tokens_teste]

# Criar uma matriz de contagem de termos (bag of words) com os tokens
vectorizer = CountVectorizer()
X_treino = vectorizer.fit_transform(tokens_treino_str)
X_teste = vectorizer.transform(tokens_teste_str)

# Inicializar e treinar o classificador Naive Bayes
nb_classifier = MultinomialNB()
nb_classifier.fit(X_treino, contextos_treino)


# Fazer previsões no conjunto de teste
previsoes = nb_classifier.predict(X_teste)

# Salvar o vetorizador e o classificador treinados em arquivos
joblib.dump(vectorizer, 'vectorizer.joblib')
joblib.dump(nb_classifier, 'nb_classifier.joblib')

# Avaliar o desempenho do modelo
print(classification_report(contextos_teste, previsoes))