package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDate;
import java.util.Map;
import java.util.Objects;

/**
 * Taxpayer information for ATS scenarios.
 *
 * Represents primary or spouse taxpayer data from IRS ATS test scenarios.
 */
public class ATSTaxpayer {
    @JsonProperty("firstName")
    private String firstName;

    @JsonProperty("lastName")
    private String lastName;

    @JsonProperty("middleInitial")
    private String middleInitial;

    @JsonProperty("ssn")
    private String ssn;

    @JsonProperty("ssnAtsReference")
    private String ssnAtsReference;

    @JsonProperty("dateOfBirth")
    private LocalDate dateOfBirth;

    @JsonProperty("occupation")
    private String occupation;

    @JsonProperty("address")
    private ATSAddress address;

    @JsonProperty("isBlind")
    private boolean isBlind;

    @JsonProperty("isOver65")
    private boolean isOver65;

    @JsonProperty("isDeceased")
    private boolean isDeceased;

    @JsonProperty("dateOfDeath")
    private LocalDate dateOfDeath;

    @JsonProperty("isPrimaryFiler")
    private boolean isPrimaryFiler = true;

    // Additional taxpayer attributes for extended scenarios
    @JsonProperty("countryOfResidence")
    private String countryOfResidence;

    @JsonProperty("isFullTimeStudent")
    private boolean isFullTimeStudent;

    @JsonProperty("isMilitary")
    private boolean isMilitary;

    @JsonProperty("isClergy")
    private boolean isClergy;

    @JsonProperty("isEducator")
    private boolean isEducator;

    @JsonProperty("treatyCountry")
    private String treatyCountry;

    @JsonProperty("visaType")
    private String visaType;

    @JsonProperty("firstYearInUS")
    private Integer firstYearInUS;

    @JsonProperty("militaryBranch")
    private String militaryBranch;

    @JsonProperty("combatZoneService")
    private boolean combatZoneService;

    @JsonProperty("taxTreatyCountry")
    private String taxTreatyCountry;

    @JsonProperty("combatZoneMonths")
    private Integer combatZoneMonths;

    @JsonProperty("foreignAddress")
    private Map<String, Object> foreignAddress;

    public ATSTaxpayer() {}

    // Getters and Setters
    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public String getMiddleInitial() { return middleInitial; }
    public void setMiddleInitial(String middleInitial) { this.middleInitial = middleInitial; }

    public String getSsn() { return ssn; }
    public void setSsn(String ssn) { this.ssn = ssn; }

    /**
     * Get SSN without dashes (9 digits).
     */
    public String getSsnClean() {
        if (ssn == null) return null;
        return ssn.replace("-", "");
    }

    /**
     * Get SSN area code (first 3 digits).
     */
    public String getSsnArea() {
        String clean = getSsnClean();
        return clean != null ? clean.substring(0, 3) : null;
    }

    /**
     * Get SSN group (digits 4-5).
     */
    public String getSsnGroup() {
        String clean = getSsnClean();
        return clean != null ? clean.substring(3, 5) : null;
    }

    /**
     * Get SSN serial (last 4 digits).
     */
    public String getSsnSerial() {
        String clean = getSsnClean();
        return clean != null ? clean.substring(5, 9) : null;
    }

    public String getSsnAtsReference() { return ssnAtsReference; }
    public void setSsnAtsReference(String ssnAtsReference) { this.ssnAtsReference = ssnAtsReference; }

    public LocalDate getDateOfBirth() { return dateOfBirth; }
    public void setDateOfBirth(LocalDate dateOfBirth) { this.dateOfBirth = dateOfBirth; }

    public String getOccupation() { return occupation; }
    public void setOccupation(String occupation) { this.occupation = occupation; }

    public ATSAddress getAddress() { return address; }
    public void setAddress(ATSAddress address) { this.address = address; }

    public boolean isBlind() { return isBlind; }
    public void setBlind(boolean blind) { isBlind = blind; }

    public boolean isOver65() { return isOver65; }
    public void setOver65(boolean over65) { isOver65 = over65; }

    public boolean isDeceased() { return isDeceased; }
    public void setDeceased(boolean deceased) { isDeceased = deceased; }

    public LocalDate getDateOfDeath() { return dateOfDeath; }
    public void setDateOfDeath(LocalDate dateOfDeath) { this.dateOfDeath = dateOfDeath; }

    public boolean isPrimaryFiler() { return isPrimaryFiler; }
    public void setPrimaryFiler(boolean primaryFiler) { isPrimaryFiler = primaryFiler; }

    public String getCountryOfResidence() { return countryOfResidence; }
    public void setCountryOfResidence(String countryOfResidence) { this.countryOfResidence = countryOfResidence; }

    public boolean isFullTimeStudent() { return isFullTimeStudent; }
    public void setFullTimeStudent(boolean fullTimeStudent) { isFullTimeStudent = fullTimeStudent; }

    public boolean isMilitary() { return isMilitary; }
    public void setMilitary(boolean military) { isMilitary = military; }

    public boolean isClergy() { return isClergy; }
    public void setClergy(boolean clergy) { isClergy = clergy; }

    public boolean isEducator() { return isEducator; }
    public void setEducator(boolean educator) { isEducator = educator; }

    public String getTreatyCountry() { return treatyCountry; }
    public void setTreatyCountry(String treatyCountry) { this.treatyCountry = treatyCountry; }

    public String getVisaType() { return visaType; }
    public void setVisaType(String visaType) { this.visaType = visaType; }

    public Integer getFirstYearInUS() { return firstYearInUS; }
    public void setFirstYearInUS(Integer firstYearInUS) { this.firstYearInUS = firstYearInUS; }

    public String getMilitaryBranch() { return militaryBranch; }
    public void setMilitaryBranch(String militaryBranch) { this.militaryBranch = militaryBranch; }

    public boolean isCombatZoneService() { return combatZoneService; }
    public void setCombatZoneService(boolean combatZoneService) { this.combatZoneService = combatZoneService; }

    public String getTaxTreatyCountry() { return taxTreatyCountry; }
    public void setTaxTreatyCountry(String taxTreatyCountry) { this.taxTreatyCountry = taxTreatyCountry; }

    public Integer getCombatZoneMonths() { return combatZoneMonths; }
    public void setCombatZoneMonths(Integer combatZoneMonths) { this.combatZoneMonths = combatZoneMonths; }

    public Map<String, Object> getForeignAddress() { return foreignAddress; }
    public void setForeignAddress(Map<String, Object> foreignAddress) { this.foreignAddress = foreignAddress; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ATSTaxpayer that = (ATSTaxpayer) o;
        return Objects.equals(ssn, that.ssn);
    }

    @Override
    public int hashCode() {
        return Objects.hash(ssn);
    }
}
