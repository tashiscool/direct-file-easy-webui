package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

/**
 * Expected tax calculation values for ATS scenario validation.
 *
 * These values represent the IRS-expected outcomes from each ATS scenario
 * and are used to validate that our tax calculations match.
 */
public class ATSExpectedValues {
    // Income
    @JsonProperty("totalWages")
    private BigDecimal totalWages = BigDecimal.ZERO;

    @JsonProperty("totalIncome")
    private BigDecimal totalIncome = BigDecimal.ZERO;

    @JsonProperty("adjustmentsToIncome")
    private BigDecimal adjustmentsToIncome = BigDecimal.ZERO;

    @JsonProperty("agi")
    private BigDecimal agi = BigDecimal.ZERO;

    // Deductions
    @JsonProperty("standardDeduction")
    private BigDecimal standardDeduction = BigDecimal.ZERO;

    @JsonProperty("itemizedDeduction")
    private BigDecimal itemizedDeduction = BigDecimal.ZERO;

    @JsonProperty("qbiDeduction")
    private BigDecimal qbiDeduction = BigDecimal.ZERO;

    @JsonProperty("totalDeductions")
    private BigDecimal totalDeductions = BigDecimal.ZERO;

    // Taxable income and tax
    @JsonProperty("taxableIncome")
    private BigDecimal taxableIncome = BigDecimal.ZERO;

    @JsonProperty("taxFromTaxTable")
    private BigDecimal taxFromTaxTable = BigDecimal.ZERO;

    @JsonProperty("schedule2AdditionalTax")
    private BigDecimal schedule2AdditionalTax = BigDecimal.ZERO;

    @JsonProperty("totalTaxBeforeCredits")
    private BigDecimal totalTaxBeforeCredits = BigDecimal.ZERO;

    // Credits
    @JsonProperty("childTaxCredit")
    private BigDecimal childTaxCredit = BigDecimal.ZERO;

    @JsonProperty("schedule3Credits")
    private BigDecimal schedule3Credits = BigDecimal.ZERO;

    @JsonProperty("totalCredits")
    private BigDecimal totalCredits = BigDecimal.ZERO;

    @JsonProperty("taxAfterCredits")
    private BigDecimal taxAfterCredits = BigDecimal.ZERO;

    // Self-employment
    @JsonProperty("selfEmploymentTax")
    private BigDecimal selfEmploymentTax = BigDecimal.ZERO;

    @JsonProperty("selfEmploymentDeduction")
    private BigDecimal selfEmploymentDeduction = BigDecimal.ZERO;

    // Final amounts
    @JsonProperty("totalTax")
    private BigDecimal totalTax = BigDecimal.ZERO;

    @JsonProperty("totalPayments")
    private BigDecimal totalPayments = BigDecimal.ZERO;

    @JsonProperty("federalWithholding")
    private BigDecimal federalWithholding = BigDecimal.ZERO;

    @JsonProperty("refund")
    private BigDecimal refund = BigDecimal.ZERO;

    @JsonProperty("amountOwed")
    private BigDecimal amountOwed = BigDecimal.ZERO;

    // EIC-related
    @JsonProperty("earnedIncomeCredit")
    private BigDecimal earnedIncomeCredit = BigDecimal.ZERO;

    @JsonProperty("additionalChildTaxCredit")
    private BigDecimal additionalChildTaxCredit = BigDecimal.ZERO;

    // Extended scenario expected values
    @JsonProperty("cleanVehicleCredit")
    private BigDecimal cleanVehicleCredit = BigDecimal.ZERO;

    @JsonProperty("estimatedTaxPayments")
    private BigDecimal estimatedTaxPayments = BigDecimal.ZERO;

    @JsonProperty("gamblingWinnings")
    private BigDecimal gamblingWinnings = BigDecimal.ZERO;

    @JsonProperty("partnershipIncome")
    private BigDecimal partnershipIncome = BigDecimal.ZERO;

    @JsonProperty("rentalIncome")
    private BigDecimal rentalIncome = BigDecimal.ZERO;

    @JsonProperty("residentialCleanEnergyCredit")
    private BigDecimal residentialCleanEnergyCredit = BigDecimal.ZERO;

