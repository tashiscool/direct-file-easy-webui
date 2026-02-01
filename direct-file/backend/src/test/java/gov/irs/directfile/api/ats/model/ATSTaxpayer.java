package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDate;
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
