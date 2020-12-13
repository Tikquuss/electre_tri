""""
Usage : 
python main.py --profils_file path_to_profils.xlsx --criteres_file path_to_profil.xlsx --aliments_file path_to_aliments.xlsx --output_file path_to_output.xlsx --seuil_de_majorite 0.5

Example :
python main.py --profils_file data/profils.xlsx --criteres_file data/criteres.xlsx --aliments_file data/aliments.xlsx --output_file data/output.xlsx --seuil_de_majorite 0.5

Note : vous pouvez configurer les parametres par defaut et appeler le programme comme suit :
python main.py
"""

## Liste des parametres par defaut
profils_file_default = "data/profils.xlsx"
criteres_file_default = "data/criteres.xlsx"
aliments_file_default = "data/BD3_brut.xlsx"
seuil_de_majorite_default = 0.2
import os
# le fichier de sorti par defaut se trouve dans le meme repertoire que le fichier contenant les aliments
output_file_default = os.path.join(os.path.dirname(aliments_file_default), "output.xlsx") 

import itertools
import argparse 
import pandas as pd

categories = ["A", "B", "C", "D", "E"]

def get_c_j(H : list, b_i : list, j : int, type_critere : str) :
  """retourne cj(H,b_i) et cj(b_i,H) selon la formule indiquée ci-dessus, tous des apparténant à {0, 1}
    Parametres :
      - H (list or array) : aliment (tableau de taille égale au nombre de critères, exemple [1, 10, 100, 2.1, 0] pur 5 critères)
      - b_i (list or array) : profil (meme commentaire que pour H, exemple : [2, 1, 1, 100, 1, 1] )
      - j (int) : indice du critère (entre 0 et le nombre de critères)
      - type_critere (str) : chaine de caractère indiquant si le critère j est à maximiser (max) ou à minimiser (min)
  """
  assert type_critere in ["max", "min"]
  if type_critere == "max" :
    c_j_H_b_i = 1 if H[j] >= b_i[j] else 0
    c_j_b_i_H = 1 if b_i[j] >= H[j] else 0
  if type_critere == "min" :
    c_j_H_b_i = 1 if b_i[j] >= H[j] else 0
    c_j_b_i_H = 1 if H[j] >= b_i[j] else 0
  
  return c_j_H_b_i, c_j_b_i_H

def get_indices_de_concordance_partiels(criteres : list, aliments : dict, profils : dict) :
  """Retourne un dictionnaire conténant pour chaque aliment H et chaque critère b_i
     les indices de concordance partiels c(H, bi) et c(bi, H), tous des réelle (float)

     Parametres :
        - criteres (list) : la liste des critères et de leur types
              Exemple : [["Énergie", 'min'], ["Acide Gras sat.", 'min'], ["Sucre", 'min'], ["Sodium", 'min'], ["Protéine", 'max'], ["Fibre", 'max']]
        - aliments (dict) : dictionnaire conténant les aliments (la clé correspond au nom de l'aliment, et la valeur aux 
                            évaluation qualitative attribuée à l'aliment pour chaque critères)
              Exemple : aliments = {"aliment1" : [1, 2, 3, 1, 0.1, 10], 'aliment2': [2, 0, 1, 5, 1, 10]}
        - profils (dict) : dictionnaire conténant les profils (la clé correspond au nom du profil, et la valeur aux 
                            évaluation qualitative attribuée au profil pour chaque critères)
              Exemple : profils = {"b6" : [100, 0, 0, 0, 100, 100], "b5" : [1550, 11, 0.8, 0.3, 10, 11], 
                                  "b4" : [1650, 14, 1, 0.4, 7, 8], "b3" : [1750, 17, 1.7, 0.5, 4, 5], 
                                  "b2" : [1850, 20, 4, 0.6, 3, 2.5], "b1" : [10000, 100, 100, 100, 0, 0]}
  """
  c = {}
  for j in range(len(criteres)) :
    c[j] = {}
    for H, b_i in itertools.product(*[aliments.keys(), profils.keys()]) :
      c[j][H] = c[j].get(H, {})
      c[j][b_i] = c[j].get(b_i, {})
      c[j][H][b_i], c[j][b_i][H] = get_c_j(H = aliments[H], b_i = profils[b_i], j = j, type_critere = criteres[j][1])
  return c

