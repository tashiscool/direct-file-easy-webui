package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;

/**
 * Complete ATS (Assurance Testing System) scenario data.
 *
 * This is the root object containing all tax return data for an IRS ATS test scenario.
 * Each scenario represents a complete tax return that must be validated for MeF compliance.
 *
 * Scenarios are extracted from IRS ATS PDF documents and converted to this structured format
 * for integration testing.
 */
public class ATSScenarioData {
    // Scenario metadata
    @JsonProperty("scenarioId")
    private String scenarioId;

    @JsonProperty("scenarioName")
    private String scenarioName;

    @JsonProperty("description")
    private String description;

    @JsonProperty("pdfReference")
    private String pdfReference;

    @JsonProperty("taxYear")
    private int taxYear = 2025;

    // Filing information
    @JsonProperty("filingStatus")
    private int filingStatus; // 1=Single, 2=MFJ, 3=MFS, 4=HOH, 5=QSS

    @JsonProperty("filingStatusDescription")
    private String filingStatusDescription;

    @JsonProperty("formType")
    private String formType = "1040"; // 1040, 1040-SR, 1040-NR, 1040-SS

    // Taxpayer information
    @JsonProperty("primaryTaxpayer")
    private ATSTaxpayer primaryTaxpayer;

    @JsonProperty("spouse")
    private ATSTaxpayer spouse;

    @JsonProperty("dependents")
    private List<ATSDependent> dependents = new ArrayList<>();

    // Income documents
    @JsonProperty("w2Forms")
    private List<ATSW2Data> w2Forms = new ArrayList<>();

    @JsonProperty("form1099Rs")
    private List<ATS1099RData> form1099Rs = new ArrayList<>();

    // Checkboxes
    @JsonProperty("presidentialCampaign")
    private boolean presidentialCampaign;

    @JsonProperty("spousePresidentialCampaign")
    private boolean spousePresidentialCampaign;

    @JsonProperty("digitalAssets")
    private boolean digitalAssets;

    // Attached schedules/forms flags
    @JsonProperty("hasSchedule1")
    private boolean hasSchedule1;

    @JsonProperty("hasSchedule2")
    private boolean hasSchedule2;

    @JsonProperty("hasSchedule3")
    private boolean hasSchedule3;

    @JsonProperty("hasScheduleA")
    private boolean hasScheduleA;

    @JsonProperty("hasScheduleB")
    private boolean hasScheduleB;

    @JsonProperty("hasScheduleC")
    private boolean hasScheduleC;

    @JsonProperty("hasScheduleD")
    private boolean hasScheduleD;

    @JsonProperty("hasScheduleE")
    private boolean hasScheduleE;

    @JsonProperty("hasScheduleF")
    private boolean hasScheduleF;

    @JsonProperty("hasScheduleH")
    private boolean hasScheduleH;

    @JsonProperty("hasScheduleSE")
    private boolean hasScheduleSE;

    @JsonProperty("hasForm2441")
    private boolean hasForm2441;

    @JsonProperty("hasForm5695")
    private boolean hasForm5695;

    @JsonProperty("hasForm8283")
    private boolean hasForm8283;

    @JsonProperty("hasForm8812")
    private boolean hasForm8812;

    @JsonProperty("hasForm8862")
    private boolean hasForm8862;

    @JsonProperty("hasForm8863")
    private boolean hasForm8863;

    @JsonProperty("hasForm8949")
    private boolean hasForm8949;

    @JsonProperty("hasForm3800")
    private boolean hasForm3800;

    @JsonProperty("hasForm8835")
    private boolean hasForm8835;

    @JsonProperty("hasForm8936")
    private boolean hasForm8936;

    // Expected calculation results for validation
    @JsonProperty("expectedValues")
    private ATSExpectedValues expectedValues = new ATSExpectedValues();

    public ATSScenarioData() {}

    // Getters and Setters
    public String getScenarioId() { return scenarioId; }
    public void setScenarioId(String scenarioId) { this.scenarioId = scenarioId; }

