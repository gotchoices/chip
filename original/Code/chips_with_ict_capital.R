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
# install.packages("devtools") # uncomment for the first time us
# install.packages("Rilostat") # uncomment for the first time us
# install.packages("fredr") # uncomment for the first time us
# install.packages("xlsx")

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
library(devtools)
library(Rilostat)
library(fredr)
library(xlsx)
# Set path and API Keys 

setwd("../Data")  # Relative path from Code/ to Data/

# Load API key from secrets file (see ../secrets.example.toml)
secrets <- read.dcf("../secrets.toml")
fredr_set_key(secrets[1, "fred_api_key"])

# Load data 

data("pwt10.0") # from PWT10 API 
employment <- get_ilostat("EMP_TEMP_SEX_OCU_NB_A", type = "both", cache=FALSE)
wages <- get_ilostat("EAR_4HRL_SEX_OCU_CUR_NB_A", type = "both", cache=FALSE)
hoursworked <- get_ilostat("HOW_TEMP_SEX_OCU_NB_A", type = "both", cache=FALSE)
fcslist <- read_excel("fcslist.xlsx", sheet = "Data")
freedomindex <- read_excel("freedomindex.xlsx", sheet = "EFW Data 2022 Report", skip = 4)

GDPDEF <- fredr(
  series_id = "USAGDPDEFAISMEI",
  observation_start = as.Date("1970-01-01"),
  observation_end = as.Date("2023-01-01")
)

# Clean and reshape data 

GDPDEF <- GDPDEF %>%
  rename(Date = 1, GDPDEF =3) %>%
  mutate(Year = year(Date)) %>%
  select(c("Year", "GDPDEF"))


#Define latest year 

ly = max(GDPDEF$Year) 

def2017base <- GDPDEF[which(GDPDEF$Year==2017), ] %>%
  select(GDPDEF)
def2017base <- as.numeric(def2017base)

def_ly_base <- GDPDEF[which(GDPDEF$Year==ly), ] %>%
  select(GDPDEF)
def_ly_base <- as.numeric(def_ly_base)  

GDPDEF <- GDPDEF %>%
  mutate(GDPDEF2017 = GDPDEF/def2017base,
         GDPDEFLY = GDPDEF/def_ly_base)

# Clean ILOSTAT data 

employment <- employment %>%
  select(c(2,7,9,11,12)) %>%
  rename(Country = 1, Sex = 2, Skill = 3, Year = 4, Employed = 5) %>%
  mutate(Year = as.numeric(Year)) %>%
  filter(Sex == "SEX_T") %>%
  select(-c(2)) %>% 
  filter(Skill != "Occupation (Skill level): Not elsewhere classified", 
         Skill != "OCU_ISCO88_0",
         Skill != "OCU_ISCO08_0",
         Skill != "OCU_ISCO68_AF",
         Skill != "OCU_ISCO88_X",
         Skill != "OCU_ISCO68_X",
         Skill != "OCU_ISCO08_X",
         Skill != "OCU_SKILL_X",
         Skill != "OCU_SKILL_TOTAL",
         Skill != "OCU_ISCO08_TOTAL",
         Skill != "OCU_ISCO68_TOTAL",
         Skill != "OCU_ISCO88_TOTAL", 
         Skill != "OCU_SKILL_L3-4", 
         Skill != "OCU_SKILL_L2", 
         Skill != "OCU_SKILL_L1") 
 
hoursworked <- hoursworked %>%
  select(c(2,7,9,11,12)) %>%
  rename(Country = 1, Sex = 2, Skill = 3, Year = 4, Hours = 5) %>%
  mutate(Year = as.numeric(Year)) %>%
  filter(Sex == "SEX_T") %>%
  select(-c(2)) %>% 
  filter(Skill != "OCU_SKILL_X",
         Skill != "OCU_ISCO08_X", 
         Skill != "OCU_ISCO88_0",
         Skill != "OCU_ISCO08_0",
         Skill != "OCU_ISCO08_TOTAL",
         Skill != "OCU_SKILL_TOTAL",
         Skill != "OCU_SKILL_L3-4",
         Skill != "OCU_SKILL_L2",
         Skill != "OCU_SKILL_L1")

