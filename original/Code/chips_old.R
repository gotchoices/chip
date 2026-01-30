# Install packages

# install.packages("pwt10") # uncomment for the first time use 
# install.packages("vtable") # uncomment for the first time use 
# install.packages("tidyverse")  uncomment for the first time use 
# install.packages("ggplot2") # uncomment for the first time use 
# install.packages("ggrepel") # uncomment for the first time use 
# install.packages("readxl") # uncomment for the first time use 
# install.packages("mice") # uncomment for the first time use 
# install.packages("stringr") # uncomment for the first time use 
# install.packages("fixest") # uncomment for the first time use 
# install.packages("lubridate") # uncomment for the first time us

# Load R libraries 

library(pwt10)
library(mice)
library(lubridate)
library(dplyr)
library(readr)
library(tidyr)
library(vtable)
library(ggplot2)
library(ggrepel)
library(readxl)
library(stringr)
library(fixest)

# Set path 

setwd("../Data")  # Relative path from Code/ to Data/

# Load data 

data("pwt10.0") # from PWT10 API 
employment <- read_csv("employment.csv")
wages <- read_csv("wages.csv")
hoursworked <- read_csv("hoursworked.csv")
fcslist <- read_excel("fcslist.xlsx", sheet = "Data")
freedomindex <- read_excel("freedomindex.xlsx", sheet = "EFW Data 2022 Report", skip = 4)
GDPDEF <- read_csv("GDPDEF.csv")

# Clean and reshape data 

GDPDEF <- GDPDEF %>%
  rename(Date = 1, GDPDEF =2) %>%
  mutate(Year = year(Date)) %>%
  select(-"Date")

def2017base <- GDPDEF[which(GDPDEF$Year==2017), ] %>%
  select(GDPDEF)
def2017base <- as.numeric(def2017base)

def2021base <- GDPDEF[which(GDPDEF$Year==2021), ] %>%
  select(GDPDEF)
def2021base <- as.numeric(def2021base)  

GDPDEF <- GDPDEF %>%
  mutate(GDPDEF2017 = GDPDEF/def2017base,
         GDPDEF2021 = GDPDEF/def2021base)

# The lines below process Heritage freedom index and 
# the World Bank list of fragile economies 
# While these data weren't used in the final analysis 
# It can be used in further research to test robustness of 
# CHIP value estimates across different country groups

fcslist1 <- fcslist %>%
  pivot_longer(cols = starts_with("y"),
               names_to = "year",
               names_prefix = "y",
               values_to = "Fragile",
               values_drop_na = TRUE) %>%
  rename(Country = 1, Code =2, Region =3, Income_Group = 4, Year = 5) %>%
  mutate(Year = as.numeric(Year))

freedomindex1 <- freedomindex %>%
  select(c(1, 3:6)) %>%
  rename(Code = 2, Country = 3, F_Index = 4, F_Rank = 5)
  
indices <- fcslist1 %>%
  left_join(freedomindex1, by=c("Code", "Year")) %>%
  select(-Country.y) %>%
  rename(Country = 1)

# Clean ILOSTAT data 

employment <- employment %>%
  select(c(1,4:7)) %>%
  rename(Country = 1, Sex = 2, Skill = 3, Year = 4, Employed = 5) %>%
  filter(Sex == "Sex: Total") %>%
  select(-c(2)) %>% 
  filter(Skill != "Occupation (Skill level): Not elsewhere classified", 
         Skill != "Occupation (ISCO-88): 0. Armed forces",
         Skill != "Occupation (ISCO-68): AF. Armed Forces",
         Skill != "Occupation (ISCO-08): 0. Armed forces occupations",
         Skill != "Occupation (ISCO-88): X. Not elsewhere classified",
         Skill != "Occupation (ISCO-68): X. Not elsewhere classified",
         Skill != "Occupation (ISCO-08): X. Not elsewhere classified",
         Skill != "Occupation (ISCO-08): Total",
         Skill != "Occupation (ISCO-68): Total",
         Skill != "Occupation (ISCO-88): Total") %>%
  mutate(Skill =  ifelse(Skill == "Occupation (Skill level): Total", 
                         "Occupation: Total", Skill))

