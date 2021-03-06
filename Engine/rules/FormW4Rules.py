from akkadian import *
# https://www.irs.gov/pub/irs-pdf/fw4.pdf
# IRS Form w4(2019) rules


############### source rules ###############
def form_w4_complete(person, spouse):
    return And(
        personal_allowances_wksheet_complete(person, spouse),
        Or(
            (not plans_to_itemize_or_claim_adjustments(person)), deductions_adjustments_and_additional_income_wksht_complete(person)),
        Or(not two_earners_mult_jobs_wksht_required(person, spouse), two_earners_mult_jobs_wksht_complete(person, spouse)))


#######PERSONAL ALLOWANCES WORKSHEET#######
# can we make person/spouse global?
def personal_allowances_wksheet_complete(person, spouse):
    # check complete if line h is known?
    return personal_allowances_worksheet_line_h(person, spouse) >= 0


# A, default to true/1?
def claiming_self(person):
    return If(is_claiming_self(person), 1, 0)


# B, married, filing jointly
def file_married_jointly(person, spouse):
    return If(And(is_married(person, spouse), filing_jointly(person)), 1, 0)


# intermediates help with readability?
def filing_jointly(p):
    return tax_status(p) == "Married Filing Jointly"


# convert boolean to 1/0 for adding?
# C, head of household
    #     Line C. Head of household please note:
    # Generally, you may claim head of household
    # filing status on your tax return only if you’re
    # unmarried and pay more than 50% of the
    # costs of keeping up a home for yourself and
    # a qualifying individual. See Pub. 501 for
    # more information about filing status
def file_head_of_household(person):
    return If(head_of_household(person), 1, 0)

    # • You’re single, or married filing separately, and have only one job; or
    # •  You’re married filing jointly, have only one job, and your spouse doesn’t work; or
    # • Your wages from a second job or your spouse’s wages (or the total of both) are $1,500 or less


def only_job_or_low_wage_second(person, spouse):
    # dev question, could we infer "only one job" as one active wages/employment record? Probably a question for policy team.
    # formatting? #readability?
    If(
        Or(
            And(
                Or(is_single(person),
                   married_filing_separately(person, spouse)),
                has_only_one_job(person)),
            And(
                file_married_jointly(person, spouse),
                has_only_one_job(person),
                spouse_unemployed(spouse)
            ),
            combined_couple_wages(person, spouse) <= 1500),
        1,
        0)


def married_filing_separately(person, spouse):
    return And(is_married(person, spouse),
               filing_separately(person))


def filing_separately(p):
    return Not(filing_jointly(p))

# Child tax credit. See Pub. 972, Child Tax Credit, for more information.
# • If your total income will be less than $71,201 ($103,351 if married filing jointly), enter 4 for each eligible child.
# • If your total income will be from $71,201 to $179,050 ($103,351 to $345,850 if married filing jointly), enter 2 for each
# eligible child.
# • If your total income will be from $179,051 to $200,000 ($345,851 to $400,000 if married filing jointly), enter 1 for
# each eligible child.
# • If your total income will be higher than $200,000 ($400,000 if married filing jointly), enter -0- . . . . . . .


def child_tax_credit(person, spouse):
    If(And(spouse is not None, file_married_jointly(person, spouse)), 
    #then
    child_tax_credit_w_spouse(person, spouse), 
    #else
    # no spouse
    child_tax_credit_w_o_spouse(person))
     

def child_tax_credit_w_spouse(person, spouse):
    
    return If((total_income(person) + total_income(spouse) < 103351),
    #then
    4 * num_children(person),
    #elif
    (And(total_income(person) + total_income(spouse) >= 103, 351, total_income(person) + total_income(spouse) <= 345, 850)),
    #then
    2 * num_children(person),
    #elif
    (And(total_income(person) + total_income(spouse) >= 345851, total_income(person) + total_income(spouse) <= 400000)),
    #then
    num_children(person),
    #otherwise
    0)

def child_tax_credit_w_o_spouse(person):
    return If(total_income(person) < 71201,
        #then
        4 * num_children(person),
        #else if
        (And(total_income(person) >= 71201, total_income(person) <= 179051)),
            #then
            2 * num_children(person),
        #else if
        (And(total_income(person) >= 179051, total_income(person) <= 200000)),
            #then
            num_children(person),
        #otherwise
            0)