wages <- wages %>%
  select(c(2,7,9,11,13,14)) %>%
  rename(Country = 1, Sex = 2, Skill = 3, Currency = 4, Year = 5, Wage = 6) %>%
  filter(Sex == "SEX_T") %>%
  mutate(Year = as.numeric(Year)) %>%
  select(-c(2)) %>% 
  filter(Skill != "OCU_SKILL_X",
         Skill != "OCU_ISCO08_X", 
         Skill != "OCU_ISCO88_X", 
         Skill != "OCU_ISCO88_0",
         Skill != "OCU_ISCO08_0",
         Skill != "OCU_ISCO08_TOTAL",
         Skill != "OCU_ISCO88_TOTAL",
         Skill != "OCU_SKILL_TOTAL",
         Skill != "OCU_SKILL_L3-4",
         Skill != "OCU_SKILL_L2",
         Skill != "OCU_SKILL_L1") %>%
filter(!(Country=="Albania"&Year ==2012))  #remove crazy values / outliers
  

# Rebase real wage data to last available year

wages_USD <- wages %>%
  filter(Currency == "CUR_TYPE_USD") %>%
  select(-"Currency") %>%
  left_join(GDPDEF, by = "Year") %>%
  mutate(Wage = Wage / GDPDEF2017, WageLY = Wage/GDPDEFLY) %>%
  select(-c("GDPDEF", "GDPDEF2017", "GDPDEFLY"))

wages_PPP <- wages %>%
  filter(Currency == "CUR_TYPE_PPP") %>%
  select(-"Currency") 

PPPF <- wages_USD %>%
  left_join(wages_PPP, by = c("Country", "Year", "Skill")) %>%
  filter(grepl('_9', Skill)) %>%
  filter(!is.na(Wage.y)) %>%
  mutate(PPPF = Wage.y / Wage.x) %>%
  select(Country, Year, PPPF) 

# Merge and Standartize Labor data 

