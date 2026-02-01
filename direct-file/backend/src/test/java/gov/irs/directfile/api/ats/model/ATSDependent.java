package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDate;
import java.util.Objects;

/**
 * Dependent information for ATS scenarios.
 */
public class ATSDependent {
    @JsonProperty("firstName")
    private String firstName;

    @JsonProperty("lastName")
    private String lastName;

    @JsonProperty("ssn")
    private String ssn;

    @JsonProperty("relationship")
    private String relationship;

    @JsonProperty("dateOfBirth")
    private LocalDate dateOfBirth;

    @JsonProperty("monthsLivedWithTaxpayer")
    private int monthsLivedWithTaxpayer = 12;

    // Qualifying child (under 17 at end of year)
    @JsonProperty("qualifyingChildUnder17")
    private boolean qualifyingChildUnder17;

    // Qualifying for child tax credit
    @JsonProperty("creditForOtherDependents")
    private boolean creditForOtherDependents;

    // Qualifying for dependent care credit
    @JsonProperty("qualifyingForDependentCare")
    private boolean qualifyingForDependentCare;

    // US citizen or resident
    @JsonProperty("usCitizenOrResident")
    private boolean usCitizenOrResident = true;

    // Alternative field names used in some scenarios
    @JsonProperty("qualifiesForCTC")
    private boolean qualifiesForCTC;

    @JsonProperty("qualifiesForODC")
    private boolean qualifiesForODC;

    @JsonProperty("isFullTimeStudent")
    private boolean isFullTimeStudent;

    @JsonProperty("isDisabled")
    private boolean isDisabled;

    @JsonProperty("qualifiesForCDCC")
    private boolean qualifiesForCDCC;

    public ATSDependent() {}

    // Getters and Setters
    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public String getSsn() { return ssn; }
    public void setSsn(String ssn) { this.ssn = ssn; }

    public String getSsnClean() {
        if (ssn == null) return null;
        return ssn.replace("-", "");
    }

    public String getSsnArea() {
        String clean = getSsnClean();
        return clean != null ? clean.substring(0, 3) : null;
    }

    public String getSsnGroup() {
        String clean = getSsnClean();
        return clean != null ? clean.substring(3, 5) : null;
    }

    public String getSsnSerial() {
        String clean = getSsnClean();
        return clean != null ? clean.substring(5, 9) : null;
    }

    public String getRelationship() { return relationship; }
    public void setRelationship(String relationship) { this.relationship = relationship; }

    public LocalDate getDateOfBirth() { return dateOfBirth; }
    public void setDateOfBirth(LocalDate dateOfBirth) { this.dateOfBirth = dateOfBirth; }

    public int getMonthsLivedWithTaxpayer() { return monthsLivedWithTaxpayer; }
    public void setMonthsLivedWithTaxpayer(int monthsLivedWithTaxpayer) { this.monthsLivedWithTaxpayer = monthsLivedWithTaxpayer; }

    public boolean isQualifyingChildUnder17() { return qualifyingChildUnder17; }
    public void setQualifyingChildUnder17(boolean qualifyingChildUnder17) { this.qualifyingChildUnder17 = qualifyingChildUnder17; }

    public boolean isCreditForOtherDependents() { return creditForOtherDependents; }
    public void setCreditForOtherDependents(boolean creditForOtherDependents) { this.creditForOtherDependents = creditForOtherDependents; }

    public boolean isQualifyingForDependentCare() { return qualifyingForDependentCare; }
    public void setQualifyingForDependentCare(boolean qualifyingForDependentCare) { this.qualifyingForDependentCare = qualifyingForDependentCare; }

    public boolean isUsCitizenOrResident() { return usCitizenOrResident; }
    public void setUsCitizenOrResident(boolean usCitizenOrResident) { this.usCitizenOrResident = usCitizenOrResident; }

    public boolean isQualifiesForCTC() { return qualifiesForCTC; }
    public void setQualifiesForCTC(boolean qualifiesForCTC) { this.qualifiesForCTC = qualifiesForCTC; }

    public boolean isQualifiesForODC() { return qualifiesForODC; }
    public void setQualifiesForODC(boolean qualifiesForODC) { this.qualifiesForODC = qualifiesForODC; }

    public boolean isFullTimeStudent() { return isFullTimeStudent; }
    public void setFullTimeStudent(boolean fullTimeStudent) { isFullTimeStudent = fullTimeStudent; }

    public boolean isDisabled() { return isDisabled; }
    public void setDisabled(boolean disabled) { isDisabled = disabled; }

    public boolean isQualifiesForCDCC() { return qualifiesForCDCC; }
    public void setQualifiesForCDCC(boolean qualifiesForCDCC) { this.qualifiesForCDCC = qualifiesForCDCC; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ATSDependent that = (ATSDependent) o;
        return Objects.equals(ssn, that.ssn);
    }

    @Override
    public int hashCode() {
        return Objects.hash(ssn);
    }
}