hoursworked <- hoursworked %>%
  select(c(1,4:7)) %>%
  rename(Country = 1, Sex = 2, Skill = 3, Year = 4, Hours = 5) %>%
  filter(Sex == "Sex: Total") %>%
  select(-c(2)) %>% 
  filter(Skill != "Occupation (Skill level): Not elsewhere classified", 
         Skill != "Occupation (ISCO-08): 0. Armed forces occupations",
         Skill != "Occupation (ISCO-08): X. Not elsewhere classified", 
         Skill != "Occupation (ISCO-08): Total") %>%
  mutate(Skill =  ifelse(Skill == "Occupation (Skill level): Total", 
                         "Occupation: Total", Skill))
wages <- wages %>%
  select(c(1,4:8)) %>%
  rename(Country = 1, Sex = 2, Skill = 3, Currency = 4, Year = 5, Wage = 6) %>%
  filter(Sex == "Sex: Total") %>%
  select(-c(2)) %>% 
  filter(Skill != "Occupation (ISCO-88): 0. Armed forces",
         Skill != "Occupation (ISCO-88): X. Not elsewhere classified") %>%
  mutate(Skill =  ifelse(Skill == "Occupation (ISCO-88): Total", 
                         "Occupation: Total", Skill))

# Rebase real wage data to 2021

wages_USD <- wages %>%
  filter(Currency == "Currency: U.S. dollars") %>%
  select(-"Currency") %>%
  left_join(GDPDEF, by = "Year") %>%
  mutate(Wage = Wage / GDPDEF2017, Wage2021 = Wage/GDPDEF2021) %>%
  select(-c("GDPDEF", "GDPDEF2017", "GDPDEF2021"))

wages_PPP <- wages %>%
  filter(Currency == "Currency: 2017 PPP $") %>%
  select(-"Currency") 

PPPF <- wages_USD %>%
  left_join(wages_PPP, by = c("Country", "Year", "Skill")) %>%
  filter(grepl('Elementary', Skill)) %>%
  filter(!(Country=="Albania"&Year ==2012)) %>% #remove crazy values / outliers
  filter(!is.na(Wage.y)) %>%
  mutate(PPPF = Wage.y / Wage.x) %>%
  select(Country, Year, PPPF) 

# Merge and Standartize Labor data 