def get_indices_de_concordance_globaux(n : int, indices_de_concordance_partiels : dict, proids : list) :
  """Retourne un dictionnaire conténant pour chaque aliment H et chaque critère b_i
     les indices de concordance globaux c(H, bi) et c(bi, H), tous des réelle (float)

     Parametres :
        - n (list) : nombre de critères
        - indices_de_concordance_partiels (dict) : dictionnaires conténant les indices de concordance partiels calculé comme illustrer à l'étapes 1
        - proids (liste) : listes de poids pour chaque critères (poids[j] = poids du critère j)
              Exemple : poids = [1, 1, 1, 1, 2, 2]
  """
  C = {}
  sum_k = sum(proids)
  for H, b_i in itertools.product(*[aliments.keys(), profils.keys()]) :
    C[H] = C.get(H, {})
    C[b_i] = C.get(b_i, {})
    C[H][b_i] = sum([ proids[j] * indices_de_concordance_partiels[j][H][b_i] for j in range(n)]) / sum_k 
    C[b_i][H] = sum([ proids[j] * indices_de_concordance_partiels[j][b_i][H] for j in range(n)]) / sum_k 
  return C

def surclass(seuil_de_majorite : float, H : str, b_i : str, indices_de_concordance_globaux : dict):
	"""relation de surclassement : retourne H S b_i et b_i S H (qui sont tous de boolean : c'est à dire Vrai(True) ou Faux(False))
     Parametres :
        - seuil_de_majorite (float) : réel entre 0 et 1 (ou 0% à 100%) répresentant le seuil de majorité
        - H (str) : nom de l'aliment
        - b_i (str) : nom du profil
        - indices_de_concordance_globaux (dict) : dictionnaires conténant les indices de concordance globaux calculer comme illustrer à l'étapes 2
  """
	H_S_b_i = indices_de_concordance_globaux[H][b_i] >= seuil_de_majorite
	b_i_S_H = indices_de_concordance_globaux[b_i][H] >= seuil_de_majorite
	return H_S_b_i, b_i_S_H

def PessimisticmajoritySorting(categories : list, aliments : dict, profils : dict, indices_de_concordance_globaux : dict, seuil_de_majorite : float) :
  """ Classe chaque aliment dans une catégorie selon la procédure d'affectation pessimiste
      Parametres : 
          - categories (list) : liste des categories 
              Exemple : categories= ["A", "B", "C", "D", "E"]
          - aliments (dict) : dictionnaire conténant les aliments (la clé correspond au nom de l'aliment, et la valeur aux 
                              évaluation qualitative attribuée à l'aliment pour chaque critères)
                      Exemple : aliments = {"aliment1" : [1, 2, 3, 1, 0.1, 10], 'aliment2': [2, 0, 1, 5, 1, 10]}
          - proids (liste) : listes de poids pour chaque critères (poids[j] = poids du critère j)
                      Exemple : poids = [1, 1, 1, 1, 2, 2]
          - indices_de_concordance_globaux (dict) : dictionnaires conténant les indices de concordance globaux calculer comme illustrer à l'étapes 2
          - seuil_de_majorite (float) : réel entre 0 et 1 (ou 0% à 100%) répresentant le seuil de majorité
  """
  result = {}
  r = len(categories)
  b = list(profils.keys())
  for H in aliments.keys() :
    for k in range(r-1, -1, -1) : 
      H_S_b_k, _ = surclass(seuil_de_majorite, H, b[k], indices_de_concordance_globaux)
      if H_S_b_k :
        result[H] = categories[k]
        break
    result[H] = result.get(H, categories[0]) 
  return result

