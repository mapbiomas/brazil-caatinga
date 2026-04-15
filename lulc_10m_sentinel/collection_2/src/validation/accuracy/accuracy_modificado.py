import glob
import pandas as pd 
import sys
import math
import warnings
import os
from os import path, makedirs
import csv
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import confusion_matrix, precision_score, recall_score, accuracy_score, f1_score
from sklearn.utils.multiclass import unique_labels
import DictClass

input_dir = "csv_stat/"
output_dir = 'OUTPUT'
pointsAcc = "occTab_corr_Caatinga_class_filtered_Tp_V5.csv"
#version = 'v5'
STRATA_FILE = 'strataCaatinga.csv'
input = os.getcwd()
pos = input.rfind('/')
input_dir = os.path.join(input[:pos], input_dir)


path_acc = 'acuracy_' + pointsAcc[11:]
input_dirAcc = os.path.join(input_dir, path_acc)
arq_acc = open(input_dirAcc, 'w+')
arq_acc.write('nivel;ano;acuracia;erro_comissao;erro_omissao\n')

IGNORED_CLASSES = [0,31,32,30,25,23,5,29]
ALL_CLASSES = DictClass.ALL_CLASSES

def get_classes(df_tmp, level='l3'):

	class_values = {}
	class_names = {}

	clas_classes = pd.Index(df_tmp['classification'].unique())
	ref_classes = pd.Index(df_tmp['reference'].unique())

	acc_classes = clas_classes.intersection(ref_classes)

	val_remap = {}
	# consultado as classes do diccionario de classes 
	for value in ALL_CLASSES.keys():
		
		if (value not in IGNORED_CLASSES and (value in acc_classes)):
			
			val_key = "%s_val" % (level)
			new_val = ALL_CLASSES[value][val_key]
			class_name = ALL_CLASSES[value][level]

			val_remap[value] = new_val
			class_values[new_val] = True
			class_names[class_name] = True

	df_tmp = df_tmp[df_tmp['classification'].isin(val_remap.keys())]
	df_tmp = df_tmp[df_tmp['reference'].isin(val_remap.keys())]

	df_tmp['classification'] = df_tmp['classification'].map(val_remap)
	df_tmp['reference'] = df_tmp['reference'].map(val_remap)
	class_values = list(class_values.keys())
	class_names = list(class_names.keys())

	return df_tmp, class_values, class_names


def set_all_sum_of_matrix_acc(matrix_acc):

	dimension = int(math.sqrt(matrix_acc.size))
	
	matrix_a = np.zeros((dimension + 1, dimension + 1)).astype(np.int32)
	
	matrix_a[0:dimension, 0: dimension] = matrix_acc

	for ii in range(dimension):

		matrix_a[ii, dimension] = np.sum(matrix_a[ii, : dimension])
		matrix_a[dimension, ii] = np.sum(matrix_a[ :dimension, ii])

	matrix_a[dimension, dimension] = np.sum(matrix_a[0:dimension, 0:dimension])

	print(matrix_a)
	return matrix_a, dimension