# Credit for other dependents. See Pub. 972, Child Tax Credit, for more information.
# • If your total income will be less than $71,201 ($103,351 if married filing jointly), enter “1” for each eligible dependent.
# • If your total income will be from $71,201 to $179,050 ($103,351 to $345,850 if married filing jointly), enter “1” for every
# two dependents (for example, “-0-” for one dependent, “1” if you have two or three dependents, and “2” if you have
# four dependents).
# • If your total income will be higher than $179,050 ($345,850 if married filing jointly), enter “-0-” . . . . . .
def credit_for_other_dependents(person, spouse):
    If(spouse is not None,
        And(credit_for_other_dependents_w_spouse(person, spouse), file_married_jointly(person, spouse)),
        credit_for_other_dependents_w_o_spouse(person))

def credit_for_other_dependents_w_spouse(person, spouse):
        return If(total_income(person) + total_income(spouse) < 103351,
             #then
             num_dependents(person),
            #elif
            (And(total_income(person) + total_income(spouse) >= 103351, total_income(person) + total_income(spouse) <= 345850)),
                #then
                math.floor(num_dependents(person) / 2),
            #elif
            (total_income(person) + total_income(spouse) > 345850),
             #then
             0)

def credit_for_other_dependents_w_o_spouse(person):
       return If(total_income(person) < 71201,
             num_dependents(person),
            (And(total_income(person) >= 71201,
            total_income(person) <= 179051)),
             math.floor(num_dependents(person) / 2),
            (total_income(person) > 179050),
            0)

# Other credits. If you have other credits, see Worksheet 1-6 of Pub. 505 and enter the amount from that worksheet
# here. If you use Worksheet 1-6, enter “-0-” on lines E and F . . . .
def other_credits(person):
    return If(has_other_credits(person), other_credits_pub505(person), 0)


def personal_allowances_worksheet_line_h(person, spouse):
    return claiming_self(person)\
           + file_married_jointly(person, spouse)\
           + file_head_of_household(person)\
           + only_job_or_low_wage_second(person, spouse)\
           + child_tax_credit(person, spouse)\
           + credit_for_other_dependents(person, spouse)\
           + other_credits(person)


#######Deductions, Adjustments, and Additional Income Worksheet#######
# Note: Use this worksheet only if you plan to itemize deductions, claim certain adjustments to income, or have a large amount of nonwage
# income not subject to withholding.
def deductions_adjustments_and_additional_income_wksht_complete(person):
    return ded_adj_adtl_inc_line_10 >= 0

# Enter an estimate of your 2019 itemized deductions. These include qualifying home mortgage interest,
# charitable contributions, state and local taxes (up to $10,000), and medical expenses in excess of 10% of
# your income. See Pub. 505 for details . . . . . . . . . . . . . . . . . . . . . .


def ded_adj_adtl_inc_line_1(person):
    return itemized_deductions_2019(person)

# 2 Enter: { $24,400 if you’re married filing jointly or qualifying widow(er)
# $18,350 if you’re head of household
# $12,200 if you’re single or married filing separately } . .


def ded_adj_adtl_inc_line_2(person):
    return If(Or(filing_jointly(person), qualifying_widower(person)),
        24400,
    head_of_household(person),
     18350,
    Or(is_single(person), filing_separately(person)),
     12200)

# Subtract line 2 from line 1. If zero or less, enter “-0-”
def ded_adj_adtl_inc_line_3(person, spouse):
    return If(ded_adj_adtl_inc_line_1(person) - ded_adj_adtl_inc_line_2(person) >= 0,
         ded_adj_adtl_inc_line_1(person) - ded_adj_adtl_inc_line_2(person),
        False)

# Enter an estimate of your 2019 adjustments to income, qualified business income deduction, and any
# additional standard deduction for age or blindness (see Pub. 505 for information about these items) . .
def ded_adj_adtl_inc_line_4(person, spouse):
    return estimate_2019_adj_to_inc_qual_bus_inc_ded_addtl_std_ded(person)

# Add lines 3 and 4 and enter the total
def ded_adj_adtl_inc_line_5(person, spouse):
    return ded_adj_adtl_inc_line_3(person, spouse) + ded_adj_adtl_inc_line_4(person, spouse)

# Enter an estimate of your 2019 nonwage income not subject to withholding (such as dividends or interest) .
def ded_adj_adtl_inc_line_6(person, spouse):
    return estimate_2019_nonwage_inc_not_subj_to_withholding(person)