def OptimisticmajoritySorting(categories : list, aliments : dict, profils : dict, indices_de_concordance_globaux : dict, seuil_de_majorite : float) : 
  """ Classe chaque aliment dans une catégorie selon la procédure d'affectation optimiste
      Parametres : 
          - categories (list) : liste des categories 
              Exemple : categories= ["A", "B", "C", "D", "E"]
          - aliments (dict) : dictionnaire conténant les aliments (la clé correspond au nom de l'aliment, et la valeur aux 
                              évaluation qualitative attribuée à l'aliment pour chaque critères)
                      Exemple : aliments = {"aliment1" : [1, 2, 3, 1, 0.1, 10], 'aliment2': [2, 0, 1, 5, 1, 10]}
          - proids (liste) : listes de poids pour chaque critères (poids[j] = poids du critère j)
                      Exemple : poids = [1, 1, 1, 1, 2, 2]
          - indices_de_concordance_globaux (dict) : dictionnaires conténant les indices de concordance globaux calculer comme illustrer à l'étapes 2
          - seuil_de_majorite (float) : réel entre 0 et 1 (ou 0% à 100%) répresentant le seuil de majorité
  """
  result = {}
  r = len(categories)
  b = list(profils.keys())
  for H in aliments.keys() :
    for k in range(1, r+1) :
      H_S_b_k, b_k_S_H = surclass(seuil_de_majorite, H, b[k], indices_de_concordance_globaux)
      #if b_k_S_H :
      if b_k_S_H and not H_S_b_k :
        result[H] = categories[k-1]
        break
    result[H] = result.get(H, categories[r-1])
  return result

def get_profils(file_path : str, sheet_name : str = None):
    """Prend un fichier excel conténant les profils ou les aliments et retourne le résultats au format :
      - aliments = {"aliment_1" : [1, 2, 3, 1, 0.1, 10], ..., 'aliment_n': [2, 0, 1, 5, 1, 10]} par exemple, s'il s'agit des aliments
      - profils = {"b6" : [100, 0, 0, 0, 100, 100], ..., "b1" : [10000, 100, 100, 100, 0, 0]} par exemple, s'il s'agit des profils

      Parametres :
        - file_path (str) : chemin du fichier excel
        - sheet_name (str) nom de la feuille excel cible (si aucune feuille n'est spécifiée, la prémiere feuille est considérée)
    """
    if sheet_name is None :
        content = pd.read_excel(file_path, index_col=0)
    else :
        content = pd.read_excel(file_path, index_col=0, sheet_name=sheet_name)
    indexs = content.index
    profils = {key : [] for key in indexs}
    for critere in content.keys() :
        C = content[critere]
        for key in indexs :
            profils[key].append(C[key])
    return profils

def get_criteres_poids(file_path : str, sheet_name : str = None):
    """Prend un fichier excel conténant les criteres, leur poids et leur type (max ou min) et retourne le résultats au format :
      - criteres = [["Énergie", 'min'], ["Acide Gras sat.", 'min'], ["Sucre", 'min'], ["Sodium", 'min'], ["Protéine", 'max'], ["Fibre", 'max']] par exemple
      - poids = [1, 1, 1, 1, 2, 2] par exemple

      Parametres :
        - file_path (str) : chemin du fichier excel
        - sheet_name (str) nom de la feuille excel cible (si aucune feuille n'est spécifiée, la prémiere feuille est considérée)
    """
    if sheet_name is None :
        content = pd.read_excel(file_path, index_col=0)
    else :
        content = pd.read_excel(file_path, index_col=0, sheet_name=sheet_name)
    #indexs = content.index
    poids, criteres = [], []
    for critere in content.keys() :
        C = content[critere]
        poids.append(C["poids"])
        criteres.append([critere, C["type_critere"]])
    return criteres, poids

