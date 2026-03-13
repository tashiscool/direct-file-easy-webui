package gov.irs.directfile.api.ats.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

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

    // Additional income forms (stored as generic maps for flexibility)
    @JsonProperty("form1099Nec")
    private List<Map<String, Object>> form1099Nec = new ArrayList<>();

    @JsonProperty("form1099G")
    private Map<String, Object> form1099G;

    @JsonProperty("form1099Div")
    private List<Map<String, Object>> form1099Div = new ArrayList<>();

    @JsonProperty("form1099Int")
    private List<Map<String, Object>> form1099Int = new ArrayList<>();

    @JsonProperty("formW2G")
    private List<Map<String, Object>> formW2G = new ArrayList<>();

    @JsonProperty("scheduleK1")
    private List<Map<String, Object>> scheduleK1 = new ArrayList<>();

    @JsonProperty("formSSA1099")
    private List<Map<String, Object>> formSSA1099 = new ArrayList<>();

    @JsonProperty("form1099B")
    private List<Map<String, Object>> form1099B = new ArrayList<>();

    @JsonProperty("form1095A")
    private Map<String, Object> form1095A;

    @JsonProperty("form1098")
    private Map<String, Object> form1098;

    @JsonProperty("form1098T")
    private Map<String, Object> form1098T;

    @JsonProperty("form1116ForeignTaxCredit")
    private Map<String, Object> form1116ForeignTaxCredit;

    @JsonProperty("form1098E")
    private Map<String, Object> form1098E;

    @JsonProperty("form8962")
    private Map<String, Object> form8962;

    @JsonProperty("scheduleD")
    private Map<String, Object> scheduleD;

    // Schedule data
    @JsonProperty("scheduleA")
    private Map<String, Object> scheduleA;

    @JsonProperty("scheduleC")
    private Map<String, Object> scheduleC;

    @JsonProperty("scheduleE")
    private Map<String, Object> scheduleE;

    @JsonProperty("scheduleSE")
    private Map<String, Object> scheduleSE;

    // Credits and special forms
    @JsonProperty("form8936CleanVehicle")
    private Map<String, Object> form8936CleanVehicle;

    @JsonProperty("form5695ResidentialEnergy")
    private Map<String, Object> form5695ResidentialEnergy;

    @JsonProperty("form8889HSA")
    private Map<String, Object> form8889HSA;

    @JsonProperty("form8863Education")
    private Map<String, Object> form8863Education;

    @JsonProperty("form8962PTC")
    private Map<String, Object> form8962PTC;

    @JsonProperty("form2441ChildCare")
    private Map<String, Object> form2441ChildCare;

    @JsonProperty("form1116ForeignTax")
    private Map<String, Object> form1116ForeignTax;

    @JsonProperty("form8995QBI")
    private Map<String, Object> form8995QBI;

    @JsonProperty("form6251AMT")
    private Map<String, Object> form6251AMT;

    // Special scenarios
    @JsonProperty("isoExercise")
    private Map<String, Object> isoExercise;

    @JsonProperty("gamblingActivity")
    private Map<String, Object> gamblingActivity;

    @JsonProperty("digitalAssetTransactions")
    private List<Map<String, Object>> digitalAssetTransactions = new ArrayList<>();

    @JsonProperty("iraContributions")
    private Map<String, Object> iraContributions;

    @JsonProperty("hsaContributions")
    private Map<String, Object> hsaContributions;

    @JsonProperty("militaryIncome")
    private Map<String, Object> militaryIncome;

    @JsonProperty("militaryInfo")
    private Map<String, Object> militaryInfo;

    @JsonProperty("taxTreatyBenefits")
    private Map<String, Object> taxTreatyBenefits;

    @JsonProperty("movingExpenses")
    private Map<String, Object> movingExpenses;

    @JsonProperty("clergyIncome")
    private Map<String, Object> clergyIncome;

    @JsonProperty("clergyInfo")
    private Map<String, Object> clergyInfo;

    @JsonProperty("form4361Exemption")
    private boolean form4361Exemption;

    @JsonProperty("rentalProperties")
    private List<Map<String, Object>> rentalProperties = new ArrayList<>();

    @JsonProperty("stakingRewards")
    private Map<String, Object> stakingRewards;

    @JsonProperty("educatorExpenses")
    private Map<String, Object> educatorExpenses;

    @JsonProperty("estimatedTaxPayments")
    private List<Map<String, Object>> estimatedTaxPayments = new ArrayList<>();

    @JsonProperty("educationCredits")
    private Map<String, Object> educationCredits;

    @JsonProperty("healthInsurance")
    private Map<String, Object> healthInsurance;

    @JsonProperty("parsonageAllowance")
    private Map<String, Object> parsonageAllowance;

    @JsonProperty("childCareExpenses")
    private Map<String, Object> childCareExpenses;

    @JsonProperty("businessIncome")
    private Map<String, Object> businessIncome;

    @JsonProperty("form2441")
    private Map<String, Object> form2441;

    @JsonProperty("stakingIncome")
    private Map<String, Object> stakingIncome;

    @JsonProperty("scholarshipIncome")
    private Map<String, Object> scholarshipIncome;

    @JsonProperty("form1099Misc")
    private List<Map<String, Object>> form1099Misc = new ArrayList<>();

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

    @JsonProperty("hasForm5329")
    private boolean hasForm5329;

    @JsonProperty("hasForm6251")
    private boolean hasForm6251;

    @JsonProperty("hasForm1116")
    private boolean hasForm1116;

    @JsonProperty("hasForm8889")
    private boolean hasForm8889;

    @JsonProperty("hasForm8962")
    private boolean hasForm8962;

    @JsonProperty("hasForm8995")
    private boolean hasForm8995;

    @JsonProperty("hasScheduleOI")
    private boolean hasScheduleOI;

    @JsonProperty("hasForm3903")
    private boolean hasForm3903;

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

    public boolean isHasForm5329() { return hasForm5329; }
    public void setHasForm5329(boolean hasForm5329) { this.hasForm5329 = hasForm5329; }

    public boolean isHasForm6251() { return hasForm6251; }
    public void setHasForm6251(boolean hasForm6251) { this.hasForm6251 = hasForm6251; }

    public boolean isHasForm1116() { return hasForm1116; }
    public void setHasForm1116(boolean hasForm1116) { this.hasForm1116 = hasForm1116; }

    public boolean isHasForm8889() { return hasForm8889; }
    public void setHasForm8889(boolean hasForm8889) { this.hasForm8889 = hasForm8889; }

    public boolean isHasForm8962() { return hasForm8962; }
    public void setHasForm8962(boolean hasForm8962) { this.hasForm8962 = hasForm8962; }

    public boolean isHasForm8995() { return hasForm8995; }
    public void setHasForm8995(boolean hasForm8995) { this.hasForm8995 = hasForm8995; }

    public boolean isHasScheduleOI() { return hasScheduleOI; }
    public void setHasScheduleOI(boolean hasScheduleOI) { this.hasScheduleOI = hasScheduleOI; }

    public boolean isHasForm3903() { return hasForm3903; }
    public void setHasForm3903(boolean hasForm3903) { this.hasForm3903 = hasForm3903; }

    // Additional income forms getters/setters
    public List<Map<String, Object>> getForm1099Nec() { return form1099Nec; }
    public void setForm1099Nec(List<Map<String, Object>> form1099Nec) { this.form1099Nec = form1099Nec; }

    public Map<String, Object> getForm1099G() { return form1099G; }
    public void setForm1099G(Map<String, Object> form1099G) { this.form1099G = form1099G; }

    public List<Map<String, Object>> getForm1099Div() { return form1099Div; }
    public void setForm1099Div(List<Map<String, Object>> form1099Div) { this.form1099Div = form1099Div; }

    public List<Map<String, Object>> getForm1099Int() { return form1099Int; }
    public void setForm1099Int(List<Map<String, Object>> form1099Int) { this.form1099Int = form1099Int; }

    public List<Map<String, Object>> getForm1099Misc() { return form1099Misc; }
    public void setForm1099Misc(List<Map<String, Object>> form1099Misc) { this.form1099Misc = form1099Misc; }

    public List<Map<String, Object>> getFormW2G() { return formW2G; }
    public void setFormW2G(List<Map<String, Object>> formW2G) { this.formW2G = formW2G; }

    public List<Map<String, Object>> getScheduleK1() { return scheduleK1; }
    public void setScheduleK1(List<Map<String, Object>> scheduleK1) { this.scheduleK1 = scheduleK1; }

    public List<Map<String, Object>> getFormSSA1099() { return formSSA1099; }
    public void setFormSSA1099(List<Map<String, Object>> formSSA1099) { this.formSSA1099 = formSSA1099; }

    // Schedule data getters/setters
    public Map<String, Object> getScheduleA() { return scheduleA; }
    public void setScheduleA(Map<String, Object> scheduleA) { this.scheduleA = scheduleA; }

    public Map<String, Object> getScheduleC() { return scheduleC; }
    public void setScheduleC(Map<String, Object> scheduleC) { this.scheduleC = scheduleC; }

    public Map<String, Object> getScheduleE() { return scheduleE; }
    public void setScheduleE(Map<String, Object> scheduleE) { this.scheduleE = scheduleE; }

    public Map<String, Object> getScheduleSE() { return scheduleSE; }
    public void setScheduleSE(Map<String, Object> scheduleSE) { this.scheduleSE = scheduleSE; }

    // Credit form getters/setters
    public Map<String, Object> getForm8936CleanVehicle() { return form8936CleanVehicle; }
    public void setForm8936CleanVehicle(Map<String, Object> form8936CleanVehicle) { this.form8936CleanVehicle = form8936CleanVehicle; }

    public Map<String, Object> getForm5695ResidentialEnergy() { return form5695ResidentialEnergy; }
    public void setForm5695ResidentialEnergy(Map<String, Object> form5695ResidentialEnergy) { this.form5695ResidentialEnergy = form5695ResidentialEnergy; }

    public Map<String, Object> getForm8889HSA() { return form8889HSA; }
    public void setForm8889HSA(Map<String, Object> form8889HSA) { this.form8889HSA = form8889HSA; }

    public Map<String, Object> getForm8863Education() { return form8863Education; }
    public void setForm8863Education(Map<String, Object> form8863Education) { this.form8863Education = form8863Education; }

    public Map<String, Object> getForm8962PTC() { return form8962PTC; }
    public void setForm8962PTC(Map<String, Object> form8962PTC) { this.form8962PTC = form8962PTC; }

    public Map<String, Object> getForm2441ChildCare() { return form2441ChildCare; }
    public void setForm2441ChildCare(Map<String, Object> form2441ChildCare) { this.form2441ChildCare = form2441ChildCare; }

    public Map<String, Object> getForm1116ForeignTax() { return form1116ForeignTax; }
    public void setForm1116ForeignTax(Map<String, Object> form1116ForeignTax) { this.form1116ForeignTax = form1116ForeignTax; }

    public Map<String, Object> getForm8995QBI() { return form8995QBI; }
    public void setForm8995QBI(Map<String, Object> form8995QBI) { this.form8995QBI = form8995QBI; }

    public Map<String, Object> getForm6251AMT() { return form6251AMT; }
    public void setForm6251AMT(Map<String, Object> form6251AMT) { this.form6251AMT = form6251AMT; }

    // Special scenario getters/setters
    public Map<String, Object> getIsoExercise() { return isoExercise; }
    public void setIsoExercise(Map<String, Object> isoExercise) { this.isoExercise = isoExercise; }

    public Map<String, Object> getGamblingActivity() { return gamblingActivity; }
    public void setGamblingActivity(Map<String, Object> gamblingActivity) { this.gamblingActivity = gamblingActivity; }

    public List<Map<String, Object>> getDigitalAssetTransactions() { return digitalAssetTransactions; }
    public void setDigitalAssetTransactions(List<Map<String, Object>> digitalAssetTransactions) { this.digitalAssetTransactions = digitalAssetTransactions; }

    public Map<String, Object> getIraContributions() { return iraContributions; }
    public void setIraContributions(Map<String, Object> iraContributions) { this.iraContributions = iraContributions; }

    public Map<String, Object> getHsaContributions() { return hsaContributions; }
    public void setHsaContributions(Map<String, Object> hsaContributions) { this.hsaContributions = hsaContributions; }

    public Map<String, Object> getMilitaryIncome() { return militaryIncome; }
    public void setMilitaryIncome(Map<String, Object> militaryIncome) { this.militaryIncome = militaryIncome; }

    public Map<String, Object> getMilitaryInfo() { return militaryInfo; }
    public void setMilitaryInfo(Map<String, Object> militaryInfo) { this.militaryInfo = militaryInfo; }

    public Map<String, Object> getTaxTreatyBenefits() { return taxTreatyBenefits; }
    public void setTaxTreatyBenefits(Map<String, Object> taxTreatyBenefits) { this.taxTreatyBenefits = taxTreatyBenefits; }

    public Map<String, Object> getMovingExpenses() { return movingExpenses; }
    public void setMovingExpenses(Map<String, Object> movingExpenses) { this.movingExpenses = movingExpenses; }

    public Map<String, Object> getClergyIncome() { return clergyIncome; }
    public void setClergyIncome(Map<String, Object> clergyIncome) { this.clergyIncome = clergyIncome; }

    public Map<String, Object> getClergyInfo() { return clergyInfo; }
    public void setClergyInfo(Map<String, Object> clergyInfo) { this.clergyInfo = clergyInfo; }

    public boolean isForm4361Exemption() { return form4361Exemption; }
    public void setForm4361Exemption(boolean form4361Exemption) { this.form4361Exemption = form4361Exemption; }

    public List<Map<String, Object>> getRentalProperties() { return rentalProperties; }
    public void setRentalProperties(List<Map<String, Object>> rentalProperties) { this.rentalProperties = rentalProperties; }

    public List<Map<String, Object>> getEstimatedTaxPayments() { return estimatedTaxPayments; }
    public void setEstimatedTaxPayments(List<Map<String, Object>> estimatedTaxPayments) { this.estimatedTaxPayments = estimatedTaxPayments; }

    public Map<String, Object> getScholarshipIncome() { return scholarshipIncome; }
    public void setScholarshipIncome(Map<String, Object> scholarshipIncome) { this.scholarshipIncome = scholarshipIncome; }

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
