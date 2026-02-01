package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * W-2 wage and tax statement data for ATS scenarios.
 */
public class ATSW2Data {
    @JsonProperty("employeeName")
    private String employeeName;

    @JsonProperty("employerName")
    private String employerName;

    @JsonProperty("employerEin")
    private String employerEin;

    @JsonProperty("employerAddress")
    private ATSAddress employerAddress;

    // Box 1: Wages, tips, other compensation
    @JsonProperty("wages")
    private BigDecimal wages = BigDecimal.ZERO;

    // Box 2: Federal income tax withheld
    @JsonProperty("federalWithholding")
    private BigDecimal federalWithholding = BigDecimal.ZERO;

    // Box 3: Social security wages
    @JsonProperty("ssWages")
    private BigDecimal ssWages = BigDecimal.ZERO;

    // Box 4: Social security tax withheld
    @JsonProperty("ssTax")
    private BigDecimal ssTax = BigDecimal.ZERO;

    // Box 5: Medicare wages and tips
    @JsonProperty("medicareWages")
    private BigDecimal medicareWages = BigDecimal.ZERO;

    // Box 6: Medicare tax withheld
    @JsonProperty("medicareTax")
    private BigDecimal medicareTax = BigDecimal.ZERO;

    // Box 7: Social security tips
    @JsonProperty("ssTips")
    private BigDecimal ssTips = BigDecimal.ZERO;

    // Box 8: Allocated tips
    @JsonProperty("allocatedTips")
    private BigDecimal allocatedTips = BigDecimal.ZERO;

    // Box 10: Dependent care benefits
    @JsonProperty("dependentCareBenefits")
    private BigDecimal dependentCareBenefits = BigDecimal.ZERO;

    // Box 11: Nonqualified plans
    @JsonProperty("nonqualifiedPlans")
    private BigDecimal nonqualifiedPlans = BigDecimal.ZERO;

    // Box 12: Codes (simplified as single code/amount for now)
    @JsonProperty("box12Code")
    private String box12Code;

    @JsonProperty("box12Amount")
    private BigDecimal box12Amount = BigDecimal.ZERO;

    // Box 12: Multiple codes (extended format)
    @JsonProperty("box12Codes")
    private List<Map<String, Object>> box12Codes;

    // Box 14: Other (can be String or List<Map<String, Object>>)
    @JsonProperty("box14Other")
    private Object box14Other;

    // Box 10: Dependent care benefits (alternative field name)
    @JsonProperty("box10DependentCareBenefits")
    private BigDecimal box10DependentCareBenefits = BigDecimal.ZERO;

    // Military W-2 flag
    @JsonProperty("isMilitaryW2")
    private boolean isMilitaryW2;

    // Combat pay (for military W-2s)
    @JsonProperty("combatPay")
    private BigDecimal combatPay = BigDecimal.ZERO;

    // Clergy W-2 flag
    @JsonProperty("isClergyW2")
    private boolean isClergyW2;

    // Box 13: Checkboxes
    @JsonProperty("statutoryEmployee")
    private boolean statutoryEmployee;

    @JsonProperty("retirementPlan")
    private boolean retirementPlan;

    @JsonProperty("thirdPartySickPay")
    private boolean thirdPartySickPay;

    // State information (Boxes 15-17)
    @JsonProperty("state")
    private String state;

    @JsonProperty("stateId")
    private String stateId;

    @JsonProperty("stateWages")
    private BigDecimal stateWages = BigDecimal.ZERO;

    @JsonProperty("stateTax")
    private BigDecimal stateTax = BigDecimal.ZERO;

    // Local information (Boxes 18-20)
    @JsonProperty("localWages")
    private BigDecimal localWages = BigDecimal.ZERO;

    @JsonProperty("localTax")
    private BigDecimal localTax = BigDecimal.ZERO;

    @JsonProperty("localityName")
    private String localityName;

    public ATSW2Data() {}

    // Getters and Setters
    public String getEmployeeName() { return employeeName; }
    public void setEmployeeName(String employeeName) { this.employeeName = employeeName; }

    public String getEmployerName() { return employerName; }
    public void setEmployerName(String employerName) { this.employerName = employerName; }

    public String getEmployerEin() { return employerEin; }
    public void setEmployerEin(String employerEin) { this.employerEin = employerEin; }

    /**
     * Get employer EIN without dashes (9 digits).
     */
    public String getEmployerEinClean() {
        if (employerEin == null) return null;
        return employerEin.replace("-", "");
    }

    public ATSAddress getEmployerAddress() { return employerAddress; }
    public void setEmployerAddress(ATSAddress employerAddress) { this.employerAddress = employerAddress; }

    public BigDecimal getWages() { return wages; }
    public void setWages(BigDecimal wages) { this.wages = wages; }

