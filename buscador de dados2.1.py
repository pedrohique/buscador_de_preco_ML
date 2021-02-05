'''Na versão 2.1 a busca é menos detalhada, porem muito mais rapida, pois busca e extrai o os dados direto do menu de produtos e não da pagina do item.'''

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
import time
from pymongo import MongoClient
import unicodedata
import re

'''conexão banco mongo'''
client = MongoClient("mongodb+srv://pedrohique:qq54525658qq@cluster0.nt3ry.mongodb.net/mercado_livre?retryWrites=true&w=majority")
db = client.mercado_livre

def escrever_banco(produto,dados):
    table = db.get_collection(f'{produto}_{date.today()}')
    table.insert_one(dados)

'''produto procurado'''
def produto_desejado():
    produto = input('Digite o nome do produto que deseja procurar: ')
    return produto


'''função para se conectar ao link atraves do requests - retorno todo codigo html da pagina que chamaremos de soup'''
def conectar(produto):  # metodo captura dados da pagina de pesquisa e retorna na variavel declarada
    response = requests.get(f'https://lista.mercadolivre.com.br/{produto}_Desde_0')
    html_doc = response.content
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup

def extrator_dados(soup, indice, df):
    '''div aonde esta localizado o item'''
    for itens in soup.find_all('div', class_='andes-card andes-card--flat andes-card--default ui-search-result ui-search-result--core andes-card--padding-default'):
        '''div aonde esta localizado os dados do item'''
        dict_dados = {}
        for classe in itens.find_all('div', class_='ui-search-result__content-wrapper'):
            dict_dados['index'] = indice
            '''nome - codigo a baixo busca o nome do item'''
            dados = classe.find('div', class_='ui-search-item__group ui-search-item__group--title')
            title = dados.find('a', class_='ui-search-item__group__element ui-search-link')
            produto = title.find('h2', class_='ui-search-item__title').string
            dict_dados['produto'] = produto
            '''preço - codigo abaixo busca o preço do item'''
            soup_preco = classe.find('div', class_='ui-search-result__content-columns')
            soup_preco1 = soup_preco.find('div', class_='ui-search-result__content-column ui-search-result__content-column--left')
            soup_preco2 = soup_preco1.find('div', class_='ui-search-item__group ui-search-item__group--price')
            soup_preco3 = soup_preco2.find('div', class_='ui-search-price ui-search-price--size-medium ui-search-item__group__element')
            soup_preco4 = soup_preco3.find('div', class_='ui-search-price__second-line')
            soup_preco5 = soup_preco4.find('span', class_='price-tag ui-search-price__part')
            preco_inteiro = soup_preco5.find('span', class_='price-tag-fraction')
            preco_fracao = soup_preco5.find('span', class_='price-tag-cents')
            if preco_fracao != None:
                valor = float(f'{preco_inteiro.string}.{preco_fracao.string}')
            else:
                valor = float(preco_inteiro.string)
            dict_dados['valor'] = valor
            #print(preco_total)
            '''frete gratis - S = 0 / N = 1'''
            try:
                soup_frete = classe.find('div', class_='ui-search-item__group ui-search-item__group--shipping')
            except:
                frete_gratis = 0
            try:
                soup_frete1 = soup_frete.find('div', class_='ui-search-item__group__element ui-search-item__group__element--shipping')
            except:
                frete_gratis = 0
            try:
                soup_frete2 = soup_frete1.find('p', class_='ui-search-item__shipping ui-search-item__shipping--free')
                if soup_frete2 != None:
                    frete_gratis = 1
            except:
                frete_gratis = 0
            dict_dados['frete_gratis'] = frete_gratis

            '''Extrair link'''
            soup_link = title.get('href')
            dict_dados['link'] = soup_link
            #print(soup_link)
            df.loc[indice] = [indice, produto, valor, frete_gratis, soup_link]
            indice = indice + 1

            #escrever_banco(produto_desejado, dict_dados)
            print(dict_dados)





'''extrator de indice - para fazer a busca e percorrer por varias paginas, vamos utilizar uma função para retornar a quantidade
   de produtos encontrador para alterar o indice do link'''
def extrator_indice(soup):
    index = soup.find('span', class_='ui-search-search-result__quantity-results')
    index = index.string.replace('.', '')
    index = int(index.replace('resultados', ''))
    return index



produto = produto_desejado()
df = pd.DataFrame(columns=['index', 'produto', 'valor', 'frete_gratis', 'link'])
indice = extrator_indice(conectar(produto))
indice_atual = 1
while indice_atual <= indice:
    extrator_dados(conectar(produto), indice_atual, df)
    indice_atual = indice_atual + 50
    time.sleep(2)
df.to_csv(f'{produto}_{date.today()}.csv', index=False)