labordata <- employment %>% 
  left_join(hoursworked, by = c("Country", "Year", "Skill")) %>%
  left_join(wages_USD, by = c("Country", "Year", "Skill")) %>%
  arrange(Country,Year,Skill) %>%
  mutate(Skill = case_when(Skill == "Occupation (ISCO-08): 1. Managers" ~ "Managers", 
                   Skill == "Occupation (ISCO-08): 2. Professionals" ~ "Professionals",
                   Skill == "Occupation (ISCO-08): 3. Technicians and associate professionals" ~ "Technicians",
                   Skill == "Occupation (ISCO-08): 4. Clerical support workers" ~ "Clerks",
                   Skill == "Occupation (ISCO-08): 5. Service and sales workers" ~ "Salesmen",
                   Skill == "Occupation (ISCO-08): 6. Skilled agricultural, forestry and fishery workers" ~ "Agforestry",
                   Skill == "Occupation (ISCO-08): 7. Craft and related trades workers" ~"Craftsmen",
                   Skill == "Occupation (ISCO-08): 8. Plant and machine operators, and assemblers" ~ "Operators",
                   Skill == "Occupation (ISCO-08): 9. Elementary occupations" ~ "Elementary",
                   Skill == "Occupation: Total" ~ "Total",
                   Skill == "Occupation (ISCO-68): 2. Administrative and managerial workers" ~ "Managers", 
                   Skill == "Occupation (ISCO-68): 0/1. Professional, technical and related workers" ~ "Professionals",
                   Skill == "Occupation (ISCO-68): 3. Clerical and related workers" ~ "Clerks",
                   Skill == "Occupation (ISCO-68): 4. Sales workers" ~ "Sales68",
                   Skill == "Occupation (ISCO-68): 5. Service workers" ~ "Service68",                   
                   Skill == "Occupation (ISCO-68): 6. Agriculture, animal husbandry and forestry workers, fishermen and hunters" ~ "Agforestry",
                   Skill == "Occupation (ISCO-68): 7,8,9. Production and related workers, transport equipment operators and labourers" ~ "Operators",
                   Skill == "Occupation (ISCO-88): 1. Legislators, senior officials and managers" ~ "Managers", 
                   Skill == "Occupation (ISCO-88): 2. Professionals" ~ "Professionals",
                   Skill == "Occupation (ISCO-88): 3. Technicians and associate professionals" ~ "Technicians",
                   Skill == "Occupation (ISCO-88): 4. Clerks" ~ "Clerks",
                   Skill == "Occupation (ISCO-88): 5. Service workers and shop and market sales workers" ~ "Salesmen",
                   Skill == "Occupation (ISCO-88): 6. Skilled agricultural and fishery workers" ~ "Agforestry",
                   Skill == "Occupation (ISCO-88): 7. Craft and related trades workers" ~"Craftsmen",
                   Skill == "Occupation (ISCO-88): 8. Plant and machine operators and assemblers" ~ "Operators",
                   Skill == "Occupation (ISCO-88): 9. Elementary occupations" ~ "Elementary",
                   Skill == "Occupation (Skill level): Skill level 1 ~ low" ~ "LowSkilled",
                   Skill == "Occupation (Skill level): Skill level 2 ~ medium" ~ "MedSkilled",
                   Skill == "Occupation (Skill level): Skill levels 3 and 4 ~ high" ~ "HighSkilled"
                  )
         )


# Clean wage data
  
wagedata <- labordata %>%
  select(c(1,2,3,6)) %>%
  filter(is.na(Wage) ==FALSE) %>%
  filter(!(Country=="Ghana"&Year ==2017)) %>% #remove crazy values / outliers
  filter(!(Country=="Egypt"&Year ==2009)) %>% #remove crazy values / outliers
  filter(!(Country=="Rwanda"&Year ==2014)) %>% #remove crazy values / outliers
  filter(!(Country=="Congo, Democratic Republic of the"&Year ==2005)) %>% #remove crazy values / outliers
  filter(!(Country=="Côte d'Ivoire"&Year ==2019)) %>% #remove crazy values / outliers
  filter(!(Country=="Belize"&Year ==2017)) %>%  #remove crazy values / outliers
  filter(!(Country=="Cambodia")) %>% #remove crazy values / outliers
  filter(!(Country=="Lao People's Democratic Republic")) %>% #remove crazy values / outliers
  filter(!(Country=="Timor-Leste")) %>% #remove crazy values / outliers
  pivot_wider(names_from = Skill, values_from = Wage) 
 # left_join(indices, by=c("Country", "Year"))

# Calculate relative wages 

wageratdata <- wagedata %>% 
  mutate(Professionals = Professionals / Managers,
         Technicians = Technicians / Managers,
         Clerks = Clerks / Managers, 
         Salesmen = Salesmen / Managers,
         Agforestry = Agforestry / Managers,
         Craftsmen = Craftsmen / Managers,
         Operators = Operators / Managers,
         Elementary = Elementary / Managers) %>%
  select(-c("Managers", "Total")) %>%
  group_by(Country) %>%
  summarise(across(c(2:9), ~ mean(.x, na.rm = TRUE)))

# Summarize and plot relative wage data 

st(wageratdata)

# Plot Figure 1 

wrat_barchart <- wageratdata %>%
  summarise(across(c(2:9), ~ mean(.x, na.rm = TRUE))) %>%
  mutate(Managers = 1)