# Subtract line 6 from line 5. If zero, enter “-0-”. If less than zero, enter the amount in parentheses
def ded_adj_adtl_inc_line_7(person, spouse):
    return ded_adj_adtl_inc_line_5(person, spouse) - ded_adj_adtl_inc_line_6(person, spouse)

# Divide the amount on line 7 by $4,200 and enter the result here. If a negative amount, enter in parentheses.
# Drop any fraction
def ded_adj_adtl_inc_line_8(person, spouse):
    return math.floor(ded_adj_adtl_inc_line_7(person, spouse) / 4200)

# Enter the number from the Personal Allowances Worksheet, line H, above
def ded_adj_adtl_inc_line_9(person, spouse):
    return personal_allowances_worksheet_line_h(person, spouse)

# Add lines 8 and 9 and enter the total here. If zero or less, enter “- 0 -”. If you plan to use the Two-Earners/
# Multiple Jobs Worksheet, also enter this total on line 1 of that worksheet on page 4. Otherwise, stop here
# and enter this total on Form W-4, line 5, page 1
def ded_adj_adtl_inc_line_10(person, spouse):
    return max(ded_adj_adtl_inc_line_8(person, spouse) + ded_adj_adtl_inc_line_9(person, spouse), 0)


###############Two Earners/Multiple Jobs Wksht###############
# Note: Use this worksheet only if the instructions under line H from the Personal Allowances Worksheet direct you here.

# If you have more than one job at a time
# or are married filing jointly and you and your spouse both work,
#
# and the combined earnings from all jobs exceed $53,000 ($24,450 if married filing jointly), see the
# Two-Earners/Multiple Jobs Worksheet on page 4 to avoid having too little tax withheld.
def two_earners_mult_jobs_wksht_required(person, spouse):
    return If(
        Or(two_earners_mult_jobs_wksht_required_single(person),
           two_earners_mult_jobs_wksht_required_couple(person, spouse)),
        True, False)

#complete if line 9 is known
def two_earners_mult_jobs_wksht_complete(person, spouse):
    return two_earners_mult_jobs_wksht_line_9(person, spouse)

def two_earners_mult_jobs_wksht_required_single(person):
    return If(And(count_of_jobs(person) > 1, total_income(person) > 53000), True, False)


def two_earners_mult_jobs_wksht_required_couple(person, spouse):
    return If(
    And(is_married(person, spouse),
            filing_jointly(person),
            couple_both_work(person, spouse),
            combined_couple_wages(person, spouse) > 24450), True, False)


# Enter the number from the Personal Allowances Worksheet, line H, page 3 (or, if you used the
# Deductions, Adjustments, and Additional Income Worksheet on page 3, the number from line 10 of that
# worksheet)
# tbd, logic to figure out which wksht has been completed
def two_earners_mult_jobs_wksht_line_1(person, spouse):
    return If(plans_to_itemize_or_claim_adjustments(person), ded_adj_adtl_inc_line_10(person, spouse), personal_allowances_worksheet_line_h(person, spouse))

# Find the number in Table 1 below that applies to the LOWEST paying job and enter it here. However, if you’re
# married filing jointly and wages from the highest paying job are $75,000 or less and the combined wages for
# you and your spouse are $107,000 or less, don’t enter more than “3”


def two_earners_mult_jobs_wksht_line_2(person, spouse):
    return If(And(is_married(person, spouse), filing_jointly(person), highest_earning_job_from_couple(person, spouse) <= 75000, combined_couple_wages(person, spouse)),
        # assumes only one job, needs to be expanded
        min(3, two_earners_mult_jobs_wksht_table_1_married_joint_lookup(min(persons_wages(person), persons_wages(spouse)))),
    (And(is_married(person, spouse), filing_jointly(person)),
        two_earners_mult_jobs_wksht_table_1_married_joint_lookup(combined_couple_wages(person, spouse))),
    two_earners_mult_jobs_wksht_table_1_all_others_lookup(persons_wages(person)))


# If line 1 is more than or equal to line 2, subtract line 2 from line 1. Enter the result here (if zero, enter “-0-”)
# and on Form W-4, line 5, page 1. Do not use the rest of this worksheet
def two_earners_mult_jobs_wksht_line_3(person, spouse):
    return If(two_earners_mult_jobs_wksht_line_1(person) >= two_earners_mult_jobs_wksht_line_2(person, spouse),
        two_earners_mult_jobs_wksht_line_2(person, spouse) - two_earners_mult_jobs_wksht_line_1(person),
        two_earners_mult_jobs_wksht_line_4(person))


