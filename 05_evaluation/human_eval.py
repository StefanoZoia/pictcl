import csv
from scipy.stats import binomtest
from matplotlib import pyplot as plt
import numpy as np

sessions = dict()

with open("human_eval_results/evaluation-kr-2026-02-13-15-40.csv", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    reader.__next__()
    for row in reader:
        session_id = row[1]
        winner_image = row[4]
        winner_position = row[5]

        if session_id not in sessions:
            sessions[session_id] = list()

        sessions[session_id].append({"winner": winner_image, "position": winner_position})

i = 0

trusted_sessions = dict()
for s in sessions:
    answers = sessions[s]
    i += len(answers)
    trusted = len(answers) >= 30
    
    for a in answers:
        if "/static/control_losers" in a["winner"]:
            trusted = False
    if trusted:
        trusted_sessions[s] = sessions[s]
        
print(i)
print(len(trusted_sessions))

i = 0
count_cocos = 0
count_baseline = 0        
count_ooc_cocos = 0
count_ooc_baseline = 0
count_left = 0
count_right = 0

for s in trusted_sessions:
    for curr_ans in trusted_sessions[s]:
        i+=1
        if "/static/control_" not in curr_ans["winner"]:
            if "/static/cocos_images" in curr_ans["winner"]:
                count_cocos += 1
                if "ooc_" in curr_ans["winner"]:
                    count_ooc_cocos += 1
            elif "/static/images" in curr_ans["winner"]:
                count_baseline += 1
                if "ooc_" in curr_ans["winner"]:
                    count_ooc_baseline += 1
            else:
                print(curr_ans["winner"])

            if "right" in curr_ans["position"]:
                count_right += 1
            elif "left" in curr_ans["position"]:
                count_left += 1
            else:
                print(curr_ans["position"])



print(i)
count_imgs = count_cocos + count_baseline
count_ooc = count_ooc_cocos + count_ooc_baseline

print(f"Total evaluations: {count_imgs}")
print(f"Total rigth: {count_right} = {count_right/count_imgs:.2%}")
print(f"Total left: {count_left} = {count_left/count_imgs:.2%}")
print(f"Total cocos: {count_cocos} = {count_cocos/count_imgs:.2%}")

print("\nTesting for cocos preference:")
cocos_test = binomtest(k=count_cocos, n=count_imgs, p=0.5, alternative='greater')
print(f"One-sided binomial test p-value = {cocos_test.pvalue}")
print(f"Clopper-Pearson 95% CI: {cocos_test.proportion_ci(confidence_level=0.95)}")

print("\nTesting for right preference:")
position_test = binomtest(k=count_right, n=count_imgs, p=0.5, alternative='greater')
print(f"One-sided binomial test p-value = {position_test.pvalue}")
print(f"Clopper-Pearson 95% CI: {position_test.proportion_ci(confidence_level=0.95)}")


print(f"\nTotal object-object combination: {count_ooc}")
print(f"Total cocos on ooc: {count_ooc_cocos} = {count_ooc_cocos/count_ooc:.2%}")

print("\nTesting for cocos preference on ooc:")
ooc_cocos_test = binomtest(k=count_ooc_cocos, n=count_ooc, p=0.5, alternative='greater')
print(f"One-sided binomial test p-value = {ooc_cocos_test.pvalue}")
print(f"Clopper-Pearson 95% CI: {ooc_cocos_test.proportion_ci(confidence_level=0.95)}")

'''
print("\nTesting for cocos improving on full mark score:")
ooc_cocos_test = binomtest(k=253, n=279, p=0.8889, alternative='greater')
print(f"One-sided binomial test p-value = {ooc_cocos_test.pvalue}")
print(f"Clopper-Pearson 95% CI: {ooc_cocos_test.proportion_ci(confidence_level=0.95)}")

print("\nTesting for cocos improving on concept fraction score:")
ooc_cocos_test = binomtest(k=531, n=558, p=0.9427, alternative='greater')
print(f"One-sided binomial test p-value = {ooc_cocos_test.pvalue}")
print(f"Clopper-Pearson 95% CI: {ooc_cocos_test.proportion_ci(confidence_level=0.95)}")'''


plt.rcParams.update({'font.size': 15})

subset = ("Overall", "Object combinations")
scores = {
    'Baseline': (count_baseline/count_imgs*100, count_ooc_baseline/count_ooc*100),
    r'$\mathregular{T^{CL}}$': (count_cocos/count_imgs*100, count_ooc_cocos/count_ooc*100),
}

x = np.arange(len(subset))  # the label locations
width = 0.3  # the width of the bars
multiplier = 0

fig, ax = plt.subplots(layout='constrained')

for system, score in scores.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, score, width, label=system)
    ax.bar_label(rects, padding=3, fmt=lambda x: f'{round(x, 2)}%')
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Preferences')
#ax.set_title('System preferences')
n_cols = len(scores)
ax.set_xticks(x + ((n_cols - 1) * width/2), subset)
ax.legend(loc='upper center', ncols=n_cols)
ax.set_ylim(0,65)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
#ax.spines['bottom'].set_visible(False)
ax.get_yaxis().set_ticks([])

plt.savefig("human-eval.pdf")
plt.show()