wrat_barchart <- wrat_barchart[, c(9, 1, 2, 3, 6, 7, 4, 5, 8)]
barplot(as.matrix(wrat_barchart), xlab="Skill Category",ylab="Skill Level",col="blue")

wageratdata1 <- wageratdata %>%
  select(-"Country")
boxplot(wageratdata1)
title("Wage Ratios to Managers across 115 countries")

# Impute missing values of wage ratios using MICE/OLS

imp <- mice::mice(wageratdata, method = "norm.predict", m = 1)
wageratdata_imp <- complete(imp)

wageratdata_long <- wageratdata_imp %>%
  mutate(Managers = 1) %>%
  pivot_longer(cols = !Country,
               names_to = "Skill",
               names_prefix = NULL,
               values_to = "Wrat",
               values_drop_na = TRUE) 

# Construct simple labor weights

labdata <- labordata %>%
  dplyr::filter(!grepl('LowSkilled|HighSkilled|MedSkilled|Total', Skill)) %>%
  select(-c("Wage", "Wage2021")) %>%
  mutate(Hours = ifelse(is.na(Hours) ==TRUE, 40, Hours)) %>%
  mutate(LaborHours = Employed * Hours) %>%
  select(-c("Employed", "Hours")) %>% 
  pivot_wider(names_from = Skill, values_from = LaborHours) %>%
  replace(is.na(.), 0) %>%
  mutate(Salesmen = ifelse(Salesmen ==0, Sales68 + Service68, Salesmen)) %>%
  select(-c("Sales68", "Service68")) %>%
  pivot_longer(cols = !c(1:2),
               names_to = "Skill",
               names_prefix = NULL,
               values_to = "LaborHours",
               values_drop_na = TRUE) 
  
  labtotal <- labdata %>%
  group_by(Country, Year) %>%
  summarise(LaborHours = sum(LaborHours)) %>%
  mutate(Skill = "Total")
  
  labweightdata <- base::rbind(labdata, labtotal) %>%
    pivot_wider(names_from = Skill, values_from = LaborHours) %>%  
    mutate(Managers = Managers / Total,
         Professionals = Professionals / Total,
         Technicians = Technicians / Total,
         Clerks = Clerks / Total, 
         Salesmen = Salesmen / Total,
         Agforestry = Agforestry / Total,
         Craftsmen = Craftsmen / Total,
         Operators = Operators / Total,
         Elementary = Elementary / Total) %>%
  select(-Total) %>%
  pivot_longer(cols = !c(1:2),
               names_to = "Skill",
               names_prefix = NULL,
               values_to = "LaborWeight",
               values_drop_na = TRUE) 


# Construct units of 'effective labor' 

efflabdata <- labordata %>%
  dplyr::filter(!grepl('LowSkilled|HighSkilled|MedSkilled|Total', Skill)) %>%
  select(-c("Wage", "Wage2021")) %>%
  mutate(Hours = ifelse(is.na(Hours) ==TRUE, 40, Hours)) %>%
  mutate(LaborHours = Employed * Hours) %>%
  select(-c("Employed", "Hours")) %>%
  pivot_wider(names_from = Skill, values_from = LaborHours) %>%
  replace(is.na(.), 0) %>%
  mutate(Salesmen = ifelse(Salesmen ==0, Sales68 + Service68, Salesmen)) %>%
  select(-c("Sales68", "Service68")) %>%
  pivot_longer(cols = !c(1:2),
               names_to = "Skill",
               names_prefix = NULL,
               values_to = "LaborHours",
               values_drop_na = TRUE) %>%
  left_join(wageratdata_long, by=c("Country", "Skill")) %>%
  mutate(Eff_Labor = LaborHours * Wrat) %>%
  select(-c("Wrat", "LaborHours")) 

efflabtotal <- efflabdata %>%
  group_by(Country, Year) %>%
  summarise(Eff_Labor = sum(Eff_Labor)) %>%
  mutate(Skill = "Total")