# Note: If line 1 is less than line 2, enter “-0-” on Form W-4, line 5, page 1. Complete lines 4 through 9 below to
# figure the additional withholding amount necessary to avoid a year-end tax bill.
# Enter the number from line 2 of this worksheet
def two_earners_mult_jobs_wksht_line_4(person, spouse):
    return two_earners_mult_jobs_wksht_line_2(person, spouse)

# Enter the number from line 1 of this worksheet
def two_earners_mult_jobs_wksht_line_5(person, spouse):
    return two_earners_mult_jobs_wksht_line_1(person)

# 6 Subtract line 5 from line 4
def two_earners_mult_jobs_wksht_line_6(person, spouse):
    return two_earners_mult_jobs_wksht_line_4(person, spouse) - two_earners_mult_jobs_wksht_line_5(person, spouse)

# Find the amount in Table 2 below that applies to the HIGHEST paying job and enter it here
def two_earners_mult_jobs_wksht_line_7(person, spouse):
    return If(And(is_married(person), filing_jointly(person)),
        # assumes one job, needs to be expanded
        two_earners_mult_jobs_wksht_table_2_married_joint_lookup(max(persons_wages(person), persons_wages(spouse))),
        two_earners_mult_jobs_wksht_table_2_all_others_lookup(persons_wages(person)))

# Multiply line 7 by line 6 and enter the result here. This is the additional annual withholding needed
def two_earners_mult_jobs_wksht_line_8(person, spouse):
    return  two_earners_mult_jobs_wksht_line_6(person, spouse) * two_earners_mult_jobs_wksht_line_7(person, spouse)

# Divide line 8 by the number of pay periods remaining in 2019. For example, divide by 18 if you’re paid every
# 2 weeks and you complete this form on a date in late April when there are 18 pay periods remaining in
# 2019. Enter the result here and on Form W-4, line 6, page 1. This is the additional amount to be withheld
# from each paycheck 
def two_earners_mult_jobs_wksht_line_9(person, spouse):
    return trunc(two_earners_mult_jobs_wksht_line_8(person, spouse) / num_pay_periods_remaining_in_year(person))

############### intermediates ###############
def spouse_unemployed(s):
    return employment_status(s) != "Employed"


def combined_couple_wages(person, spouse):
    # wages from person's first job, wages from spouse's job
    return If(is_single(person), wages_from_second_job(person), wages_from_second_job(person) + persons_wages(spouse))


def has_only_one_job(person):
    return count_of_jobs(person) == 1


# certainty < 1, is single single or is single/widowed single?
def is_single(p):
    return Or(marital_status(p) == "Single, unmarried, or legally separated",
              marital_status(p) == "Widowed (spouse died during the tax year)",
              marital_status(p) == "Widowed (spouse died before the tax year)")

# def highest_earning_job_from_couple(person, spouse):
#     # need temporal max function?
#     return Max(highest_earning_job_wages(person), highest_earning_job_wages(spouse))


def two_earners_mult_jobs_wksht_table_2_married_joint_lookup(wages):
    return If(wages <= 24900, 420,
              wages <= 84450, 500,
              wages <= 173900, 910,
              wages <= 326950, 1000,
              wages <= 413700, 1330,
              wages <= 617851, 1450,
              1540)


def two_earners_mult_jobs_wksht_table_2_all_others_lookup(wages):
    return If(wages <= 7200, 420,
              wages <= 36975, 500,
              wages <= 81700, 910,
              wages <= 158225, 1000,
              wages <= 201600, 1330,
              wages <= 507800, 1450,
              1540)


def two_earners_mult_jobs_wksht_table_1_married_joint_lookup(wages):
    return If(wages <= 5000, 0,
              wages <= 9500, 1,
              wages <= 19500, 2,
              wages <= 35000, 3,
              wages <= 40000, 4,
              wages <= 46000, 5,
              wages <= 55000, 6,
              wages <= 60000, 7,
              wages <= 70000, 8,
              wages <= 75000, 9,
              wages <= 85000, 10,
              wages <= 95000, 11,
              wages <= 125000, 12,
              wages <= 155000, 13,
              wages <= 165000, 14,
              wages <= 175000, 15,
              wages <= 180000, 16,
              wages <= 195000, 17,
              wages <= 205000, 18,
              19)


