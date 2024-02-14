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
    (['Crie', 'um', 'compromisso'], {'intent': 'criar_evento'}),
    (['crie', 'para', 'mim', 'um', 'evento'], {'intent': 'criar_evento'}),
    (['criar', 'evento'], {'intent': 'criar_evento'}),
    (['marcar', 'evento'], {'intent': 'criar_evento'}),
    (['agendar', 'compromisso'], {'intent': 'criar_evento'}),
    (['Marque', 'compromisso', 'para', 'mim'], {'intent': 'criar_evento'}),
    (['para', 'amanha', 'agende'], {'intent': 'criar_evento'}),
    (['marque', 'para', 'mim'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'compromisso', 'para', 'o', 'evento', 'de', 'lançamento'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'almoço', 'com', 'o', 'cliente', 'no', 'próximo', 'sábado'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'evento', 'para', 'a', 'palestra', 'do', 'professor', 'Carlos'], {'intent': 'criar_evento'}),
    (['Quero', 'marcar', 'um', 'encontro', 'com', 'os', 'amigos', 'no', 'parque', 'no', 'dia', '15'], {'intent': 'criar_evento'}),
    (['Marque', 'uma', 'apresentação', 'para', 'a', 'nova', 'campanha', 'publicitária', 'na', 'próxima', 'semana'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'reunião', 'de', 'equipe', 'no', 'dia', '10', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'a', 'sessão', 'de', 'autógrafos', 'no', 'dia', '15', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Quero', 'marcar', 'um', 'almoço', 'com', 'a', 'família', 'no', 'próximo', 'domingo', 'às', '12', 'horas'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'a', 'visita', 'técnica', 'na', 'próxima', 'semana'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'compromisso', 'para', 'o', 'curso', 'de', 'fotografia', 'no', 'dia', '25', 'de', 'maio'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'evento', 'para', 'a', 'oficina', 'de', 'culinária', 'no', 'dia', '10', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'encontro', 'para', 'a', 'sessão', 'de', 'cinema', 'no', 'sábado', 'à', 'noite'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'conferência', 'anual', 'da', 'empresa'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'workshop', 'de', 'marketing', 'digital'], {'intent': 'criar_evento'}),
    (['Quero', 'marcar', 'um', 'almoço', 'com', 'os', 'colegas', 'de', 'trabalho', 'no', 'dia', '20', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'happy', 'hour', 'na', 'sexta-feira'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'compromisso', 'para', 'o', 'treinamento', 'de', 'vendas', 'no', 'dia', '25'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'evento', 'para', 'a', 'feira', 'de', 'livros', 'no', 'próximo', 'mês'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'encontro', 'para', 'o', 'congresso', 'de', 'tecnologia', 'no', 'dia', '15', 'de', 'maio'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'reunião', 'de', 'família', 'no', 'domingo', 'à', 'tarde'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'a', 'reunião', 'com', 'o', 'cliente', 'no', 'dia', '10', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'aniversário', 'do', 'José'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'entrega', 'dos', 'prêmios', 'no', 'dia', '15'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'encontro', 'para', 'o', 'jantar', 'com', 'os', 'amigos', 'no', 'dia', '20', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'a', 'visita', 'ao', 'parque', 'no', 'sábado'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'reunião', 'do', 'clube', 'de', 'leitura', 'no', 'próximo', 'mês'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'a', 'palestra', 'sobre', 'empreendedorismo', 'no', 'dia', '05'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'encontro', 'no', 'parque', 'no', 'próximo', 'domingo'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'feira', 'de', 'ciências', 'no', 'dia', '12', 'de', 'maio'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'a', 'palestra', 'sobre', 'saúde', 'mental', 'no', 'dia', '10', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'encontro', 'cultural', 'na', 'próxima', 'semana'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'reunião', 'com', 'os', 'fornecedores', 'no', 'dia', '18'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'a', 'visita', 'ao', 'museu', 'no', 'dia', '25', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'a', 'festança', 'junina', 'em', 'julho'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'almoço', 'de', 'negócios', 'no', 'dia', '30'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'a', 'confraternização', 'da', 'empresa', 'no', 'próximo', 'mês'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'encontro', 'esportivo', 'na', 'próxima', 'semana'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'a', 'reunião', 'de', 'equipe', 'no', 'dia', '12'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'curso', 'de', 'idiomas', 'no', 'próximo', 'mês'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'almoço', 'com', 'os', 'colegas', 'de', 'trabalho', 'no', 'dia', '20'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '10'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '15'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '20'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '25'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '30'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '05'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '12'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '18'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '22'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '28'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '03'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '08'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '14'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '21'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '10', 'de', 'fevereiro'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '15', 'de', 'março'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '20', 'de', 'abril'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '25', 'de', 'maio'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '30', 'de', 'junho'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '05', 'de', 'julho'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '12', 'de', 'agosto'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '18', 'de', 'setembro'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '22', 'de', 'outubro'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '28', 'de', 'novembro'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '03', 'de', 'dezembro'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '08', 'de', 'janeiro'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '14', 'de', 'fevereiro'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '21', 'de', 'março'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '10', 'de', 'abril', 'às', '10h'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '15', 'de', 'março', 'às', '15h'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '20', 'de', 'abril', 'às', '14h'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '25', 'de', 'maio', 'às', '16h'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '30', 'de', 'junho', 'às', '09h'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '05', 'de', 'julho', 'às', '11h'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '12', 'de', 'agosto', 'às', '13h'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '18', 'de', 'setembro', 'às', '14h'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '22', 'de', 'outubro', 'às', '10h'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '28', 'de', 'novembro', 'às', '09h'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '03', 'de', 'dezembro', 'às', '15h'], {'intent': 'criar_evento'}),
    (['Crie', 'um', 'compromisso', 'para', 'o', 'dia', '08', 'de', 'janeiro', 'às', '14h'], {'intent': 'criar_evento'}),
    (['Marque', 'um', 'evento', 'para', 'o', 'dia', '14', 'de', 'fevereiro', 'às', '13h'], {'intent': 'criar_evento'}),
    (['Agende', 'um', 'evento', 'para', 'o', 'dia', '21', 'de', 'março', 'às', '11h'], {'intent': 'criar_evento'}),
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