def classification_report_shinny(df_temp, class_names, class_values, year):	
	
	result = []
	result_glob = []

	y_true = df_temp[['reference']].to_numpy().flatten()
	y_pred = df_temp[['classification']].to_numpy().flatten()
	# sample_weight = 1 / df_temp[['prob_amos']].to_numpy().flatten()

	# descartando o pesso das classes de 
	matrixC = confusion_matrix(y_true, y_pred) # sample_weight=sample_weight, 
	# print("matrix da funssão ", matrixC)
	# recalculando a matriz de acurracia 
	matrix, num_classes = set_all_sum_of_matrix_acc(matrixC)	
	glob_acc = global_acc(matrix, num_classes)	

	"years; global_accuracy; error_comission; error_omission;  quantity_diss ; alloc_dis ; exchange; shift\n"
	print("acuracia global ", glob_acc)	
	text_gb = str(year) + ';' + str(glob_acc) + ';'
	
	user_acc, prod_acc, user_err, prod_err, erro_comissao, erro_omissao = user_prod_acc_err(matrix, num_classes)
	text_gb += str(erro_comissao) + ';' + str(erro_omissao) + ';'

	quantid, allocat, exchange, shift = allocation_erros(matrix, num_classes)
	
	#  quantity_diss ; alloc_dis ; exchange; shift
	mcalc = np.round_(sum(quantid) / 2, decimals= 2)
	text_gb += str(mcalc) + ';'

	mcalc = glob_acc - mcalc
	text_gb += str(mcalc) + ';'

	mcalc = np.round_(sum(exchange) / 2, decimals= 2)
	text_gb += str(mcalc) + ';'

	mcalc = np.round_(sum(shift) / 2, decimals= 2)
	text_gb += str(mcalc) + '\n'
	
	result_glob.append(text_gb)

	for ii in range(num_classes):

		texto = str(year) + ';'
		texto += class_names[ii] + ';'
		
		# addicionando os valores das classes 
		for jj in range(num_classes):
			texto += str(matrix[ii, jj]) + ';'
	
		texto += str(matrix[ii, num_classes]) + ';'
		texto += str(user_acc[ii]) + ';'
		texto += str(prod_acc[ii]) + ';'
		texto += str(user_err[ii]) + ';'
		texto += str(prod_err[ii]) + ';'
		texto += str(quantid[ii]) + ';'
		texto += str(allocat[ii]) + ';'
		texto += str(exchange[ii]) + ';'
		texto += str(shift[ii]) + '\n'
		print(texto)
		result.append(texto)

	texto = str(year) + "; producer's total; "
	for ii in range(num_classes):
		texto += str(matrix[num_classes, ii]) + ';'
	texto += str(matrix[num_classes, num_classes])
	texto +=  "; NA; NA; NA; NA; NA; NA; NA; NA \n"
	result.append(texto)

	return result, result_glob


def save_csv(output_filename, data):

	output_file = open(output_filename, mode='w')  
	print("Generating " + 'accMetricas_' + pointsAcc[11:])
	# print(type(data))
	
	for file in data:				
		output_file.write(file)
	output_file.close()

def calculate_prob(df):

	print("-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-")
	print("--- building probability of class ---")
	print("-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*- \n")

	strata = pd.read_csv(input_dir + STRATA_FILE)
	df = pd.merge(df, strata, how='inner', on="bacia")
	print(df.head(3))
	samples = df['bacia'].value_counts().rename_axis('bacia').reset_index(name='n_samp')
	df = pd.merge(samples, df, on='bacia')
	df['prob_amos'] = df['n_samp'] / df['pop']

	return df

def mkdirp(path):
	try:
		makedirs(path)
	except:
		pass

def accuracy_assessment_all(df, biome='BRASIL'):
	
	level = 'l3'

	try:
		makedirs(output_dir)
	except:
		pass

	output_filename = path.join(output_dir, ''.join(['acc_caat_', pointsAcc]))
	output_filename_glob = path.join(output_dir, ''.join(['acc_caat_glob', pointsAcc]))

	years = [ kk for kk in df['year'].unique()]
	years.sort()
	result = []	
	header = 'years; class_names;'
	header_glob = "years; global_accuracy; error_comission; error_omission;  quantity_diss ; alloc_dis ; exchange; shift\n"
	result_global = [header_glob]
	
	years = ['Todos'] + years
	# print("anos com dados ", years)
	#years = [2018] #, 'Todos'
	# print(type(years))
	
	for cc, year in enumerate(years):
		
		new_df = df.copy(deep=True)
		# print(" com {} ".format(new_df.shape))
		
		if year != 'Todos':			
			new_df = new_df[new_df['year'] == year].copy(deep=True)
			
		# tratando as classes salvas e exportando um novo dataframe
		new_df, class_values, class_names = get_classes(new_df, level)

		if cc == 0:
			for nn in class_values:
				header += 'class_' + str(nn) + ';'
			header += "user's total ; user's accuracy ; producer's accuracy;"
			header += "error comission; error omission; quantity diss ; alloc dis ; exchange; shift\n"
			print(header)
			result.append(header)
		
		print("year {} com {} ".format(year, new_df.shape))
		temporal, result_years = classification_report_shinny(new_df, class_names, class_values,  year)
		
		result += temporal
		result_global += result_years

	save_csv(output_filename, result)
	save_csv(output_filename_glob, result_global)