    @JsonProperty("unemploymentCompensation")
    private BigDecimal unemploymentCompensation = BigDecimal.ZERO;

    @JsonProperty("interestIncome")
    private BigDecimal interestIncome = BigDecimal.ZERO;

    @JsonProperty("dividendIncome")
    private BigDecimal dividendIncome = BigDecimal.ZERO;

    @JsonProperty("capitalGains")
    private BigDecimal capitalGains = BigDecimal.ZERO;

    @JsonProperty("socialSecurityBenefits")
    private BigDecimal socialSecurityBenefits = BigDecimal.ZERO;

    @JsonProperty("taxableSocialSecurity")
    private BigDecimal taxableSocialSecurity = BigDecimal.ZERO;

    @JsonProperty("iraDeduction")
    private BigDecimal iraDeduction = BigDecimal.ZERO;

    @JsonProperty("hsaDeduction")
    private BigDecimal hsaDeduction = BigDecimal.ZERO;

    @JsonProperty("educationCredit")
    private BigDecimal educationCredit = BigDecimal.ZERO;

    @JsonProperty("foreignTaxCredit")
    private BigDecimal foreignTaxCredit = BigDecimal.ZERO;

    @JsonProperty("childCareCareCredit")
    private BigDecimal childCareCredit = BigDecimal.ZERO;

    @JsonProperty("premiumTaxCredit")
    private BigDecimal premiumTaxCredit = BigDecimal.ZERO;

    @JsonProperty("netInvestmentIncomeTax")
    private BigDecimal netInvestmentIncomeTax = BigDecimal.ZERO;

    @JsonProperty("additionalMedicareTax")
    private BigDecimal additionalMedicareTax = BigDecimal.ZERO;

    @JsonProperty("amt")
    private BigDecimal amt = BigDecimal.ZERO;

    @JsonProperty("regularTax")
    private BigDecimal regularTax = BigDecimal.ZERO;

    @JsonProperty("deductibleSETax")
    private BigDecimal deductibleSETax = BigDecimal.ZERO;

    @JsonProperty("partnershipDeductions")
    private BigDecimal partnershipDeductions = BigDecimal.ZERO;

    @JsonProperty("energyEfficientHomeCredit")
    private BigDecimal energyEfficientHomeCredit = BigDecimal.ZERO;

    @JsonProperty("taxOnOrdinaryIncome")
    private BigDecimal taxOnOrdinaryIncome = BigDecimal.ZERO;

    @JsonProperty("qualifiedDividends")
    private BigDecimal qualifiedDividends = BigDecimal.ZERO;

    @JsonProperty("educatorExpenses")
    private BigDecimal educatorExpenses = BigDecimal.ZERO;

    @JsonProperty("combatZoneService")
    private BigDecimal combatZoneService = BigDecimal.ZERO;

    @JsonProperty("taxTreatyCountry")
    private String taxTreatyCountry;

    @JsonProperty("stakingRewards")
    private BigDecimal stakingRewards = BigDecimal.ZERO;

    @JsonProperty("box10DependentCareBenefits")
    private BigDecimal box10DependentCareBenefits = BigDecimal.ZERO;

    @JsonProperty("taxOnQualifiedDividends")
    private BigDecimal taxOnQualifiedDividends = BigDecimal.ZERO;

    @JsonProperty("taxOnQualifiedDividendsCapGains")
    private BigDecimal taxOnQualifiedDividendsCapGains = BigDecimal.ZERO;

    @JsonProperty("educatorExpenseDeduction")
    private BigDecimal educatorExpenseDeduction = BigDecimal.ZERO;

    @JsonProperty("studentLoanInterestDeduction")
    private BigDecimal studentLoanInterestDeduction = BigDecimal.ZERO;

    @JsonProperty("aotcCredit")
    private BigDecimal aotcCredit = BigDecimal.ZERO;

    @JsonProperty("businessIncome")
    private BigDecimal businessIncome = BigDecimal.ZERO;

    @JsonProperty("dependentCareBenefitsExcluded")
    private BigDecimal dependentCareBenefitsExcluded = BigDecimal.ZERO;

    @JsonProperty("stakingIncome")
    private BigDecimal stakingIncome = BigDecimal.ZERO;