labordata <- employment %>% 
  left_join(hoursworked, by = c("Country", "Year", "Skill")) %>%
  left_join(wages_USD, by = c("Country", "Year", "Skill")) %>%
  arrange(Country,Year,Skill) %>%
  mutate(Skill = case_when(Skill == "OCU_ISCO08_1" ~ "Managers", 
                   Skill == "OCU_ISCO08_2" ~ "Professionals",
                   Skill == "OCU_ISCO08_3" ~ "Technicians",
                   Skill == "OCU_ISCO08_4" ~ "Clerks",
                   Skill == "OCU_ISCO08_5" ~ "Salesmen",
                   Skill == "OCU_ISCO08_6" ~ "Agforestry",
                   Skill == "OCU_ISCO08_7" ~"Craftsmen",
                   Skill == "OCU_ISCO08_8" ~ "Operators",
                   Skill == "OCU_ISCO08_9" ~ "Elementary",
                   Skill == "OCU_ISCO68_2" ~ "Managers", 
                   Skill == "OCU_ISCO08_9" ~ "Professionals",
                   Skill == "OCU_ISCO68_3" ~ "Clerks",
                   Skill == "OCU_ISCO68_4" ~ "Sales68",
                   Skill == "OCU_ISCO68_5" ~ "Service68",                   
                   Skill == "OCU_ISCO68_6" ~ "Agforestry",
                   Skill == "OCU_ISCO68_7-9" ~ "Operators",
                   Skill == "OCU_ISCO88_1" ~ "Managers", 
                   Skill == "OCU_ISCO88_2" ~ "Professionals",
                   Skill == "OCU_ISCO88_3" ~ "Technicians",
                   Skill == "OCU_ISCO88_4" ~ "Clerks",
                   Skill == "OCU_ISCO88_5" ~ "Salesmen",
                   Skill == "OCU_ISCO88_6" ~ "Agforestry",
                   Skill == "OCU_ISCO88_7" ~"Craftsmen",
                   Skill == "OCU_ISCO88_8" ~ "Operators",
                   Skill == "OCU_ISCO88_9" ~ "Elementary"
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
  select(-c("Managers")) %>%
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
  select(-c("Wage", "WageLY")) %>%
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
  select(-c("Wage", "WageLY")) %>%
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

efflabdata <- na.omit(efflabdata)

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

# Import and clean the OECD ICT data, construct ICT CAP share 

oecd_ict <- read.csv("oecd_ict.csv")

oecd_ict <- oecd_ict %>% 
  select(LOCATION, TIME, Value) %>%
  rename(Code = LOCATION, ict_share = Value, Year = TIME) %>% 
  left_join(cleanpwt, by = c("Code","Year")) %>%
  select(c(1:4,7,9)) %>%
  group_by(Code) %>%
  mutate(I = cn - lag(cn), I1 = rnna - lag(rnna))

oecd_ict <- oecd_ict %>% 
  mutate(I = ifelse(is.na(I), cn, I), I1 = ifelse(is.na(I1), rnna, I1), 
         I_IT = I * ict_share / 100, I_IT1 = I1 * ict_share / 100) %>%
  select(-ict_share) %>%
  group_by(Code) %>%
  mutate(K_IT = cumsum(I_IT), K_IT1 = cumsum(I_IT1), 
         ict_share = K_IT/cn*100, ict_share_1 = K_IT1/rnna*100) %>%
  select(-c(K_IT, K_IT1, I, I1, I_IT, I_IT1, cn, rnna, Country))

# Import and clean the EU KLEMS data 

klems_ict <- read.csv("capital_accounts.csv")
klems_ict <- klems_ict %>%
  select(geo_name, year, nace_r2_name, K_CT, K_IT, K_Soft_DB, K_GFCF) %>%
  rename(Country = geo_name, Year = year) %>%
  filter(!grepl("European Union", Country)) %>%
  filter(!grepl("Euro", Country)) %>%
  filter(!grepl("without UK", Country)) %>%
  filter(!grepl("AT, BE, CZ, DE", Country)) %>%
  mutate(Country = ifelse(grepl("FRG", Country), "Germany", Country)) %>%
  group_by(Country, Year) %>%
  summarise(across(starts_with("K_"), ~ sum(.x, na.rm = TRUE))) %>%
  mutate(ict_share1 = rowSums(cbind(K_CT,K_IT,K_Soft_DB), na.rm = TRUE)/K_GFCF*100) %>%
  select(Country, Year, ict_share1) %>%
  arrange(Country, Year)
  
# Merge PWT, and the OECD and KLEMS ICT data

cleanpwt <- cleanpwt %>% 
  left_join(oecd_ict, by = c("Code","Year")) %>%
  left_join(klems_ict, by = c("Country","Year")) 

cleanpwt <- cleanpwt %>% 
  mutate(ict_s = rowMeans(cbind(ict_share,ict_share1), na.rm = TRUE),
         ict_s1 = rowMeans(cbind(ict_share,ict_share_1), na.rm = TRUE)) %>% 
  mutate(K_IT = cn * ict_s / 100, K_NIT = cn - K_IT, 
         K_IT1 = rnna * ict_s1 / 100, K_NIT1 = rnna - K_IT1) %>% 
  select(-c(ict_s, ict_s1, ict_share,ict_share1, ict_share_1))

# Merge PWT and labor data

estdata <- labtotal %>%
  select(-Skill) %>%
  left_join(efflabtotal, by = c("Country", "Year")) %>%
  select(-Skill) %>%
  left_join(cleanpwt, by = c("Country", "Year")) %>%
  dplyr::filter(!(is.na(cn) == TRUE & is.na(rnna) ==TRUE))

# Make a subset of data for which ICT capital stocks are available 

estdata1 <- estdata %>%
  filter(!is.nan(K_IT) | !is.nan(K_IT1))

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
                    + log(rnna / LaborHours * hc) : factor(Country), estdata)
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


# Estimate Cobb-Douglas production functions separating out IT and non IT capital with country fixed effects

prod_fe_it = feols(log(rgdpna) ~ 
   log(K_IT1 / LaborHours * hc) + log(K_NIT1 / LaborHours * hc) : factor(Country), estdata1)
coef_fe_it <- as.data.frame(prod_fe_it[["coefficients"]]) %>% 
  slice(-(1:2)) # extract vector of coefficients 

cnames_it <- as.data.frame(rownames(coef_fe_it))
cnames_it <- cnames_it %>%
  rename(Country = 1) %>%
  mutate(Country = str_replace(Country, "log\\(K_NIT1/LaborHours \\* hc\\):factor\\(Country\\)", ""))

prod_fe1_it = feols(log(cgdpo / LaborHours * hc) ~ 
     log(K_IT / LaborHours * hc) + log(K_NIT / LaborHours * hc) : factor(Country), estdata1)
coef_fe1_it <- as.data.frame(prod_fe1_it[["coefficients"]]) %>% slice(-(1:2)) # extract vector of coefficients 

cnames_it1 <- as.data.frame(rownames(coef_fe1_it))
cnames_it1 <- cnames_it1 %>%
  rename(Country = 1) %>%
  mutate(Country = str_replace(Country, "log\\(K_NIT/LaborHours \\* hc\\):factor\\(Country\\)", ""))

prod_fe2_it = feols(log(rgdpna / Eff_Labor * hc) ~ 
     log(K_IT1 / Eff_Labor * hc)  + log(K_NIT1 / Eff_Labor * hc) : factor(Country), estdata1)
coef_fe2_it <- as.data.frame(prod_fe2_it[["coefficients"]])  %>% slice(-(1:2)) # extract vector of coefficients 

cnames_it2 <- as.data.frame(rownames(coef_fe2_it))
cnames_it2 <- cnames_it2 %>%
  rename(Country = 1) %>%
  mutate(Country = str_replace(Country, "log\\(K_NIT1/Eff_Labor \\* hc\\):factor\\(Country\\)", ""))

prod_fe3_it = feols(log(cgdpo / Eff_Labor * hc) ~ 
     log(K_IT / Eff_Labor * hc)  + log(K_NIT / Eff_Labor * hc) : factor(Country) , estdata1)
coef_fe3_it <- as.data.frame(prod_fe3_it[["coefficients"]]) %>% slice(-(1:2)) # extract vector of coefficients 

cnames_it3 <- as.data.frame(rownames(coef_fe3_it))
cnames_it3 <- cnames_it3 %>%
  rename(Country = 1) %>%
  mutate(Country = str_replace(Country, "log\\(K_NIT/Eff_Labor \\* hc\\):factor\\(Country\\)", ""))

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

LH_alphas_IT <- cbind(cnames_it, coef_fe_it) %>%
  rename(alpha1_it = 2) %>%
  mutate(alpha1_it = ifelse((alpha1_it  > 0 & alpha1_it < 1), alpha1_it, NA)) %>%
  filter(!(is.na(alpha1_it) == TRUE))

LH_alphas_IT1 <- cbind(cnames_it1, coef_fe1_it) %>%
  rename(alpha2_it = 2) %>%
  mutate(alpha2_it = ifelse((alpha2_it  > 0 & alpha2_it < 1), alpha2_it, NA)) %>%
  filter(!(is.na(alpha2_it) == TRUE))

ELH_alphas_IT <- cbind(cnames_it2, coef_fe2_it) %>%
  rename(alpha3_it = 2) %>%
  mutate(alpha3_it = ifelse((alpha3_it  > 0 & alpha3_it < 1), alpha3_it, NA)) %>%
  filter(!(is.na(alpha3_it) == TRUE))

ELH_alphas_IT1 <- cbind(cnames_it3, coef_fe3_it) %>%
  rename(alpha4_it = 2) %>%
  mutate(alpha4_it = ifelse((alpha4_it  > 0 & alpha4_it < 1), alpha4_it, NA)) %>%
  filter(!(is.na(alpha4_it) == TRUE))

Alphas_IT <- LH_alphas_IT %>%
  full_join(LH_alphas_IT1, by = c("Country")) %>%
  full_join(ELH_alphas_IT, by = c("Country")) %>%
  full_join(ELH_alphas_IT1, by = c("Country")) 

# Impute missing values for alphas

imp1 <- mice::mice(LH_alphas, method = "norm.predict", m = 1)
LH_alphas_imp <- complete(imp1)
imp2 <- mice::mice(ELH_alphas, method = "norm.predict", m = 1)
ELH_alphas_imp <- complete(imp2)

# Update alphas from IT estimation if nonmissing
# Calculate marginal product of labor for each of 4 alpha measures 

mpldata <- estdata %>% 
  left_join(LH_alphas_imp, by = "Country") %>%
  left_join(ELH_alphas_imp, by = "Country") %>%
  left_join(Alphas_IT, by = "Country") %>%
  mutate(alpha1 = ifelse(is.na(alpha1_it), alpha1, alpha1_it),
         ifelse(is.na(alpha2_it), alpha2, alpha2_it),
         ifelse(is.na(alpha3_it), alpha3, alpha3_it),
         ifelse(is.na(alpha4_it), alpha4, alpha4_it)) %>%
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

# Calculate DF adjusted wage for last available year 

wagedataly <- labordata %>%
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

chipswagedata <- wagedataly %>% 
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

wchipswagedata <- wagedataly %>% 
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

# Construct time-varying CHIPS indices 

# Option A: Adjusting for changes in wages and dollar inflation
# Using metric used in the note (el_wo_wage)

wchipswagedataA <- wagedataly %>% 
  left_join(chipsdata, by = c("Country", "Year")) %>%
  filter(!(is.na(chips1) == TRUE | is.na(chips2) ==TRUE | is.na(chips4) ==TRUE)) %>%
  left_join(PPPF, by = c("Country", "Year")) %>%
  left_join(weightdata, by = "Country") 

for(i in 2017:2022) {
  varname <- paste("el_wo_wage", i , sep=".")
  defbase <- as.numeric(GDPDEF[which(GDPDEF$Year==i), 2])
  wchipswagedataA[[varname]] <- with(wchipswagedataA, Elementary * chips4 / def_ly_base * defbase)
  wchipswagedataA[wchipswagedataA$Year >=i,][[varname]] <- NA
}
wchipswagedataA <- wchipswagedataA %>%
  group_by(Country) %>% 
  summarize(across(where(is.numeric), ~ mean(.x, na.rm = TRUE))) %>%
  mutate(across(starts_with("el_wo_wage"), ~ sum(.x * w_output, na.rm = TRUE))) %>%
  select(starts_with("el_wo_wage")) %>%
  summarise_all(mean, na.rm = TRUE) 

# Option B: Adjusting for changes in dollar inflation only 
# Using metric used in the note (el_wo_wage)

wchipswagedataB <- wagedataly %>% 
  left_join(chipsdata, by = c("Country", "Year")) %>%
  filter(!(is.na(chips1) == TRUE | is.na(chips2) ==TRUE | is.na(chips4) ==TRUE)) %>%
  left_join(PPPF, by = c("Country", "Year")) %>%
  left_join(weightdata, by = "Country") 

for(i in 2017:2022) {
  varname <- paste("el_wo_wage", i , sep=".")
  defbase <- as.numeric(GDPDEF[which(GDPDEF$Year==i), 2])
  wchipswagedataB[[varname]] <- with(wchipswagedataB, Elementary * chips4 / def_ly_base * defbase)
}
  
wchipswagedataB <- wchipswagedataB %>%
  group_by(Country) %>% 
  summarize(across(where(is.numeric), ~ mean(.x))) %>%
  mutate(across(starts_with("el_wo_wage"), ~ sum(.x * w_output))) %>%
    select(starts_with("el_wo_wage")) %>%
  summarise_all(mean, na.rm = TRUE) 

# Preparing time-series tables

chip_ts <- rbind(wchipswagedataA, wchipswagedataB)
chip_ts["Option"] <- c("A","B")

chip_ts <- chip_ts %>%
  pivot_longer(!Option, names_to = "Year", values_to = "value")
chip_ts$Year <- as.numeric(gsub("[^0-9]", "", chip_ts$Year))
chip_ts <- chip_ts %>%
  pivot_wider(names_from = Option, names_prefix = "Option", values_from = value)

write.xlsx(chip_ts, file = "time_series_itc.xlsx", sheetName = "Sheet1", 
           col.names = TRUE, row.names = TRUE, append = FALSE)
