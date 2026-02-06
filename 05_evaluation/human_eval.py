import csv
from scipy.stats import binomtest

countall = 0
countright = 0
countleft = 0
countcocos = 0

with open("pilot.csv", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    reader.__next__()
    for row in reader:
        countall += 1
        if "/static/cocos_images/" in row[4]:
            countcocos += 1
        if row[5] == "right":
            countright += 1
        elif row[5] == "left":
            countleft += 1
        else:
            print(row[5])

print(f"Total evaluations: {countall}")
print(f"Total rigth: {countright} = {countright/countall:%}")
print(f"Total left: {countleft} = {countleft/countall:%}")
print(f"Total cocos: {countcocos} = {countcocos/countall:%}")

print("\nTesting for cocos preference:")
cocos_test = binomtest(k=countcocos, n=countall, p=0.5, alternative='greater')
print(f"One-sided binomial test p-value = {cocos_test.pvalue}")
print(f"Clopper-Pearson 95% CI: {cocos_test.proportion_ci(confidence_level=0.95)}")

print("\nTesting for left preference:")
position_test = binomtest(k=countleft, n=countall, p=0.5, alternative='greater')
print(f"One-sided binomial test p-value = {position_test.pvalue}")
print(f"Clopper-Pearson 95% CI: {position_test.proportion_ci(confidence_level=0.95)}")