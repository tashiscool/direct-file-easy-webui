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
}
