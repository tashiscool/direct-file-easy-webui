package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.util.Objects;

/**
 * 1099-R distribution data for ATS scenarios.
 *
 * Form 1099-R reports distributions from pensions, annuities, retirement plans,
 * IRAs, insurance contracts, etc.
 */
public class ATS1099RData {
    @JsonProperty("payerName")
    private String payerName;

    @JsonProperty("payerEin")
    private String payerEin;

    @JsonProperty("payerAddress")
    private ATSAddress payerAddress;

    // Box 1: Gross distribution
    @JsonProperty("grossDistribution")
    private BigDecimal grossDistribution = BigDecimal.ZERO;

    // Box 2a: Taxable amount
    @JsonProperty("taxableAmount")
    private BigDecimal taxableAmount = BigDecimal.ZERO;

    // Box 2b: Taxable amount not determined
    @JsonProperty("taxableAmountNotDetermined")
    private boolean taxableAmountNotDetermined;

    // Box 2b: Total distribution
    @JsonProperty("totalDistribution")
    private boolean totalDistribution;

    // Box 3: Capital gain (included in box 2a)
    @JsonProperty("capitalGain")
    private BigDecimal capitalGain = BigDecimal.ZERO;

    // Box 4: Federal income tax withheld
    @JsonProperty("federalWithholding")
    private BigDecimal federalWithholding = BigDecimal.ZERO;

    // Box 5: Employee contributions/Designated Roth contributions or insurance premiums
    @JsonProperty("employeeContributions")
    private BigDecimal employeeContributions = BigDecimal.ZERO;

    // Box 6: Net unrealized appreciation in employer's securities
    @JsonProperty("netUnrealizedAppreciation")
    private BigDecimal netUnrealizedAppreciation = BigDecimal.ZERO;

    // Box 7: Distribution code(s)
    @JsonProperty("distributionCode")
    private String distributionCode;

    // Box 7: IRA/SEP/SIMPLE checkbox
    @JsonProperty("iraSepSimple")
    private boolean iraSepSimple;

    // Box 8: Other
    @JsonProperty("otherAmount")
    private BigDecimal otherAmount = BigDecimal.ZERO;

    // Box 9a: Your percentage of total distribution
    @JsonProperty("yourPercentage")
    private BigDecimal yourPercentage;

    // Box 9b: Total employee contributions
    @JsonProperty("totalEmployeeContributions")
    private BigDecimal totalEmployeeContributions = BigDecimal.ZERO;

    // Box 10: Amount allocable to IRR within 5 years
    @JsonProperty("irrWithin5Years")
    private BigDecimal irrWithin5Years = BigDecimal.ZERO;

    // Box 11: 1st year of desig. Roth contrib.
    @JsonProperty("firstYearRothContrib")
    private Integer firstYearRothContrib;

    // State tax information (Boxes 12-17)
    @JsonProperty("state")
    private String state;

    @JsonProperty("stateId")
    private String stateId;

    @JsonProperty("stateDistribution")
    private BigDecimal stateDistribution = BigDecimal.ZERO;

    @JsonProperty("stateTaxWithheld")
    private BigDecimal stateTaxWithheld = BigDecimal.ZERO;

    // Local tax information
    @JsonProperty("localDistribution")
    private BigDecimal localDistribution = BigDecimal.ZERO;

    @JsonProperty("localTaxWithheld")
    private BigDecimal localTaxWithheld = BigDecimal.ZERO;

    @JsonProperty("localityName")
    private String localityName;

    // Alternative field names used in some scenarios
    @JsonProperty("isIRA")
    private boolean isIRA;

    @JsonProperty("pensionPlan")
    private String pensionPlan;

    public ATS1099RData() {}

    // Getters and Setters
    public String getPayerName() { return payerName; }
    public void setPayerName(String payerName) { this.payerName = payerName; }

    public String getPayerEin() { return payerEin; }
    public void setPayerEin(String payerEin) { this.payerEin = payerEin; }

    public String getPayerEinClean() {
        if (payerEin == null) return null;
        return payerEin.replace("-", "");
    }

    public ATSAddress getPayerAddress() { return payerAddress; }
    public void setPayerAddress(ATSAddress payerAddress) { this.payerAddress = payerAddress; }

    public BigDecimal getGrossDistribution() { return grossDistribution; }
    public void setGrossDistribution(BigDecimal grossDistribution) { this.grossDistribution = grossDistribution; }