# Construct Effective Labor weights

efflabweight <- base::rbind(efflabdata, efflabtotal) %>%
  pivot_wider(names_from = Skill, values_from = Eff_Labor) %>%
  mutate(Managers = Managers / Total,
         Professionals = Professionals / Total,
         Technicians = Technicians / Total,
         Clerks = Clerks / Total, 
         Salesmen = Salesmen / Total,
         Agforestry = Agforestry / Total,
         Craftsmen = Craftsmen / Total,
         Operators = Operators / Total,
         Elementary = Elementary / Total) %>%
  select(-Total) %>%
  pivot_longer(cols = !c(1:2),
               names_to = "Skill",
               names_prefix = NULL,
               values_to = "EffLaborWeight",
               values_drop_na = TRUE) 

# Prepare effective labor dataset for merging with PWT

efflabdata1 <- na.omit(efflabtotal) %>%
  select(-Skill)

wwagedata <- labordata %>%
  dplyr::filter(!grepl('LowSkilled|HighSkilled|MedSkilled|Total', Skill)) %>%
  select(-c("Employed", "Hours")) %>%
  left_join(labweightdata, by = c("Country", "Year", "Skill")) %>%
  left_join(efflabweight, by = c("Country", "Year", "Skill")) %>%
  mutate(AW_Wage = Wage * LaborWeight, EW_Wage = Wage * EffLaborWeight) %>%
  group_by(Country, Year) %>%
  summarize(AW_Wage = sum(AW_Wage), EW_Wage = sum(EW_Wage)) %>%
  filter(!(Country=="Albania"&Year ==2012)) #remove crazy values / outliers

wwagedata <- na.omit(wwagedata)

# Clean PWT data 

cleanpwt <- pwt10.0 %>%
  select(country, isocode, year, cgdpo, hc, cn, rgdpna, rnna) %>%
  rename(Country = 1, Code = 2, Year = 3) %>%
  dplyr::filter(!(is.na(cn) == TRUE & is.na(rnna) ==TRUE)) %>%
  mutate(Country = str_replace(Country, "Bolivia \\(Plurinational State of\\)", "Bolivia")) %>%
  mutate(Country = str_replace(Country, "Cabo Verde", "Cape Verde")) %>%
  mutate(Country = str_replace(Country, "Congo, Democratic Republic", "Congo, Democratic Republic of the")) %>%
  mutate(Country = str_replace(Country, "Cote d'Ivoire", "Côte d'Ivoire")) %>%
  mutate(Country = str_replace(Country, "Czech Republic", "Czechia")) %>%
  mutate(Country = str_replace(Country, "China, Hong Kong SAR", "Hong Kong, China")) %>%
  mutate(Country = str_replace(Country, "Iran \\(Islamic Republic of\\)", "Iran, Islamic Republic of")) %>%
  mutate(Country = str_replace(Country, "Republic of Korea", "Korea, Republic of")) %>%
  mutate(Country = str_replace(Country, "Lao People's DR", "Lao People's Democratic Republic")) %>%
  mutate(Country = str_replace(Country, "China, Macao SAR", "Macau, China")) %>%
  mutate(Country = str_replace(Country, "Republic of Moldova", "Moldova, Republic of")) %>%
  mutate(Country = str_replace(Country, "State of Palestine", "Occupied Palestinian Territory")) %>%
  mutate(Country = str_replace(Country, "St. Vincent & Grenadines", "Saint Vincent and the Grenadines")) %>%
  mutate(Country = str_replace(Country, "Taiwan", "Taiwan, China")) %>%
  mutate(Country = str_replace(Country, "U.R. of Tanzania: Mainland", "Tanzania, United Republic of")) %>%
  mutate(Country = str_replace(Country, "Turkey", "Türkiye")) %>%
  mutate(Country = str_replace(Country, "United States of America", "United States")) %>%
  mutate(Country = str_replace(Country, "Venezuela \\(Bolivarian Republic of\\)", "Venezuela, Bolivarian Republic of"))