    @JsonProperty("childAndDependentCareCredit")
    private BigDecimal childAndDependentCareCredit = BigDecimal.ZERO;

    @JsonProperty("combatPay")
    private BigDecimal combatPay = BigDecimal.ZERO;

    @JsonProperty("refundableAotc")
    private BigDecimal refundableAotc = BigDecimal.ZERO;

    @JsonProperty("scholarshipIncome")
    private BigDecimal scholarshipIncome = BigDecimal.ZERO;

    @JsonProperty("selfEmployedHealthInsurance")
    private BigDecimal selfEmployedHealthInsurance = BigDecimal.ZERO;

    @JsonProperty("shortTermCapitalGains")
    private BigDecimal shortTermCapitalGains = BigDecimal.ZERO;

    @JsonProperty("longTermCapitalGains")
    private BigDecimal longTermCapitalGains = BigDecimal.ZERO;

    @JsonProperty("nonrefundableAotc")
    private BigDecimal nonrefundableAotc = BigDecimal.ZERO;

    @JsonProperty("excessAdvancePtcRepayment")
    private BigDecimal excessAdvancePtcRepayment = BigDecimal.ZERO;

    @JsonProperty("pensionIncome")
    private BigDecimal pensionIncome = BigDecimal.ZERO;

    @JsonProperty("refundableCredits")
    private BigDecimal refundableCredits = BigDecimal.ZERO;

    @JsonProperty("netCapitalGain")
    private BigDecimal netCapitalGain = BigDecimal.ZERO;

    @JsonProperty("taxOnLongTermCapGains")
    private BigDecimal taxOnLongTermCapGains = BigDecimal.ZERO;

    @JsonProperty("stipendIncome")
    private BigDecimal stipendIncome = BigDecimal.ZERO;

    @JsonProperty("housingAllowanceExclusion")
    private BigDecimal housingAllowanceExclusion = BigDecimal.ZERO;

    @JsonProperty("taxableWages")
    private BigDecimal taxableWages = BigDecimal.ZERO;

    @JsonProperty("combatPayExclusion")
    private BigDecimal combatPayExclusion = BigDecimal.ZERO;

    @JsonProperty("taxableScholarship")
    private BigDecimal taxableScholarship = BigDecimal.ZERO;

    @JsonProperty("adjustedWages")
    private BigDecimal adjustedWages = BigDecimal.ZERO;

    @JsonProperty("taxTreatyExemption")
    private BigDecimal taxTreatyExemption = BigDecimal.ZERO;

    @JsonProperty("movingExpenseDeduction")
    private BigDecimal movingExpenseDeduction = BigDecimal.ZERO;

    public ATSExpectedValues() {}

    // Getters and Setters
    public BigDecimal getTotalWages() { return totalWages; }
    public void setTotalWages(BigDecimal totalWages) { this.totalWages = totalWages; }

    public BigDecimal getTotalIncome() { return totalIncome; }
    public void setTotalIncome(BigDecimal totalIncome) { this.totalIncome = totalIncome; }

    public BigDecimal getAdjustmentsToIncome() { return adjustmentsToIncome; }
    public void setAdjustmentsToIncome(BigDecimal adjustmentsToIncome) { this.adjustmentsToIncome = adjustmentsToIncome; }

    public BigDecimal getAgi() { return agi; }
    public void setAgi(BigDecimal agi) { this.agi = agi; }

    public BigDecimal getStandardDeduction() { return standardDeduction; }
    public void setStandardDeduction(BigDecimal standardDeduction) { this.standardDeduction = standardDeduction; }

    public BigDecimal getItemizedDeduction() { return itemizedDeduction; }
    public void setItemizedDeduction(BigDecimal itemizedDeduction) { this.itemizedDeduction = itemizedDeduction; }

    public BigDecimal getQbiDeduction() { return qbiDeduction; }
    public void setQbiDeduction(BigDecimal qbiDeduction) { this.qbiDeduction = qbiDeduction; }

    public BigDecimal getTotalDeductions() { return totalDeductions; }
    public void setTotalDeductions(BigDecimal totalDeductions) { this.totalDeductions = totalDeductions; }