def to_excel(classement, output_file : str, sheet_name : str = None):
    """Fonction écrivant les résultats fournis par les procédures d'affectation dans les fichiers excel

      Parametres :
        - classement (dict) : dictionnaire conténant pour chaque aliment (clé = nom de l'aliment) sa catégorie (valeur)
        - output_file (str) : chemin du fichier excel dans lequel le résultat sera stocké
        - sheet_name (str) nom de la feuille excel cible (si aucune feuille n'est spécifié, la prémiere feuille est considérée)
    """
    index = classement.keys()
    columns = ["categories"]
    df = list(classement.values())
    df = [[a] for a in df]
    df = pd.DataFrame(df, index=index, columns = columns)
    if sheet_name is None :
        df.to_excel(output_file)
    else :
        df.to_excel(output_file, sheet_name = sheet_name)
 
if __name__ == '__main__' :
    
    # parse parameters
    parser = argparse.ArgumentParser(description = "parameters parser")
    parser.add_argument("--profils_file", type = str, default = profils_file_default, help = "Chemin du fichier xlsx contenant les profils")
    parser.add_argument("--criteres_file", type = str, default = criteres_file_default, help = "Chemin du fichier xlsx contenant les criteres")
    parser.add_argument("--aliments_file", type = str, default = aliments_file_default, help = "Chemin du fichier xlsx contenant les aliments")
    parser.add_argument("--output_file", type = str, default = output_file_default , help = "Chemin du fichier xlsx contenant les aliments")
    parser.add_argument("--seuil_de_majorite", type = float, default = seuil_de_majorite_default, help = "seuil de majorite")
    params = parser.parse_args() 

    # check parameters 
    assert os.path.isfile(params.profils_file)
    assert os.path.isfile(params.criteres_file)
    assert os.path.isfile(params.aliments_file)
    seuil_de_majorite = params.seuil_de_majorite
    if not params.output_file :
        params.output_file = os.path.join(os.path.dirname(params.aliments_file), "output.xlsx") 
        
    #criteres = [["Énergie", 'min'], ["Acide Gras sat.", 'min'], ["Sucre", 'min'], ["Sodium", 'min'], ["Protéine", 'max'], ["Fibre", 'max']]
    #proids = [1, 1, 1, 1, 2, 2]
    criteres, poids = get_criteres_poids(file_path = params.criteres_file)
    
    #profils = {"b6" : [100, 0, 0, 0, 100, 100], "b5" : [1550, 11, 0.8, 0.3, 10, 11], "b4" : [1650, 14, 1, 0.4, 7, 8], "b3" : [1750, 17, 1.7, 0.5, 4, 5], "b2" : [1850, 20, 4, 0.6, 3, 2.5], "b1" : [10000, 100, 100, 100, 0, 0]}
    profils = get_profils(file_path = params.profils_file)
    
    #aliments = {"okok" : [1, 1, 1, 1, 1, 1], 'eru': [1, 1, 1, 1, 1, 1]}
    aliments = get_profils(file_path = params.aliments_file)
    #print(aliments)
       
    # experiments
    profils = {k : v for k, v in sorted(profils.items(), key=lambda b : b[0], reverse = True)} # se rassurer qu'on part de b6 à b1
    categories = sorted(categories, key = lambda c : c, reverse = False) # se rassurer qu'on part de A à E
    
    # Étape 1 : Détermination des indices de concordance partiels
    c = get_indices_de_concordance_partiels(criteres = criteres, aliments = aliments, profils = profils)
    #print(c)
    
    # Détermination des indices de concordance globaux
    C =  get_indices_de_concordance_globaux(n = len(criteres), indices_de_concordance_partiels = c, proids = poids)
    #print(C)
    
    # relation de surclassement & Procédures d’affectation
    categotiries_pessimist = PessimisticmajoritySorting(categories = categories, aliments = aliments, profils = profils, indices_de_concordance_globaux = C, seuil_de_majorite = seuil_de_majorite) 
    categotiries_optimist = OptimisticmajoritySorting(categories = categories, aliments = aliments, profils = profils, indices_de_concordance_globaux = C, seuil_de_majorite = seuil_de_majorite)

    #print(categotiries_pessimist)
    #print(categotiries_optimist)
    
    to_excel(categotiries_pessimist, params.output_file, "categotiries_pessimistes")
    to_excel(categotiries_optimist, params.output_file, "categotiries_optimistes")