def two_earners_mult_jobs_wksht_table_1_all_others_lookup(wages):
    return If(wages <= 7000, 0,
              wages <= 13000, 1,
              wages <= 27500, 2,
              wages <= 32000, 3,
              wages <= 40000, 4,
              wages <= 60000, 5,
              wages <= 75000, 6,
              wages <= 85000, 7,
              wages <= 95000, 8,
              wages <= 100000, 9,
              wages <= 110000, 10,
              wages <= 115000, 11,
              wages <= 125000, 12,
              wages <= 135000, 13,
              wages <= 145000, 14,
              wages <= 160000, 15,
              wages <= 180000, 16,
              17)


############### base input rules ###############
# base level attributes? Can we make these "fall out"?
def is_married(person, spouse):
    return marital_status(person) == "Married"


def marital_status(p):
    return(In("str", "marital_status", p, None, "What is {0}'s marital status?"))


def tax_status(p):
    return In("str", "tax_status", p, None, "How does {0} plan to file taxes?")


def head_of_household(p):
    return(In("bool", "head_of_household", p, None, "Is {0} the head of their household?"))

# converting boolean to integer for summing, is there a better pattern to employ?
def is_claiming_self(p):
    return(In("bool", "claim_self", p, None, "Does {0} intend to claim themself?"))


def employment_status(p):
    return(In("str", "employment_status", p, None, "What is {0}'s employment status?"))


def wages_from_second_job(p):
    return In("num", "second_job_wages", p, None, "What was the total sum of wages for {0} from their second job last year?")


def persons_wages(p):
    return In("num", "wages", p, None, "What was the total sum of wages for {0} last year?")


def count_of_jobs(p):
    return In("num", "number_of_jobs", p, None, "How many jobs did {0} simultaneously hold last year?")


def has_other_credits(p):
    return In("bool", "has_other_credits_pub505", p, None, "Does {0} have other credits from Worksheet 1-6 of Pub. 505?")


def other_credits_pub505(p):
    return In("num", "other_credits_pub505", p, None, "How many other credits does {0} have from Worksheet 1-6 of Pub. 505?")

# temporal?
def itemized_deductions_2019(p):
    return In("num", "itemized_deductions_2019", p, None, "Please enter the an estimate of {0}'s 2019 itemized deductions. "
              + "These include qualifying home mortgage interest, "
              + "charitable contributions, state and local taxes (up to $10,000), and medical expenses in excess of 10% of "
              + "your income. See Pub. 505 for details")


def estimate_2019_adj_to_inc_qual_bus_inc_ded_addtl_std_ded(p):
    return In("num", "itemized_deductions_2019", p, None, "Enter an estimate of {0}'s 2019 adjustments to income, "
              + "qualified business income deduction, and any additional standard deduction for age or blindness "
              + "(see Pub. 505 for information about these items) . . ")

def estimate_2019_nonwage_inc_not_subj_to_withholding(p):
    return In("num", "itemized_deductions_2019", p, None, "Enter an estimate of {0}'s 2019 nonwage income not subject to withholding (such as dividends or interest)")

def highest_earning_job_wages(p):
    return In("num", "highest_earning_job_total_wages", p, None, "Enter the wages from {0}'s highest earning job.")

def plans_to_itemize_or_claim_adjustments(p):
    return In("bool", "plans_to_itemize_or_claim_adjustments", p, None, "Does {0} plan  to itemize or claim adjustments to income and want to reduce "
        + "their withholding, or if do they have a large amount of nonwage income not subject to withholding and want to increase their withholding.")

def couple_both_work(p, s):
    return In("bool", "couple_both_work", p, s, "Do {0} and {1} both work?")

def num_pay_periods_remaining_in_year(p):
    return In("num", "pay_periods_remaining", p, None, "Enter the number of pay periods remaining in the year for {0}, " +
    "For example, divide by 18 if you’re paid every 2 weeks and you complete this form on a date in late April when " +
    "there are 18 pay periods remaining in the year")

def total_income(p):
    return In("num", "total_income", p, None, "Enter the total expected annual income for {0}")

def num_children(p):
    return In("num", "number_children_pub_972", p, None, "Enter the number of eligible children from Publication 972, Child Tax Credit for {0}")

def num_dependents(p):
    return In("num", "num_dep_pub_972", p, None, "Enter the number of eligible dependents from Publication 972, Child Tax Credit for {0}")

def qualifying_widower(p):
    return In("bool", "qualifying_widower", p, None, "Is {0} a qualifying widower?")