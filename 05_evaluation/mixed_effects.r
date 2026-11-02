library(lme4)
library(emmeans)
library(dplyr)
library(sandwich)

df <- read.csv("sessions.csv") %>%
  mutate(
    session_id  = factor(session_id),
    category    = factor(category),
    winner_left = as.integer(position == "left"),
    pictcl_left     = ifelse(win == 1, winner_left, 1 - winner_left),
    pos         = pictcl_left - 0.5                              # centered: intercept = balanced positions
  )


ctrl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))

# ---------------------------------------------------------------
# 1) OVERALL PREFERENCE
# ---------------------------------------------------------------
m_overall <- glmer(win ~ pos + (1 | session_id),
                   data = df, family = binomial, control = ctrl)
summary(m_overall)

v <- as.numeric(VarCorr(m_overall)$session_id)
icc <- v / (v + pi^2/3)
cat(sprintf("\nParticipant ICC = %.4f\n", icc))
g <- glm(win ~ 1, data = df, family = binomial)
se_naive   <- sqrt(vcov(g)[1, 1])
se_cluster <- sqrt(vcovCL(g, cluster = df$session_id)[1, 1])
deff <- (se_cluster / se_naive)^2          # empirical design effect
cat(sprintf("Empirical design effect: %.4f\n\n", deff))

# Intercept = log-odds of preferring pictcl at balanced position
# (its Wald z-test is the test against a 50% win rate)
b  <- fixef(m_overall)["(Intercept)"]
ci <- confint(m_overall, parm = "beta_", method = "Wald")["(Intercept)", ]
cat(sprintf("Overall win prob: %.3f [%.3f, %.3f]\n",
            plogis(b), plogis(ci[1]), plogis(ci[2])))

# Position bias: odds ratio of pictcl winning when shown on the left vs right
exp(cbind(OR = fixef(m_overall)["pos"],
          confint(m_overall, parm = "pos", method = "Wald")))

# Between-participant variability
vc <- as.data.frame(VarCorr(m_overall))
cat("Participant SD (logit scale):", sqrt(vc$vcov[1]), "\n")

# ---------------------------------------------------------------
# 2) PER-CATEGORY PREFERENCE (one model, one intercept per category)
# ---------------------------------------------------------------
m_cat <- glmer(win ~ 0 + category + pos + (1 | session_id),
               data = df, family = binomial, control = ctrl)
summary(m_cat)

# Estimated win probability per category at balanced position, tested against 50%
emm <- emmeans(m_cat, ~ category, at = list(pos = 0))

res <- as.data.frame(confint(emm, type = "response", adjust = "none"))   # prob + CI
tst <- as.data.frame(test(emm, null = 0, adjust = "none"))                # z-test on logit scale
res$p_raw  <- tst$p.value
res$p_holm <- p.adjust(res$p_raw, method = "holm")
res$n      <- as.integer(table(df$category)[as.character(res$category)])
print(res[order(res$p_raw), ], digits = 3)

# Do categories differ from each other? (likelihood-ratio test)
m_cat1 <- glmer(win ~ category + pos + (1 | session_id),
                data = df, family = binomial, control = ctrl)
m_cat0 <- glmer(win ~ pos + (1 | session_id),
                data = df, family = binomial, control = ctrl)
anova(m_cat0, m_cat1)

# Pairwise category contrasts (odds ratios, Holm-adjusted)
pairs(emm, type = "response", adjust = "holm")

# ---------------------------------------------------------------
# 3) EXTENSIONS
# ---------------------------------------------------------------
# (a) Participants differ in their position bias (random slope).
m_slope <- glmer(win ~ pos + (1 + pos | session_id),
                 data = df, family = binomial, control = ctrl)
isSingular(m_slope)

# (b) Participants differ in category preference (maximal model; often singular)
m_cat_slope <- glmer(win ~ category + pos + (1 + category | session_id),
                     data = df, family = binomial, control = ctrl)

# (c) If the same image pairs were shown to several participants, add a crossed effect
#     (needs a pair_id column):
# m_cross <- glmer(win ~ pos + (1 | session_id) + (1 | pair_id),
#                  data = df, family = binomial, control = ctrl)

# (d) Sanity check without modeling: participant-level aggregation
per_user <- df %>% group_by(session_id) %>% summarise(p = mean(win))
wilcox.test(per_user$p, mu = 0.5)