# Merge PWT and labor data

estdata <- labtotal %>%
  select(-Skill) %>%
  left_join(efflabtotal, by = c("Country", "Year")) %>%
  select(-Skill) %>%
  left_join(cleanpwt, by = c("Country", "Year")) %>%
  dplyr::filter(!(is.na(cn) == TRUE & is.na(rnna) ==TRUE))

# Extract country names vectors for estimation 

cnames <- estdata %>% 
  dplyr::filter(!(is.na(hc) == TRUE | is.na(rgdpna) ==TRUE)) %>%
  group_by(Country) %>%
  summarise(LH = mean(LaborHours)) %>%
  select(Country)

cnames1 <- estdata %>% 
  dplyr::filter(!(is.na(hc) == TRUE | is.na(rgdpna) ==TRUE | is.na(Eff_Labor) ==TRUE)) %>%
  group_by(Country) %>%
  summarise(LH = mean(Eff_Labor)) %>%
  select(Country)

# Estimate Pooled Cobb-Douglas production functions 
# [initial diagnostics, not used in the final note]

prod_ols = lm(log(rgdpna / LaborHours * hc) ~ 
                  + log(rnna / LaborHours * hc), estdata)
summary(prod_ols)

prod_ols1 = lm(log(cgdpo / LaborHours * hc) ~ 
                 + log(cn / LaborHours * hc), estdata)
summary(prod_ols1)

prod_ols2 = lm(log(rgdpna / Eff_Labor * hc) ~ 
                + log(rnna / Eff_Labor * hc), estdata)
summary(prod_ols2)

prod_ols3 = lm(log(cgdpo / Eff_Labor * hc) ~ 
                 + log(cn / Eff_Labor * hc), estdata)
summary(prod_ols3)

# Estimate Cobb-Douglas production functions with country fixed effects

prod_fe = feols(log(rgdpna / LaborHours * hc) ~ 
                    + (log(rnna / LaborHours * hc) : factor(Country)), estdata)
coef_fe <- as.data.frame(prod_fe[["coefficients"]]) %>% slice(-1) # extract vector of coefficients 


prod_fe1 = feols(log(cgdpo / LaborHours * hc) ~ 
                   + log(cn / LaborHours * hc) : factor(Country), estdata)
coef_fe1 <- as.data.frame(prod_fe1[["coefficients"]]) %>% slice(-1) # extract vector of coefficients 


prod_fe2 = feols(log(rgdpna / Eff_Labor * hc) ~ 
                   + log(rnna / Eff_Labor * hc) : factor(Country), estdata)
coef_fe2 <- as.data.frame(prod_fe2[["coefficients"]])  %>% slice(-1) # extract vector of coefficients 

prod_fe3 = feols(log(cgdpo / Eff_Labor * hc) ~ 
                     + log(cn / Eff_Labor * hc) : factor(Country) , estdata)
coef_fe3 <- as.data.frame(prod_fe3[["coefficients"]]) %>% slice(-1) # extract vector of coefficients 

# Combine estimated datasets and remove values of alphas 
# that don't meet theory restrictions ( < 0 or > 1)

LH_alphas <- cbind(cnames, coef_fe, coef_fe1) %>%
  rename(alpha1 = 2, alpha2 =3) %>%
  mutate(alpha1 = ifelse((alpha1 > 0 & alpha1 < 1), alpha1, NA),
         alpha2 = ifelse((alpha2 > 0 & alpha2 < 1), alpha2, NA)) %>%
  filter(!(is.na(alpha1) == TRUE & is.na(alpha2) ==TRUE))
ELH_alphas <- cbind(cnames1, coef_fe2, coef_fe3) %>%
  rename(alpha3 = 2, alpha4 =3) %>%
  mutate(alpha3 = ifelse((alpha3 > 0 & alpha3 < 1), alpha3, NA),
         alpha4 = ifelse((alpha4 > 0 & alpha4 < 1), alpha4, NA)) %>%
  filter(!(is.na(alpha3) == TRUE & is.na(alpha4) ==TRUE))