    public String getScenarioName() { return scenarioName; }
    public void setScenarioName(String scenarioName) { this.scenarioName = scenarioName; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getPdfReference() { return pdfReference; }
    public void setPdfReference(String pdfReference) { this.pdfReference = pdfReference; }

    public int getTaxYear() { return taxYear; }
    public void setTaxYear(int taxYear) { this.taxYear = taxYear; }

    public int getFilingStatus() { return filingStatus; }
    public void setFilingStatus(int filingStatus) { this.filingStatus = filingStatus; }

    public String getFilingStatusDescription() { return filingStatusDescription; }
    public void setFilingStatusDescription(String filingStatusDescription) { this.filingStatusDescription = filingStatusDescription; }

    public String getFormType() { return formType; }
    public void setFormType(String formType) { this.formType = formType; }

    public ATSTaxpayer getPrimaryTaxpayer() { return primaryTaxpayer; }
    public void setPrimaryTaxpayer(ATSTaxpayer primaryTaxpayer) { this.primaryTaxpayer = primaryTaxpayer; }

    public ATSTaxpayer getSpouse() { return spouse; }
    public void setSpouse(ATSTaxpayer spouse) { this.spouse = spouse; }

    public List<ATSDependent> getDependents() { return dependents; }
    public void setDependents(List<ATSDependent> dependents) { this.dependents = dependents; }

    public List<ATSW2Data> getW2Forms() { return w2Forms; }
    public void setW2Forms(List<ATSW2Data> w2Forms) { this.w2Forms = w2Forms; }

    public List<ATS1099RData> getForm1099Rs() { return form1099Rs; }
    public void setForm1099Rs(List<ATS1099RData> form1099Rs) { this.form1099Rs = form1099Rs; }

    public boolean isPresidentialCampaign() { return presidentialCampaign; }
    public void setPresidentialCampaign(boolean presidentialCampaign) { this.presidentialCampaign = presidentialCampaign; }

    public boolean isSpousePresidentialCampaign() { return spousePresidentialCampaign; }
    public void setSpousePresidentialCampaign(boolean spousePresidentialCampaign) { this.spousePresidentialCampaign = spousePresidentialCampaign; }

    public boolean isDigitalAssets() { return digitalAssets; }
    public void setDigitalAssets(boolean digitalAssets) { this.digitalAssets = digitalAssets; }

    public boolean isHasSchedule1() { return hasSchedule1; }
    public void setHasSchedule1(boolean hasSchedule1) { this.hasSchedule1 = hasSchedule1; }

    public boolean isHasSchedule2() { return hasSchedule2; }
    public void setHasSchedule2(boolean hasSchedule2) { this.hasSchedule2 = hasSchedule2; }

    public boolean isHasSchedule3() { return hasSchedule3; }
    public void setHasSchedule3(boolean hasSchedule3) { this.hasSchedule3 = hasSchedule3; }

    public boolean isHasScheduleA() { return hasScheduleA; }
    public void setHasScheduleA(boolean hasScheduleA) { this.hasScheduleA = hasScheduleA; }

    public boolean isHasScheduleB() { return hasScheduleB; }
    public void setHasScheduleB(boolean hasScheduleB) { this.hasScheduleB = hasScheduleB; }

    public boolean isHasScheduleC() { return hasScheduleC; }
    public void setHasScheduleC(boolean hasScheduleC) { this.hasScheduleC = hasScheduleC; }

    public boolean isHasScheduleD() { return hasScheduleD; }
    public void setHasScheduleD(boolean hasScheduleD) { this.hasScheduleD = hasScheduleD; }

    public boolean isHasScheduleE() { return hasScheduleE; }
    public void setHasScheduleE(boolean hasScheduleE) { this.hasScheduleE = hasScheduleE; }

    public boolean isHasScheduleF() { return hasScheduleF; }
    public void setHasScheduleF(boolean hasScheduleF) { this.hasScheduleF = hasScheduleF; }

    public boolean isHasScheduleH() { return hasScheduleH; }
    public void setHasScheduleH(boolean hasScheduleH) { this.hasScheduleH = hasScheduleH; }

    public boolean isHasScheduleSE() { return hasScheduleSE; }
    public void setHasScheduleSE(boolean hasScheduleSE) { this.hasScheduleSE = hasScheduleSE; }

    public boolean isHasForm2441() { return hasForm2441; }
    public void setHasForm2441(boolean hasForm2441) { this.hasForm2441 = hasForm2441; }

    public boolean isHasForm5695() { return hasForm5695; }
    public void setHasForm5695(boolean hasForm5695) { this.hasForm5695 = hasForm5695; }

    public boolean isHasForm8283() { return hasForm8283; }
    public void setHasForm8283(boolean hasForm8283) { this.hasForm8283 = hasForm8283; }

    public boolean isHasForm8812() { return hasForm8812; }
    public void setHasForm8812(boolean hasForm8812) { this.hasForm8812 = hasForm8812; }

    public boolean isHasForm8862() { return hasForm8862; }
    public void setHasForm8862(boolean hasForm8862) { this.hasForm8862 = hasForm8862; }

    public boolean isHasForm8863() { return hasForm8863; }
    public void setHasForm8863(boolean hasForm8863) { this.hasForm8863 = hasForm8863; }

    public boolean isHasForm8949() { return hasForm8949; }
    public void setHasForm8949(boolean hasForm8949) { this.hasForm8949 = hasForm8949; }

    public boolean isHasForm3800() { return hasForm3800; }
    public void setHasForm3800(boolean hasForm3800) { this.hasForm3800 = hasForm3800; }

    public boolean isHasForm8835() { return hasForm8835; }
    public void setHasForm8835(boolean hasForm8835) { this.hasForm8835 = hasForm8835; }

    public boolean isHasForm8936() { return hasForm8936; }
    public void setHasForm8936(boolean hasForm8936) { this.hasForm8936 = hasForm8936; }

    public ATSExpectedValues getExpectedValues() { return expectedValues; }
    public void setExpectedValues(ATSExpectedValues expectedValues) { this.expectedValues = expectedValues; }

    /**
     * Check if this is a joint filing (MFJ or QSS with spouse info).
     */
    public boolean isJointFiling() {
        return filingStatus == 2 && spouse != null;
    }

    /**
     * Get total W-2 wages from all W-2 forms.
     */
    public java.math.BigDecimal getTotalW2Wages() {
        return w2Forms.stream()
            .map(ATSW2Data::getWages)
            .reduce(java.math.BigDecimal.ZERO, java.math.BigDecimal::add);
    }

    /**
     * Get total federal withholding from all W-2 forms.
     */
    public java.math.BigDecimal getTotalW2Withholding() {
        return w2Forms.stream()
            .map(ATSW2Data::getFederalWithholding)
            .reduce(java.math.BigDecimal.ZERO, java.math.BigDecimal::add);
    }

    /**
     * Get total 1099-R gross distribution.
     */
    public java.math.BigDecimal getTotal1099RGross() {
        return form1099Rs.stream()
            .map(ATS1099RData::getGrossDistribution)
            .reduce(java.math.BigDecimal.ZERO, java.math.BigDecimal::add);
    }

    /**
     * Get count of qualifying children under 17.
     */
    public long getQualifyingChildrenUnder17Count() {
        return dependents.stream()
            .filter(ATSDependent::isQualifyingChildUnder17)
            .count();
    }

    @Override
    public String toString() {
        return String.format("ATSScenarioData[id=%s, name=%s, filingStatus=%d, taxpayer=%s %s]",
            scenarioId,
            scenarioName,
            filingStatus,
            primaryTaxpayer != null ? primaryTaxpayer.getFirstName() : "N/A",
            primaryTaxpayer != null ? primaryTaxpayer.getLastName() : "");
    }
}