    public BigDecimal getTaxableIncome() { return taxableIncome; }
    public void setTaxableIncome(BigDecimal taxableIncome) { this.taxableIncome = taxableIncome; }

    public BigDecimal getTaxFromTaxTable() { return taxFromTaxTable; }
    public void setTaxFromTaxTable(BigDecimal taxFromTaxTable) { this.taxFromTaxTable = taxFromTaxTable; }

    public BigDecimal getSchedule2AdditionalTax() { return schedule2AdditionalTax; }
    public void setSchedule2AdditionalTax(BigDecimal schedule2AdditionalTax) { this.schedule2AdditionalTax = schedule2AdditionalTax; }

    public BigDecimal getTotalTaxBeforeCredits() { return totalTaxBeforeCredits; }
    public void setTotalTaxBeforeCredits(BigDecimal totalTaxBeforeCredits) { this.totalTaxBeforeCredits = totalTaxBeforeCredits; }

    public BigDecimal getChildTaxCredit() { return childTaxCredit; }
    public void setChildTaxCredit(BigDecimal childTaxCredit) { this.childTaxCredit = childTaxCredit; }

    public BigDecimal getSchedule3Credits() { return schedule3Credits; }
    public void setSchedule3Credits(BigDecimal schedule3Credits) { this.schedule3Credits = schedule3Credits; }

    public BigDecimal getTotalCredits() { return totalCredits; }
    public void setTotalCredits(BigDecimal totalCredits) { this.totalCredits = totalCredits; }

    public BigDecimal getTaxAfterCredits() { return taxAfterCredits; }
    public void setTaxAfterCredits(BigDecimal taxAfterCredits) { this.taxAfterCredits = taxAfterCredits; }

    public BigDecimal getSelfEmploymentTax() { return selfEmploymentTax; }
    public void setSelfEmploymentTax(BigDecimal selfEmploymentTax) { this.selfEmploymentTax = selfEmploymentTax; }

    public BigDecimal getSelfEmploymentDeduction() { return selfEmploymentDeduction; }
    public void setSelfEmploymentDeduction(BigDecimal selfEmploymentDeduction) { this.selfEmploymentDeduction = selfEmploymentDeduction; }

    public BigDecimal getTotalTax() { return totalTax; }
    public void setTotalTax(BigDecimal totalTax) { this.totalTax = totalTax; }

    public BigDecimal getTotalPayments() { return totalPayments; }
    public void setTotalPayments(BigDecimal totalPayments) { this.totalPayments = totalPayments; }

    public BigDecimal getFederalWithholding() { return federalWithholding; }
    public void setFederalWithholding(BigDecimal federalWithholding) { this.federalWithholding = federalWithholding; }

    public BigDecimal getRefund() { return refund; }
    public void setRefund(BigDecimal refund) { this.refund = refund; }

    public BigDecimal getAmountOwed() { return amountOwed; }
    public void setAmountOwed(BigDecimal amountOwed) { this.amountOwed = amountOwed; }

    public BigDecimal getEarnedIncomeCredit() { return earnedIncomeCredit; }
    public void setEarnedIncomeCredit(BigDecimal earnedIncomeCredit) { this.earnedIncomeCredit = earnedIncomeCredit; }

    public BigDecimal getAdditionalChildTaxCredit() { return additionalChildTaxCredit; }
    public void setAdditionalChildTaxCredit(BigDecimal additionalChildTaxCredit) { this.additionalChildTaxCredit = additionalChildTaxCredit; }

    public BigDecimal getCleanVehicleCredit() { return cleanVehicleCredit; }
    public void setCleanVehicleCredit(BigDecimal cleanVehicleCredit) { this.cleanVehicleCredit = cleanVehicleCredit; }

    public BigDecimal getEstimatedTaxPayments() { return estimatedTaxPayments; }
    public void setEstimatedTaxPayments(BigDecimal estimatedTaxPayments) { this.estimatedTaxPayments = estimatedTaxPayments; }

    public BigDecimal getGamblingWinnings() { return gamblingWinnings; }
    public void setGamblingWinnings(BigDecimal gamblingWinnings) { this.gamblingWinnings = gamblingWinnings; }