    public BigDecimal getTaxableAmount() { return taxableAmount; }
    public void setTaxableAmount(BigDecimal taxableAmount) { this.taxableAmount = taxableAmount; }

    public boolean isTaxableAmountNotDetermined() { return taxableAmountNotDetermined; }
    public void setTaxableAmountNotDetermined(boolean taxableAmountNotDetermined) { this.taxableAmountNotDetermined = taxableAmountNotDetermined; }

    public boolean isTotalDistribution() { return totalDistribution; }
    public void setTotalDistribution(boolean totalDistribution) { this.totalDistribution = totalDistribution; }

    public BigDecimal getCapitalGain() { return capitalGain; }
    public void setCapitalGain(BigDecimal capitalGain) { this.capitalGain = capitalGain; }

    public BigDecimal getFederalWithholding() { return federalWithholding; }
    public void setFederalWithholding(BigDecimal federalWithholding) { this.federalWithholding = federalWithholding; }

    public BigDecimal getEmployeeContributions() { return employeeContributions; }
    public void setEmployeeContributions(BigDecimal employeeContributions) { this.employeeContributions = employeeContributions; }

    public BigDecimal getNetUnrealizedAppreciation() { return netUnrealizedAppreciation; }
    public void setNetUnrealizedAppreciation(BigDecimal netUnrealizedAppreciation) { this.netUnrealizedAppreciation = netUnrealizedAppreciation; }

    public String getDistributionCode() { return distributionCode; }
    public void setDistributionCode(String distributionCode) { this.distributionCode = distributionCode; }

    public boolean isIraSepSimple() { return iraSepSimple; }
    public void setIraSepSimple(boolean iraSepSimple) { this.iraSepSimple = iraSepSimple; }

    public BigDecimal getOtherAmount() { return otherAmount; }
    public void setOtherAmount(BigDecimal otherAmount) { this.otherAmount = otherAmount; }

    public BigDecimal getYourPercentage() { return yourPercentage; }
    public void setYourPercentage(BigDecimal yourPercentage) { this.yourPercentage = yourPercentage; }

    public BigDecimal getTotalEmployeeContributions() { return totalEmployeeContributions; }
    public void setTotalEmployeeContributions(BigDecimal totalEmployeeContributions) { this.totalEmployeeContributions = totalEmployeeContributions; }

    public BigDecimal getIrrWithin5Years() { return irrWithin5Years; }
    public void setIrrWithin5Years(BigDecimal irrWithin5Years) { this.irrWithin5Years = irrWithin5Years; }

    public Integer getFirstYearRothContrib() { return firstYearRothContrib; }
    public void setFirstYearRothContrib(Integer firstYearRothContrib) { this.firstYearRothContrib = firstYearRothContrib; }

    public String getState() { return state; }
    public void setState(String state) { this.state = state; }

    public String getStateId() { return stateId; }
    public void setStateId(String stateId) { this.stateId = stateId; }

    public BigDecimal getStateDistribution() { return stateDistribution; }
    public void setStateDistribution(BigDecimal stateDistribution) { this.stateDistribution = stateDistribution; }

    public BigDecimal getStateTaxWithheld() { return stateTaxWithheld; }
    public void setStateTaxWithheld(BigDecimal stateTaxWithheld) { this.stateTaxWithheld = stateTaxWithheld; }

    public BigDecimal getLocalDistribution() { return localDistribution; }
    public void setLocalDistribution(BigDecimal localDistribution) { this.localDistribution = localDistribution; }

    public BigDecimal getLocalTaxWithheld() { return localTaxWithheld; }
    public void setLocalTaxWithheld(BigDecimal localTaxWithheld) { this.localTaxWithheld = localTaxWithheld; }

    public String getLocalityName() { return localityName; }
    public void setLocalityName(String localityName) { this.localityName = localityName; }

    public boolean isIRA() { return isIRA; }
    public void setIRA(boolean isIRA) { this.isIRA = isIRA; }

    public String getPensionPlan() { return pensionPlan; }
    public void setPensionPlan(String pensionPlan) { this.pensionPlan = pensionPlan; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ATS1099RData that = (ATS1099RData) o;
        return Objects.equals(payerEin, that.payerEin) &&
               Objects.equals(grossDistribution, that.grossDistribution);
    }

    @Override
    public int hashCode() {
        return Objects.hash(payerEin, grossDistribution);
    }
}