    public BigDecimal getFederalWithholding() { return federalWithholding; }
    public void setFederalWithholding(BigDecimal federalWithholding) { this.federalWithholding = federalWithholding; }

    public BigDecimal getSsWages() { return ssWages; }
    public void setSsWages(BigDecimal ssWages) { this.ssWages = ssWages; }

    public BigDecimal getSsTax() { return ssTax; }
    public void setSsTax(BigDecimal ssTax) { this.ssTax = ssTax; }

    public BigDecimal getMedicareWages() { return medicareWages; }
    public void setMedicareWages(BigDecimal medicareWages) { this.medicareWages = medicareWages; }

    public BigDecimal getMedicareTax() { return medicareTax; }
    public void setMedicareTax(BigDecimal medicareTax) { this.medicareTax = medicareTax; }

    public BigDecimal getSsTips() { return ssTips; }
    public void setSsTips(BigDecimal ssTips) { this.ssTips = ssTips; }

    public BigDecimal getAllocatedTips() { return allocatedTips; }
    public void setAllocatedTips(BigDecimal allocatedTips) { this.allocatedTips = allocatedTips; }

    public BigDecimal getDependentCareBenefits() { return dependentCareBenefits; }
    public void setDependentCareBenefits(BigDecimal dependentCareBenefits) { this.dependentCareBenefits = dependentCareBenefits; }

    public BigDecimal getNonqualifiedPlans() { return nonqualifiedPlans; }
    public void setNonqualifiedPlans(BigDecimal nonqualifiedPlans) { this.nonqualifiedPlans = nonqualifiedPlans; }

    public String getBox12Code() { return box12Code; }
    public void setBox12Code(String box12Code) { this.box12Code = box12Code; }

    public BigDecimal getBox12Amount() { return box12Amount; }
    public void setBox12Amount(BigDecimal box12Amount) { this.box12Amount = box12Amount; }

    public List<Map<String, Object>> getBox12Codes() { return box12Codes; }
    public void setBox12Codes(List<Map<String, Object>> box12Codes) { this.box12Codes = box12Codes; }

    public Object getBox14Other() { return box14Other; }
    public void setBox14Other(Object box14Other) { this.box14Other = box14Other; }

    public BigDecimal getBox10DependentCareBenefits() { return box10DependentCareBenefits; }
    public void setBox10DependentCareBenefits(BigDecimal box10DependentCareBenefits) { this.box10DependentCareBenefits = box10DependentCareBenefits; }

    public boolean isMilitaryW2() { return isMilitaryW2; }
    public void setMilitaryW2(boolean militaryW2) { isMilitaryW2 = militaryW2; }

    public boolean isStatutoryEmployee() { return statutoryEmployee; }
    public void setStatutoryEmployee(boolean statutoryEmployee) { this.statutoryEmployee = statutoryEmployee; }

    public boolean isRetirementPlan() { return retirementPlan; }
    public void setRetirementPlan(boolean retirementPlan) { this.retirementPlan = retirementPlan; }

    public boolean isThirdPartySickPay() { return thirdPartySickPay; }
    public void setThirdPartySickPay(boolean thirdPartySickPay) { this.thirdPartySickPay = thirdPartySickPay; }

    public String getState() { return state; }
    public void setState(String state) { this.state = state; }

    public String getStateId() { return stateId; }
    public void setStateId(String stateId) { this.stateId = stateId; }

    public BigDecimal getStateWages() { return stateWages; }
    public void setStateWages(BigDecimal stateWages) { this.stateWages = stateWages; }

    public BigDecimal getStateTax() { return stateTax; }
    public void setStateTax(BigDecimal stateTax) { this.stateTax = stateTax; }

    public BigDecimal getLocalWages() { return localWages; }
    public void setLocalWages(BigDecimal localWages) { this.localWages = localWages; }

    public BigDecimal getLocalTax() { return localTax; }
    public void setLocalTax(BigDecimal localTax) { this.localTax = localTax; }

    public String getLocalityName() { return localityName; }
    public void setLocalityName(String localityName) { this.localityName = localityName; }

    public BigDecimal getCombatPay() { return combatPay; }
    public void setCombatPay(BigDecimal combatPay) { this.combatPay = combatPay; }

    public boolean isClergyW2() { return isClergyW2; }
    public void setClergyW2(boolean clergyW2) { isClergyW2 = clergyW2; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ATSW2Data that = (ATSW2Data) o;
        return Objects.equals(employerEin, that.employerEin) &&
               Objects.equals(employeeName, that.employeeName) &&
               Objects.equals(wages, that.wages);
    }

    @Override
    public int hashCode() {
        return Objects.hash(employerEin, employeeName, wages);
    }
}
