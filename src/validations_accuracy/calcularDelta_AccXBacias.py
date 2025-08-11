import pandas as pd
import math

pathAccCol8 = "Accuracia_global_XBacia_col8.csv"
pathAccCol7 = "Accuracia_global_XBacia_col7.csv"
dfCol8Acc = pd.read_csv(pathAccCol8)
dfCol7Acc = pd.read_csv(pathAccCol7)
dfCol8Acc.columns = ['Index', 'Bacia', 'Accuracia_Col8', 'NumPoints', 'years']
dfCol7Acc.columns = ['Index', 'Bacia', 'Accuracia_Col7', 'NumPoints', 'years']
dfCol8Acc['Bacia'] = dfCol8Acc['Bacia'].astype(int)
dfCol8Acc['years'] = dfCol8Acc['years'].astype(int)
dfCol8Acc['NumPoints'] = dfCol8Acc['NumPoints'].astype(int)
print(dfCol8Acc.columns)
print(dfCol7Acc.head())
print(" ")
print(dfCol8Acc.head())

def set_columns(row):
    year = row['years']
    bacia = row['Bacia']
    acc = dfCol7Acc[(dfCol7Acc['Bacia'] == bacia) & (dfCol7Acc['years'] == year)]['Accuracia_Col7']
    #print("bacia ", bacia, " years ", year, " acc ", acc)
    row['Accuracia_Col7'] = acc.iloc[0]
    row["delta"]= math.fabs(row['Accuracia_Col7'] - row['Accuracia_Col8'])    
    return row

dfCol8Acc = dfCol8Acc.apply(set_columns, axis= 1)
# dfCol8Acc['Accuracia_Col7'] = dfCol7Acc['Accuracia_Col7']
print(" === ATUALIZADO ===")
print("   ", dfCol8Acc.head())


dfCol8Acc['years'] = dfCol8Acc['years'].astype(int)
dfGeral = dfCol8Acc[dfCol8Acc['years'] == 1985][['Index', 'Bacia', 'Accuracia_Col7', 'Accuracia_Col8', "delta", 'NumPoints', 'years']]
dfGeral.columns = [['Index', 'Bacia', 'Acc_C71_1985', 'Acc_C8_1985', "delta_1985", 'NumPoints', 'years']]

print("novo dataframe\n", dfGeral.head())


for nyear in range(1986, 2022):
    col8year = 'Acc_C8_' + str(nyear)
    col7year = 'Acc_C71_' + str(nyear)
    deltayear = 'delta_' + str(nyear)
    dfGeral[col8year] = dfCol8Acc[dfCol8Acc['years'] == nyear]['Accuracia_Col8'].tolist()
    dfGeral[col7year] = dfCol8Acc[dfCol8Acc['years'] == nyear]['Accuracia_Col7'].tolist()
    dfGeral[deltayear] = dfCol8Acc[dfCol8Acc['years'] == nyear]['delta'].tolist() 
    #print("serie to numpy")
    #print(dfCol8Acc[dfCol8Acc['years'] == nyear]['Accuracia_Col8'].tolist())
    #break

print("dfGeral  ", dfGeral.columns)

dfGeral['Bacia'] = dfGeral['Bacia'].astype(int)
dfGeral['years'] = dfGeral['years'].astype(int)
dfGeral['NumPoints'] = dfGeral['NumPoints'].astype(int)
print(dfGeral.head())
dfGeral.to_csv("Accuracia_Global_XBacia_XYears_Col8.csv")