def population_estimation(df):
	sample_weight = 1 / df[['prob_amos']].to_numpy().flatten()
	return sample_weight.sum()

def covariance(x, y):
	
	if x.size < 1:
		x_mean = np.mean(x)
		y_mean = np.mean(y)

		return np.sum((x - x_mean) * (y - y_mean) / (x.size - 1))
	else:
		return 0.0

def user_prod_se(df, class_val, user_acc, prod_acc, map_total, ref_total):
	
	user_var = 0
	prod_var = 0

	user_se = 0
	prod_se = 0

	for name, df_strata in df.groupby('bacia'):
		
		ref_val_s = df_strata['reference'].to_numpy()
		map_val_s = df_strata['classification'].to_numpy()

		map_total_s = np.where((map_val_s == class_val), 1, 0)
		map_correct_s = np.where(np.logical_and((map_val_s == class_val),(map_val_s == ref_val_s)), 1, 0)

		ref_total_s = np.where((ref_val_s == class_val), 1, 0)
		ref_correct_s = np.where(np.logical_and((ref_val_s == class_val),(map_val_s == ref_val_s)), 1, 0)
		
		nsamples_s, _ = df_strata.shape
		population_s = population_estimation(df_strata)

		user_var += math.pow(population_s,2) * (1 - nsamples_s/population_s) \
									* ( math.pow(	np.var(map_correct_s) , 2) \
											+ user_acc * math.pow( np.var(map_total_s) , 2) \
											- 2 * user_acc * covariance(map_total_s, map_correct_s) \
 										) / nsamples_s

		prod_var += math.pow(population_s,2) * (1 - nsamples_s/population_s) \
									* ( math.pow(	np.var(ref_correct_s) , 2) \
											+ prod_acc * math.pow( np.var(ref_total_s) , 2) \
											- 2 * prod_acc * covariance(ref_total_s, ref_correct_s) \
 										) / nsamples_s

	if (map_total !=0):
		user_var = 1 / math.pow(map_total,2) * user_var
		user_se = 1.96 * math.sqrt(user_var)
		user_se = round(user_se, 6)

	if (ref_total !=0):
		prod_var = 1 / math.pow(ref_total,2) * prod_var
		prod_se = 1.96 * math.sqrt(prod_var)
		prod_se = round(prod_se, 6)

	return user_se, prod_se

def global_se(df, mask, population):
	glob_var = 0

	for name, df_strata in df.groupby('bacia'):
		ref_val_s = df['reference'].to_numpy()
		map_val_s = df['classification'].to_numpy()

		map_correct_s = np.where( mask, 1, 0)

		nsamples_s, _ = df_strata.shape
		population_s = population_estimation(df_strata)
		glob_var += math.pow(population_s,2) * (1 - nsamples_s/population_s) \
								* np.var(map_correct_s) / nsamples_s

	glob_var = 1 / math.pow(population,2) * glob_var
	glob_se = 1.96 * math.sqrt(glob_var)

	glob_se = round(glob_se, 6)

	return glob_se

def calc_map_bias(df, class_values):

	map_bias_arr = []
	map_bias_se_arr = []

	ref_val = df['reference'].to_numpy()
	map_val = df['classification'].to_numpy()
	samp_weight = 1 / df['prob_amos'].to_numpy()

	population = population_estimation(df)

	for class_val in class_values:
	
		map_mask = np.logical_and((map_val == class_val), (ref_val != class_val))
		map_comission_prop = np.sum(np.where(map_mask, 1, 0) * samp_weight) / population

		ref_mask = np.logical_and((ref_val == class_val), (map_val != class_val))
		map_omission_prop = np.sum(np.where(ref_mask, 1, 0) * samp_weight) / population

		map_bias = (map_omission_prop - map_comission_prop)
		
		se_mask = np.logical_xor(ref_mask,map_mask)
		map_bias_se = global_se(df, se_mask, population)

		map_bias_arr.append(map_bias)
		map_bias_se_arr.append(map_bias_se)

	return map_bias_arr, map_bias_se_arr

