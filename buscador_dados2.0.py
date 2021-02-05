import requests
from bs4 import BeautifulSoup
import datetime
from datetime import date
import time
from pymongo import MongoClient
import unicodedata
import re


client = MongoClient("mongodb+srv://pedrohique:qq54525658qq@cluster0.nt3ry.mongodb.net/mercado_livre?retryWrites=true&w=majority")
db = client.get_database('mercado_livre')
produto = input('Digite o nome do produto que deseja procurar: ')
qtdenc = int


def conectar(link):  # metodo captura dados da pagina de pesquisa e retorna na variavel declarada
    response = requests.get(link)
    html_doc = response.content
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup


def buscalinksml(produto):
    #global produto
    produto = produto.replace(' ', '-')
    print(produto)
    indice = 1
    linkconectar = f'https://lista.mercadolivre.com.br/{produto}_Desde_{indice}'

    def qtdencontrada(soup):

        for qtd in soup.find_all('div', class_='ui-search-search-result'):
            qtdbusca = qtd.string.replace('.', '')
            qtdbusca = int(qtdbusca.replace('resultados', ''))
            return qtdbusca

    def gravar_csv(linksgravar):

        with open('dados/linkspequisa.csv', mode='w+', newline='', encoding='UTF-8') as csv_file:
            for i in linksgravar:
                csv_file.write(f'{i}\n')

    def copiarlinks(soup):  # seleciona os links a serem analisados
        '''Dicionario de dados'''
        dadosprod = {}
        '''copiar links'''
        links = []
        for link in soup.find_all('a', class_='ui-search-item__group__element ui-search-link'):
            links.append(str(link.get('href')))
            dadosprod['link'] = link
        for link in soup.find_all('a', class_='ui-search-result__content ui-search-link'):
            links.append(str(link.get('href')))
            dadosprod['link'] = link

        '''copiar preços'''
        for preco in soup.find_all('span', class_='price-tag ui-pdp-price__part',
                                   itemprop='offers'):  # valor no mercado livre mudou, agora a classe tem o mesmo nome que o parcelamento
            valorcheio = preco.find('span',
                                    class_='price-tag-fraction')  # tag que extrai o valor fechado sem centavos, é rpeciso fazer a verificação se o valor não é nulo para nao ter erro
            valorcheio2 = str()
            if valorcheio != None:
                valorcheio2 = valorcheio.string
            valorcents = preco.find('span',
                                    class_='price-tag-cents')  # tag que extrai os centavos do produto, é prciso fazer a verificação se o valor não é nulo
            if valorcents != None:
                valorcents2 = valorcents.string
                valortotal = f'{valorcheio2},{valorcents2}'
                dadosprod['valor'] = valortotal
            elif valorcents == None:
                valortotal = f'{valorcheio2}'
                dadosprod['valor'] = valortotal


        #gravar_csv(links)
        return dadosprod


    dados = conectar(linkconectar)
    print(dados)
    global qtdenc

    qtdenc = qtdencontrada(dados)
    print(f'{qtdenc} itens encontrados')
    #minutos = (qtdenc * 4) / 60 #datetime.timedelta(seconds=qtd)

    tempo = datetime.timedelta(seconds=(qtdenc*5))


    print(f'Tempo aproximado para extração: {tempo} horas/min/seg')
    links = []
    print('Iniciando a captura de links...')
    while indice < qtdenc:
        for link in copiarlinks(dados).keys():
            print(link)
            links.append(link)
        dados = conectar(linkconectar)
        indice = indice + 50
    return links


def removeracce(palavra):

    # Unicode normalize transforma um caracter em seu equivalente em latin.
    nfkd = unicodedata.normalize('NFKD', palavra)
    palavraSemAcento = u"".join([c for c in nfkd if not unicodedata.combining(c)])

    # Usa expressão regular para retornar a palavra apenas com números, letras e espaço
    return re.sub('[^a-zA-Z0-9 \\\]', '', palavraSemAcento)


def lerlinksml(links):
    global dadoscsv
    global produto
    index = 1
    print("iniciando a leitura dos links...")
    for link in links:
        soup = conectar(link)
        dadoscsv = {}
        for name in soup.find_all('h1', class_='ui-pdp-title'):
            dadoscsv['Produto'] = name.string
        for tag in soup.find_all('tbody', class_='andes-table__body'):
            marcador = []
            valores = []
            for tag2 in soup.find_all('tr', class_='andes-table__row'):
                label = tag2.find('th').string
                value = tag2.find('span').string
                marcador.append(label)
                valores.append(value)
                for marca, valor in zip(marcador, valores):
                    dadoscsv[marca] = valor
        for preco in soup.find_all('span', class_='price-tag ui-pdp-price__part', itemprop='offers'): #valor no mercado livre mudou, agora a classe tem o mesmo nome que o parcelamento
            valorcheio = preco.find('span', class_='price-tag-fraction')#tag que extrai o valor fechado sem centavos, é rpeciso fazer a verificação se o valor não é nulo para nao ter erro
            valorcheio2 = str()
            if valorcheio != None:
                valorcheio2 = valorcheio.string
            valorcents = preco.find('span', class_='price-tag-cents') #tag que extrai os centavos do produto, é prciso fazer a verificação se o valor não é nulo
            if valorcents != None:
                valorcents2 = valorcents.string
                valortotal = f'{valorcheio2},{valorcents2}'
            elif valorcents == None:
                valortotal = f'{valorcheio2}'
            dadoscsv['Valor'] = valortotal
        for dados in soup.find_all('span', class_='ui-pdp-subtitle'):
            qtd = dados.string.replace('\n', '').replace('\t', '').replace('vendidos',
                                                                        '').replace('vendido','').lower()
            qtd = qtd.split()
            for x in qtd:
                if qtd.index(x) > 0:
                        dadoscsv['QTD Vendida'] = qtd[2]
                if qtd[0] == 'novo':
                    dadoscsv['estado'] = qtd[0]
            dadoscsv['Link'] = link


        print(f'lendo link nº: {index} de {qtdenc}')

        tempo = datetime.timedelta(seconds=((qtdenc - index)*5))
        print(f'Tempo restante aproximado para o fim da extração: {tempo} horas/min/seg')

        index = index + 1
        produto = removeracce(produto)
        #print(produto)
        table = db.get_collection(f'{produto}_{date.today()}')
        table.insert_one(dadoscsv)
        #print(dadoscsv)
        time.sleep(2)


buscalinksml(produto)