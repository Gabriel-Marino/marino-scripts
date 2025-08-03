from re import sub
from os import remove

academicos = {
    "Gabriel"   :   20,
    "Brenno"    :   22,
    "Matheus"   :   20
}

list(map(lambda nome: open("certificado_{}_temp.tex".format(nome), "w").write(sub('#NOME', nome, open("certificado.tex", "r").read())), academicos))
list(map(lambda nome: open("certificado_{}.tex".format(nome), "w").write(sub('#HORAS', str(academicos[nome]), open("certificado_{}_temp.tex".format(nome), "r").read())), academicos))
list(map(lambda nome: remove("certificado_{}_temp.tex".format(nome)), academicos))