    public BigDecimal getPartnershipIncome() { return partnershipIncome; }
    public void setPartnershipIncome(BigDecimal partnershipIncome) { this.partnershipIncome = partnershipIncome; }

    public BigDecimal getRentalIncome() { return rentalIncome; }
    public void setRentalIncome(BigDecimal rentalIncome) { this.rentalIncome = rentalIncome; }

    public BigDecimal getResidentialCleanEnergyCredit() { return residentialCleanEnergyCredit; }
    public void setResidentialCleanEnergyCredit(BigDecimal residentialCleanEnergyCredit) { this.residentialCleanEnergyCredit = residentialCleanEnergyCredit; }

    public BigDecimal getUnemploymentCompensation() { return unemploymentCompensation; }
    public void setUnemploymentCompensation(BigDecimal unemploymentCompensation) { this.unemploymentCompensation = unemploymentCompensation; }

    public BigDecimal getInterestIncome() { return interestIncome; }
    public void setInterestIncome(BigDecimal interestIncome) { this.interestIncome = interestIncome; }

    public BigDecimal getDividendIncome() { return dividendIncome; }
    public void setDividendIncome(BigDecimal dividendIncome) { this.dividendIncome = dividendIncome; }

    public BigDecimal getCapitalGains() { return capitalGains; }
    public void setCapitalGains(BigDecimal capitalGains) { this.capitalGains = capitalGains; }

    public BigDecimal getSocialSecurityBenefits() { return socialSecurityBenefits; }
    public void setSocialSecurityBenefits(BigDecimal socialSecurityBenefits) { this.socialSecurityBenefits = socialSecurityBenefits; }

    public BigDecimal getTaxableSocialSecurity() { return taxableSocialSecurity; }
    public void setTaxableSocialSecurity(BigDecimal taxableSocialSecurity) { this.taxableSocialSecurity = taxableSocialSecurity; }

    public BigDecimal getIraDeduction() { return iraDeduction; }
    public void setIraDeduction(BigDecimal iraDeduction) { this.iraDeduction = iraDeduction; }

    public BigDecimal getHsaDeduction() { return hsaDeduction; }
    public void setHsaDeduction(BigDecimal hsaDeduction) { this.hsaDeduction = hsaDeduction; }

    public BigDecimal getEducationCredit() { return educationCredit; }
    public void setEducationCredit(BigDecimal educationCredit) { this.educationCredit = educationCredit; }

    public BigDecimal getForeignTaxCredit() { return foreignTaxCredit; }
    public void setForeignTaxCredit(BigDecimal foreignTaxCredit) { this.foreignTaxCredit = foreignTaxCredit; }

    public BigDecimal getChildCareCredit() { return childCareCredit; }
    public void setChildCareCredit(BigDecimal childCareCredit) { this.childCareCredit = childCareCredit; }

    public BigDecimal getPremiumTaxCredit() { return premiumTaxCredit; }
    public void setPremiumTaxCredit(BigDecimal premiumTaxCredit) { this.premiumTaxCredit = premiumTaxCredit; }

    public BigDecimal getNetInvestmentIncomeTax() { return netInvestmentIncomeTax; }
    public void setNetInvestmentIncomeTax(BigDecimal netInvestmentIncomeTax) { this.netInvestmentIncomeTax = netInvestmentIncomeTax; }

    public BigDecimal getAdditionalMedicareTax() { return additionalMedicareTax; }
    public void setAdditionalMedicareTax(BigDecimal additionalMedicareTax) { this.additionalMedicareTax = additionalMedicareTax; }

    public BigDecimal getAmt() { return amt; }
    public void setAmt(BigDecimal amt) { this.amt = amt; }

    public BigDecimal getRegularTax() { return regularTax; }
    public void setRegularTax(BigDecimal regularTax) { this.regularTax = regularTax; }

    public BigDecimal getDeductibleSETax() { return deductibleSETax; }
    public void setDeductibleSETax(BigDecimal deductibleSETax) { this.deductibleSETax = deductibleSETax; }

    public BigDecimal getPartnershipDeductions() { return partnershipDeductions; }
    public void setPartnershipDeductions(BigDecimal partnershipDeductions) { this.partnershipDeductions = partnershipDeductions; }