def refarea_pop(df, class_values):

	refarea_prop_arr = []
	refarea_se_arr = []

	ref_val = df['reference'].to_numpy()
	map_val = df['classification'].to_numpy()
	samp_weight = 1 / df['prob_amos'].to_numpy()

	population = population_estimation(df)

	for class_val in class_values:
	
		ref_mask = (ref_val == class_val)
		refarea = np.sum(np.where(ref_mask, 1, 0) * samp_weight)

		refarea_prop = (refarea / population)
		refarea_se = global_se(df, ref_mask, population)

		refarea_prop_arr.append(refarea_prop)
		refarea_se_arr.append(refarea_se)

	return refarea_prop_arr, refarea_se_arr

def global_acc(mat_conf, dim):

	suma = 0
	for ii in range(dim):
		suma += mat_conf[ii, ii]
	# print(suma)
	return np.round_((suma / mat_conf[dim, dim]) * 100, decimals=2)

def user_prod_acc_err(mat_conf, dim):

	user_acc_arr = []
	prod_acc_arr = []
	user_err_arr = []
	prod_err_arr = []	

	suma_com = 0
	suma_omi = 0

	for ii in range(dim):
		# print("valor central ", mat_conf[ii, ii])
		# print("valor suma ",  mat_conf[ii, dim])
		calc = np.round_((mat_conf[ii, ii] / mat_conf[ii, dim]) * 100, decimals= 2)
		user_acc_arr.append(calc)
		user_err_arr.append(100 - calc)		
		
		calc = np.round_((mat_conf[ii, ii] / mat_conf[dim, ii]) * 100, decimals= 2)
		prod_acc_arr.append(calc)
		prod_err_arr.append(100 - calc)
		
		if ii < dim:
			# print(mat_conf[ii, ii + 1: dim])
			suma_com += np.sum(mat_conf[ii, ii + 1: dim]) 
			# print(suma_com)
			suma_omi += np.sum(mat_conf[ii + 1: dim, ii])

	# print("suma total ", mat_conf[dim, dim])
	# print("suma comisao ", suma_com)
	# print("suma omisao ", suma_omi)

	erro_com = np.round_((suma_com / mat_conf[dim, dim]) * 100, decimals= 2)
	erro_omi = np.round_((suma_omi / mat_conf[dim, dim]) * 100, decimals= 2)

	return user_acc_arr, prod_acc_arr, user_err_arr, prod_err_arr, erro_com, erro_omi

def allocation_erros (mat_conf, dim):

	quantid_arr = []
	allocat_arr = []
	exchange_arr = []
	shift_arr = []	
	total = mat_conf[dim, dim]

	for ii in range(dim):
		# calculo do erro de quantidade
		dif_user_prod = abs(mat_conf[ii,dim] - mat_conf[dim, ii])
		calc = np.round_((dif_user_prod/ total) * 100, decimals= 2)
		quantid_arr.append(calc)

		# calculo do erro de Allocação 
		dif_min = 2 * min((mat_conf[ii,dim] - mat_conf[ii, ii]), (mat_conf[dim, ii] - mat_conf[ii, ii]))
		calc = np.round_((dif_min/ total) * 100, decimals= 2)
		allocat_arr.append(calc)
		
		# calculo dos erros de exchange
		suma = 0
		sum_dif = 0		
		for jj in range(dim):
			if ii != jj:
				suma += min(mat_conf[ii, jj], mat_conf[jj, ii])
				sum_dif += abs(mat_conf[ii, jj] - mat_conf[jj, ii])
		
		calc = np.round_(((suma * 2)/total) * 100, decimals= 2)
		exchange_arr.append(calc)

		# calculo do erro de shift
		calc = np.round_(((sum_dif - dif_user_prod)/total) * 100, decimals= 2)
		shift_arr.append(calc)

	return quantid_arr, allocat_arr, exchange_arr, shift_arr 

def config_class_21(df):
	agro_filter = (df['classification'] == 21) & (df['reference'].isin([15,19,20]))
	df.loc[agro_filter, 'reference'] = 21

	return df

df_csv = pd.read_csv(input_dir + pointsAcc)
print("Reading " + pointsAcc, df_csv.shape)
df_csv['system:index'] = df_csv.index
print(df_csv.columns)
df = calculate_prob(df_csv)

total_points = population_estimation(df)

df = config_class_21(df)


accuracy_assessment_all(df)