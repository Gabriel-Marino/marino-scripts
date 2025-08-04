#   Estudar o código aqui: https://colab.research.google.com/drive/1n4XAEyNBrBzWQBQC8KJcnE-WOI42LeS9
#   Inspirado por:  https://twitter.com/BrennoSullivan/status/1576655828089974785

import os

from json import loads
from pandas import DataFrame
from requests import get
from time import sleep, ctime

def kill():

    if os.name == "nt":
        return f'taskkill /PID {os.getpid()} /F'

    return f'kill -9 {os.getpid()}'

def clear():

    if os.name == "nt":
        return 'cls'

    return 'clear'

if __name__ == "__main__":
    try:
        while True:
            json_data = loads(get("https://resultados.tse.jus.br/oficial/ele2022/545/dados-simplificados/br/br-c0001-e000545-r.json").content)  #   Solicita os dados dos candidatos a presidência da API do TSE-BR.
            poll_percentage = float(json_data['pst'].replace(',', '.'))
            sep_data = [
                [[], 'nm'],     #   candidatos.
                [[], 'vap'],    #   número de votos.
                [[], 'pvap']    #   porcentagem.
                ]

            list(map(lambda data: list(map(lambda info: data[0].append(info[data[1]]) if info['seq'] in '1 2'.split(' ') else 0, json_data['cand'])), sep_data))

            os.system(clear())     #   limpa o console antes de imprimir dados novos.
            print(ctime())      #   Imprime a data e hora atual.
            print("Última atualização: {}".format(json_data['ht']))                                                                             #   Emprime o momento da última atualização enviada pelo TSE.
            print("Foram apuradas {}% urnas.".format(poll_percentage))                                                                          #   Emprime a quantidade de urnas que já foram apuradas em porcentagem.
            print(DataFrame(list(zip(sep_data[0][0], sep_data[1][0], sep_data[2][0])), columns=['Candidato', '# votos', 'Porcentagem']))        #   Cria a tabela para mostrar os dados mais organizadamente.

            os.system(kill()) if poll_percentage >= 99 else sleep(300)    #   Para o laço caso tenha apurado 99% das urnas, caso contrário espera por 5 minutos antes de imprimir os dados novos.

    except Exception as e:
        print(f"An exception occured: {e}")