    public BigDecimal getEnergyEfficientHomeCredit() { return energyEfficientHomeCredit; }
    public void setEnergyEfficientHomeCredit(BigDecimal energyEfficientHomeCredit) { this.energyEfficientHomeCredit = energyEfficientHomeCredit; }

    public BigDecimal getTaxOnOrdinaryIncome() { return taxOnOrdinaryIncome; }
    public void setTaxOnOrdinaryIncome(BigDecimal taxOnOrdinaryIncome) { this.taxOnOrdinaryIncome = taxOnOrdinaryIncome; }

    public BigDecimal getQualifiedDividends() { return qualifiedDividends; }
    public void setQualifiedDividends(BigDecimal qualifiedDividends) { this.qualifiedDividends = qualifiedDividends; }

    public BigDecimal getEducatorExpenses() { return educatorExpenses; }
    public void setEducatorExpenses(BigDecimal educatorExpenses) { this.educatorExpenses = educatorExpenses; }

    public BigDecimal getCombatZoneService() { return combatZoneService; }
    public void setCombatZoneService(BigDecimal combatZoneService) { this.combatZoneService = combatZoneService; }

    public String getTaxTreatyCountry() { return taxTreatyCountry; }
    public void setTaxTreatyCountry(String taxTreatyCountry) { this.taxTreatyCountry = taxTreatyCountry; }

    public BigDecimal getStakingRewards() { return stakingRewards; }
    public void setStakingRewards(BigDecimal stakingRewards) { this.stakingRewards = stakingRewards; }

    public BigDecimal getBox10DependentCareBenefits() { return box10DependentCareBenefits; }
    public void setBox10DependentCareBenefits(BigDecimal box10DependentCareBenefits) { this.box10DependentCareBenefits = box10DependentCareBenefits; }

    public BigDecimal getTaxOnQualifiedDividends() { return taxOnQualifiedDividends; }
    public void setTaxOnQualifiedDividends(BigDecimal taxOnQualifiedDividends) { this.taxOnQualifiedDividends = taxOnQualifiedDividends; }

    public BigDecimal getTaxOnQualifiedDividendsCapGains() { return taxOnQualifiedDividendsCapGains; }
    public void setTaxOnQualifiedDividendsCapGains(BigDecimal taxOnQualifiedDividendsCapGains) { this.taxOnQualifiedDividendsCapGains = taxOnQualifiedDividendsCapGains; }

    public BigDecimal getEducatorExpenseDeduction() { return educatorExpenseDeduction; }
    public void setEducatorExpenseDeduction(BigDecimal educatorExpenseDeduction) { this.educatorExpenseDeduction = educatorExpenseDeduction; }

    public BigDecimal getStudentLoanInterestDeduction() { return studentLoanInterestDeduction; }
    public void setStudentLoanInterestDeduction(BigDecimal studentLoanInterestDeduction) { this.studentLoanInterestDeduction = studentLoanInterestDeduction; }

    public BigDecimal getAotcCredit() { return aotcCredit; }
    public void setAotcCredit(BigDecimal aotcCredit) { this.aotcCredit = aotcCredit; }

    public BigDecimal getBusinessIncome() { return businessIncome; }
    public void setBusinessIncome(BigDecimal businessIncome) { this.businessIncome = businessIncome; }

    public BigDecimal getDependentCareBenefitsExcluded() { return dependentCareBenefitsExcluded; }
    public void setDependentCareBenefitsExcluded(BigDecimal dependentCareBenefitsExcluded) { this.dependentCareBenefitsExcluded = dependentCareBenefitsExcluded; }

    public BigDecimal getStakingIncome() { return stakingIncome; }
    public void setStakingIncome(BigDecimal stakingIncome) { this.stakingIncome = stakingIncome; }

    public BigDecimal getChildAndDependentCareCredit() { return childAndDependentCareCredit; }
    public void setChildAndDependentCareCredit(BigDecimal childAndDependentCareCredit) { this.childAndDependentCareCredit = childAndDependentCareCredit; }

    public BigDecimal getCombatPay() { return combatPay; }
    public void setCombatPay(BigDecimal combatPay) { this.combatPay = combatPay; }