# Impute missing values for alphas

imp1 <- mice::mice(LH_alphas, method = "norm.predict", m = 1)
LH_alphas_imp <- complete(imp1)
imp2 <- mice::mice(ELH_alphas, method = "norm.predict", m = 1)
ELH_alphas_imp <- complete(imp2)

# Calculate marginal product of labor for each of 4 alpha measures 

mpldata <- estdata %>% 
  left_join(LH_alphas_imp, by = "Country") %>%
  left_join(ELH_alphas_imp, by = "Country") %>%
  mutate(MPL1 = (1-alpha1)*(rnna / LaborHours * hc)^(alpha1),
         MPL2 = (1-alpha2)*(cn / LaborHours * hc)^(alpha2),
         MPL3 = (1-alpha3)*(rnna / Eff_Labor * hc)^(alpha3),
         MPL4 = (1-alpha4)*(cn / Eff_Labor * hc)^(alpha4)) %>%
  left_join(wwagedata, by = c("Country", "Year"))

# Generate weights 

weightdata <- mpldata %>% 
  select(Country, LaborHours, Eff_Labor, cgdpo, rgdpna) %>%
  group_by(Country) %>%
  summarize_all(mean) %>%
  mutate(lprod= rgdpna / LaborHours) %>%
  mutate(w_output = rgdpna/sum(rgdpna),
         w_labor = LaborHours/sum(LaborHours),
         w_lprod = lprod/sum(lprod)) %>%
  select(Country, w_output, w_labor, w_lprod)

# Calculate distortion factors 

chipsdata <- mpldata %>%
  mutate(chips1 = EW_Wage / AW_Wage,
         chips2 = MPL1 / AW_Wage,
         chips3 = MPL2 / AW_Wage,
         chips4 = MPL3 / AW_Wage,
         chips5 = MPL4 / AW_Wage) %>%
  select(Country, Code, Year, MPL3, AW_Wage, chips1, chips2, chips3, chips4, chips5) %>%
  filter(!(is.na(chips1) == TRUE))

plotdata <- chipsdata %>%
  select(Country, Code, Year, MPL3, AW_Wage) %>%
  group_by(Code) %>%
  summarise(across(c(MPL3, AW_Wage), ~ mean(.x))) %>%
  filter(!(is.na(MPL3) == TRUE))

# Plot Figure 2

ggplot(plotdata, aes(MPL3,AW_Wage)) +
  geom_point() +
  geom_text_repel(aes(label = Code)) + geom_abline(intercept = 0, slope = 1) +
  xlab("Marginal Product of Labor") + ylab("Wage, $2017 per hour")


# Plot Figure 3 panel 1 

chipsdata <- chipsdata %>%
  select(Country, Year, chips1, chips2, chips3, chips4, chips5)

st(chipsdata, vars = c('chips1', 'chips2', 'chips3', 'chips4', 'chips5'), 
   out = "latex",file = "table1.tex")
attach(chipsdata)
hist(chips4[chips4 > 0 & chips4 < 5], breaks = 20, xlab = "Normalized Truncated Value",
     main = "Distribution of DF I Factor")

# Normalize DF values to US 
# This wasn't included in the final note but is nonetheless a useful exercise 

norm <- chipsdata %>% 
  filter(Country=="United States") %>%
  summarise(across(starts_with("chips"), ~ mean(.x)))
norm1 <- norm$chips1
norm2 <- norm$chips2
norm3 <- norm$chips3
norm4 <- norm$chips4
norm5 <- norm$chips5

chipsdata_norm <- chipsdata %>%
  mutate(chips1 = chips1 / norm1, 
         chips2 = chips2 / norm2,
         chips3 = chips3 / norm3,
         chips4 = chips4 / norm4,
         chips5 = chips5 / norm5) 
