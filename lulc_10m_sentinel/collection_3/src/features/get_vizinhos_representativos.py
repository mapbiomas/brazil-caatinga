import copy
import json
import arqParametros as AP

# este dictionariuo vai ter como key as bacias 
# e o maior número de bacias vizinhas 
# quem mais vizinhas tiver mais representativo ele é 
newdict = {}

with open('dict_basin_neigbor.json', 'r') as arquivo_json:
    dictBaciasViz = json.load(arquivo_json)

# ------------------------------------------------#
cc = 1
for mkey, lstVal in dictBaciasViz.items():
    print(f"#{cc} -> {mkey} >> {lstVal}")
    cc += 1

    for nbac in lstVal:
        # update lst Keys 
        lstBasin = [str(kk) for kk in list(newdict.keys())]
        if str(nbac) not in lstBasin:
            newdict[str(nbac)] = 1
        else:
            newdict[str(nbac)] += 1


# Ordenando os valores em ordem crescente
valores_ordenados = sorted(newdict.items(), key=lambda item: item[1], reverse= True)
print(valores_ordenados)
# Criando um novo dicionário ordenado pelos valores
newdict = copy.deepcopy(dict(valores_ordenados))
lst10first = []
cc = 1
for mkey, nVal in newdict.items():
    print(f"#{cc} -> {mkey} >> {nVal}")
    if cc < 10:
        lst10first.append(mkey)
    cc += 1
    
print("lista dos 10 primeiros \n ", lst10first)