    public BigDecimal getRefundableAotc() { return refundableAotc; }
    public void setRefundableAotc(BigDecimal refundableAotc) { this.refundableAotc = refundableAotc; }

    public BigDecimal getScholarshipIncome() { return scholarshipIncome; }
    public void setScholarshipIncome(BigDecimal scholarshipIncome) { this.scholarshipIncome = scholarshipIncome; }

    public BigDecimal getSelfEmployedHealthInsurance() { return selfEmployedHealthInsurance; }
    public void setSelfEmployedHealthInsurance(BigDecimal selfEmployedHealthInsurance) { this.selfEmployedHealthInsurance = selfEmployedHealthInsurance; }

    public BigDecimal getShortTermCapitalGains() { return shortTermCapitalGains; }
    public void setShortTermCapitalGains(BigDecimal shortTermCapitalGains) { this.shortTermCapitalGains = shortTermCapitalGains; }

    public BigDecimal getLongTermCapitalGains() { return longTermCapitalGains; }
    public void setLongTermCapitalGains(BigDecimal longTermCapitalGains) { this.longTermCapitalGains = longTermCapitalGains; }

    public BigDecimal getNonrefundableAotc() { return nonrefundableAotc; }
    public void setNonrefundableAotc(BigDecimal nonrefundableAotc) { this.nonrefundableAotc = nonrefundableAotc; }

    public BigDecimal getExcessAdvancePtcRepayment() { return excessAdvancePtcRepayment; }
    public void setExcessAdvancePtcRepayment(BigDecimal excessAdvancePtcRepayment) { this.excessAdvancePtcRepayment = excessAdvancePtcRepayment; }

    public BigDecimal getPensionIncome() { return pensionIncome; }
    public void setPensionIncome(BigDecimal pensionIncome) { this.pensionIncome = pensionIncome; }

    public BigDecimal getRefundableCredits() { return refundableCredits; }
    public void setRefundableCredits(BigDecimal refundableCredits) { this.refundableCredits = refundableCredits; }

    public BigDecimal getNetCapitalGain() { return netCapitalGain; }
    public void setNetCapitalGain(BigDecimal netCapitalGain) { this.netCapitalGain = netCapitalGain; }

    public BigDecimal getTaxOnLongTermCapGains() { return taxOnLongTermCapGains; }
    public void setTaxOnLongTermCapGains(BigDecimal taxOnLongTermCapGains) { this.taxOnLongTermCapGains = taxOnLongTermCapGains; }

    public BigDecimal getStipendIncome() { return stipendIncome; }
    public void setStipendIncome(BigDecimal stipendIncome) { this.stipendIncome = stipendIncome; }

    public BigDecimal getHousingAllowanceExclusion() { return housingAllowanceExclusion; }
    public void setHousingAllowanceExclusion(BigDecimal housingAllowanceExclusion) { this.housingAllowanceExclusion = housingAllowanceExclusion; }

    public BigDecimal getTaxableWages() { return taxableWages; }
    public void setTaxableWages(BigDecimal taxableWages) { this.taxableWages = taxableWages; }

    public BigDecimal getCombatPayExclusion() { return combatPayExclusion; }
    public void setCombatPayExclusion(BigDecimal combatPayExclusion) { this.combatPayExclusion = combatPayExclusion; }

    public BigDecimal getTaxableScholarship() { return taxableScholarship; }
    public void setTaxableScholarship(BigDecimal taxableScholarship) { this.taxableScholarship = taxableScholarship; }

    public BigDecimal getAdjustedWages() { return adjustedWages; }
    public void setAdjustedWages(BigDecimal adjustedWages) { this.adjustedWages = adjustedWages; }

    public BigDecimal getTaxTreatyExemption() { return taxTreatyExemption; }
    public void setTaxTreatyExemption(BigDecimal taxTreatyExemption) { this.taxTreatyExemption = taxTreatyExemption; }

    public BigDecimal getMovingExpenseDeduction() { return movingExpenseDeduction; }
    public void setMovingExpenseDeduction(BigDecimal movingExpenseDeduction) { this.movingExpenseDeduction = movingExpenseDeduction; }
}