st(chipsdata_norm, vars = c('chips1', 'chips2', 'chips3', 'chips4', 'chips5'))
attach(chipsdata_norm)
hist(chips4[chips4 > 0 & chips4 < 30], breaks = 20, xlab = "Normalized Truncated Value",
     main = "Distribution of US normalized Chips4 measure")

# Calculate DF adjusted wage 

wagedata2021 <- labordata %>%
  select(c(1,2,3,7)) %>%
  rename(Wage = 4) %>%
  filter(is.na(Wage) ==FALSE) %>%
  filter(!(Country=="Ghana"&Year ==2017)) %>% #remove crazy values / outliers
  filter(!(Country=="Egypt"&Year ==2009)) %>% #remove crazy values / outliers
  filter(!(Country=="Rwanda"&Year ==2014)) %>% #remove crazy values / outliers
  filter(!(Country=="Congo, Democratic Republic of the"&Year ==2005)) %>% #remove crazy values / outliers
  filter(!(Country=="Côte d'Ivoire"&Year ==2019)) %>% #remove crazy values / outliers
  filter(!(Country=="Belize"&Year ==2017)) %>%  #remove crazy values / outliers
  filter(!(Country=="Cambodia")) %>% #remove crazy values / outliers
  filter(!(Country=="Lao People's Democratic Republic")) %>% #remove crazy values / outliers
  filter(!(Country=="Timor-Leste")) %>% #remove crazy values / outliers
  pivot_wider(names_from = Skill, values_from = Wage) 
# left_join(indices, by=c("Country", "Year"))

chipswagedata <- wagedata2021 %>% 
  left_join(chipsdata, by = c("Country", "Year")) %>%
  filter(!(is.na(chips1) == TRUE | is.na(chips2) ==TRUE | is.na(chips4) ==TRUE)) %>%
  mutate(el_wage1 = Elementary * chips1,
         el_wage2 = Elementary * chips2,
         el_wage3 = Elementary * chips3,
         el_wage4 = Elementary * chips4,
         el_wage5 = Elementary * chips5) %>%
  group_by(Country) %>% 
  summarize(across(starts_with("el"), ~ mean(.x)))

st(chipswagedata, vars = c('Elementary', 'el_wage1', 'el_wage2', 'el_wage3', 'el_wage4', 'el_wage5'))

# Plot Figure 3 panel 2 

attach(chipswagedata)
hist(el_wage4[el_wage4  > 0 & el_wage4  < 30], breaks = 20, xlab = "Normalized Truncated Value, 2021 USD",
     main = "Distribution of Unskilled Labor Wage Adjusted by DF I")

# Plot Distribution of unskilled labor wage (can be useful)

hist(Elementary[Elementary  > 0 & Elementary  < 35], breaks = 30, xlab = "USD per hour",
     main = "Distribution of unskilled labor wage")

# CHIPS baseline values using different weights 
# Metric used in the note is el_wo_wage

wchipswagedata <- wagedata2021 %>% 
  left_join(chipsdata, by = c("Country", "Year")) %>%
  filter(!(is.na(chips1) == TRUE | is.na(chips2) ==TRUE | is.na(chips4) ==TRUE)) %>%
  left_join(PPPF, by = c("Country", "Year")) %>%
  left_join(weightdata, by = "Country") %>%
  mutate(el_unw_wage = Elementary * chips4) %>%
  group_by(Country) %>% 
  summarize(across(where(is.numeric), ~ mean(.x))) %>%
  mutate(el_wo_wage = sum(el_unw_wage * w_output),
         el_wl_wage = sum(el_unw_wage * w_labor),
         el_wp_wage = sum(el_unw_wage * w_lprod),
         el_ppp_wage = Elementary * chips5 * PPPF) %>%
  select(el_unw_wage, el_wo_wage, el_wl_wage, el_wp_wage, el_ppp_wage) %>%
  summarise_all(mean, na.rm = TRUE) 



