package gov.irs.directfile.api.ats;

import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import gov.irs.directfile.api.ats.converter.ATSToFactGraphConverter;
import gov.irs.directfile.api.ats.model.ATSScenarioData;
import gov.irs.directfile.api.loaders.service.FactGraphService;
import gov.irs.directfile.api.util.base.BaseIntegrationTest;
import gov.irs.directfile.models.FactTypeWithItem;
import gov.irs.factgraph.Graph;
import gov.irs.factgraph.monads.Result;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
public class TaxYear2025RegressionTest extends BaseIntegrationTest {

    private static final String BOOLEAN_WRAPPER = "gov.irs.factgraph.persisters.BooleanWrapper";
    private static final String INT_WRAPPER = "gov.irs.factgraph.persisters.IntWrapper";
    private static final String DOLLAR_WRAPPER = "gov.irs.factgraph.persisters.DollarWrapper";
    private static final String ENUM_WRAPPER = "gov.irs.factgraph.persisters.EnumWrapper";

    @Autowired
    private FactGraphService factGraphService;

    private ATSToFactGraphConverter converter;
    private JsonNodeFactory nodeFactory;

    @BeforeEach
    void setUp() {
        converter = new ATSToFactGraphConverter();
        nodeFactory = JsonNodeFactory.instance;
    }

    @DynamicPropertySource
    static void registerDataSourceProperties(DynamicPropertyRegistry registry) {
        String dbUrl = buildTestDbUrl("taxyear-2025");
        registry.add("spring.datasource.url", () -> dbUrl);
        registry.add("spring.liquibase.url", () -> dbUrl);
        registry.add("spring.datasource.username", () -> "sa");
        registry.add("spring.datasource.password", () -> "");
        registry.add("spring.liquibase.user", () -> "sa");
        registry.add("spring.liquibase.password", () -> "");
    }

    @Test
    @DisplayName("QBI thresholds use the published 2025 amounts and MFJ threshold selection")
    void testQbiThresholdsUsePublished2025Amounts() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-13-birch.json");
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdSingle"))
            .isEqualByComparingTo(new BigDecimal("197300.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdMFJ"))
            .isEqualByComparingTo(new BigDecimal("394600.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdSingle8995A"))
            .isEqualByComparingTo(new BigDecimal("197300.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdMFJ8995A"))
            .isEqualByComparingTo(new BigDecimal("394600.00"));
        assertThat(getFactAsBoolean(graph, "/canUseSimplifiedMethod")).isTrue();
    }

    @Test
    @DisplayName("Schedule 1-A applies stepped overtime and tip phase-outs")
    void testSchedule1ASteppedOvertimeAndTipPhaseouts() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-13-birch.json");
        facts.put("/hasQualifiedOvertime", booleanWrapper(true));
        facts.put("/qualifiedOvertimeIncome", dollarWrapper("25000"));
        facts.put("/hasQualifiedTips", booleanWrapper(true));
        facts.put("/qualifiedTipIncome", dollarWrapper("25000"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/overtimeDeductionAmount"))
            .isEqualByComparingTo(new BigDecimal("24000.00"));
        assertThat(getFactAsBigDecimal(graph, "/tipDeductionAmount"))
            .isEqualByComparingTo(new BigDecimal("24000.00"));
    }

    @Test
    @DisplayName("Schedule 1-A increases deductions without reducing AGI")
    void testSchedule1AFlowsToDeductionsInsteadOfAgi() throws IOException {
        Map<String, FactTypeWithItem> baseFacts = scenarioFacts("scenario-13-birch.json");
        Graph baseGraph = factGraphService.getGraph(baseFacts);

        Map<String, FactTypeWithItem> factsWithSchedule1A = new HashMap<>(baseFacts);
        factsWithSchedule1A.put("/hasQualifiedOvertime", booleanWrapper(true));
        factsWithSchedule1A.put("/qualifiedOvertimeIncome", dollarWrapper("25000"));
        factsWithSchedule1A.put("/hasQualifiedTips", booleanWrapper(true));
        factsWithSchedule1A.put("/qualifiedTipIncome", dollarWrapper("25000"));

        Graph schedule1AGraph = factGraphService.getGraph(factsWithSchedule1A);

        BigDecimal baseAgi = getFactAsBigDecimal(baseGraph, "/agi");
        BigDecimal schedule1AAgi = getFactAsBigDecimal(schedule1AGraph, "/agi");
        BigDecimal schedule1ATotal = getFactAsBigDecimal(schedule1AGraph, "/totalSchedule1ADeductions");
        BigDecimal baseTotalDeductions = getFactAsBigDecimal(baseGraph, "/totalDeductions");
        BigDecimal schedule1ATotalDeductions = getFactAsBigDecimal(schedule1AGraph, "/totalDeductions");

        assertThat(schedule1ATotal).isEqualByComparingTo(new BigDecimal("48000.00"));
        assertThat(schedule1AAgi).isEqualByComparingTo(baseAgi);
        assertThat(schedule1ATotalDeductions)
            .isEqualByComparingTo(baseTotalDeductions.add(schedule1ATotal));
    }

    @Test
    @DisplayName("Schedule 1-A disallows MFS wage deductions and senior bonus")
    void testSchedule1AMfsRestrictions() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-8-lewis.json");
        facts.put("/hasQualifiedOvertime", booleanWrapper(true));
        facts.put("/qualifiedOvertimeIncome", dollarWrapper("12500"));
        facts.put("/hasQualifiedTips", booleanWrapper(true));
        facts.put("/qualifiedTipIncome", dollarWrapper("25000"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/overtimeDeductionAmount"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        assertThat(getFactAsBigDecimal(graph, "/tipDeductionAmount"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        assertThat(getFactAsBigDecimal(graph, "/totalSeniorBonusDeduction"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
    }

    @Test
    @DisplayName("Schedule 1-A auto loan phase-out rounds up each thousand dollars of excess income")
    void testSchedule1AAutoLoanRoundUpPhaseout() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-1-tara-black.json");
        distributeTotalWagesAcrossW2s(facts, new BigDecimal("100001"));
        facts.put("/hasQualifiedAutoLoanInterest", booleanWrapper(true));
        facts.put("/vehicleIsDomesticManufacture", booleanWrapper(true));
        facts.put("/qualifiedAutoLoanInterest", dollarWrapper("1000"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/autoLoanInterestDeductionAmount"))
            .isEqualByComparingTo(new BigDecimal("800.00"));
    }

    @Test
    @DisplayName("QBI deduction rolls into total deductions and final taxable income")
    void testQbiDeductionFeedsTotalDeductions() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-28-taylor-qbi.json");
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/totalQBI"))
            .isEqualByComparingTo(new BigDecimal("113000.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiDeduction"))
            .isEqualByComparingTo(new BigDecimal("17854.00"));
        assertThat(getFactAsBigDecimal(graph, "/totalDeductions"))
            .isEqualByComparingTo(new BigDecimal("33604.00"));
        assertThat(getFactAsBigDecimal(graph, "/taxableIncome"))
            .isEqualByComparingTo(new BigDecimal("71415.00"));
    }

    @Test
    @DisplayName("Detailed Form 8995-A aggregates multi-business QBI, wages, and UBIA inputs")
    void testForm8995AAggregatesDetailedBusinessInputs() throws IOException {
        ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-18-thompson-rental.json");
        Map<String, Object> form8995Qbi = new HashMap<>();
        form8995Qbi.put("businesses", List.of(
            qbiBusiness("Alpha Advisory", "210000", "60000", "100000", false),
            qbiBusiness("Beta Logistics", "90000", "20000", "50000", false)
        ));
        scenario.setForm8995QBI(form8995Qbi);

        Map<String, FactTypeWithItem> facts = new HashMap<>(converter.convert(scenario));
        facts.remove("/qbi8995A");
        facts.remove("/w2Wages8995A");
        facts.remove("/ubia8995A");
        facts.remove("/form8995AOverflowBusinesses");
        facts.remove("/hasForm8995AAttachmentStatement");
        distributeTotalWagesAcrossW2s(facts, new BigDecimal("300000"));
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/directQBI"))
            .isEqualByComparingTo(new BigDecimal("300000.00"));
        assertThat(getFactAsBigDecimal(graph, "/w2WagesPaid"))
            .isEqualByComparingTo(new BigDecimal("80000.00"));
        assertThat(getFactAsBigDecimal(graph, "/qualifiedPropertyBasis"))
            .isEqualByComparingTo(new BigDecimal("150000.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbi8995A"))
            .isEqualByComparingTo(new BigDecimal("300000.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiComponentAfter8995A"))
            .isEqualByComparingTo(new BigDecimal("40000.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiDeduction"))
            .isEqualByComparingTo(new BigDecimal("40000.00"));
        assertThat(getFactAsBigDecimal(graph, "/w2Wages8995A"))
            .isEqualByComparingTo(new BigDecimal("80000.00"));
        assertThat(getFactAsBigDecimal(graph, "/ubia8995A"))
            .isEqualByComparingTo(new BigDecimal("150000.00"));
    }

    @Test
    @DisplayName("Form 8995-A tracks overflow businesses for attachment-style parity")
    void testForm8995AOverflowStatementFacts() throws IOException {
        ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-18-thompson-rental.json");
        Map<String, Object> form8995Qbi = new HashMap<>();
        form8995Qbi.put("businesses", List.of(
            qbiBusiness("Alpha Advisory", "210000", "60000", "100000", false),
            qbiBusiness("Beta Logistics", "90000", "20000", "50000", false),
            qbiBusiness("Gamma Studio", "50000", "10000", "20000", true),
            qbiBusiness("Delta Rentals", "40000", "5000", "15000", false),
            qbiBusiness("Echo Foods", "30000", "3000", "10000", false)
        ));
        scenario.setForm8995QBI(form8995Qbi);

        Map<String, FactTypeWithItem> facts = new HashMap<>(converter.convert(scenario));
        facts.remove("/qbi8995A");
        facts.remove("/w2Wages8995A");
        facts.remove("/ubia8995A");
        facts.remove("/form8995AOverflowBusinesses");
        facts.remove("/hasForm8995AAttachmentStatement");

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsInt(graph, "/form8995ATotalBusinesses")).isEqualTo(5);
        assertThat(getFactAsInt(graph, "/form8995AOverflowBusinesses")).isEqualTo(2);
        assertThat(getFactAsBoolean(graph, "/hasForm8995AAttachmentStatement")).isTrue();
        assertThat(getFactAsBigDecimal(graph, "/form8995AOverflowQBI"))
            .isEqualByComparingTo(new BigDecimal("70000.00"));
        assertThat(getFactAsBigDecimal(graph, "/form8995AOverflowW2Wages"))
            .isEqualByComparingTo(new BigDecimal("8000.00"));
        assertThat(getFactAsBigDecimal(graph, "/form8995AOverflowUBIA"))
            .isEqualByComparingTo(new BigDecimal("25000.00"));
        assertThat(getFactAsString(graph, "/form8995ABusiness4Name")).isEqualTo("Delta Rentals");
        assertThat(getFactAsString(graph, "/form8995ABusiness5Name")).isEqualTo("Echo Foods");
        assertThat(getFactAsBigDecimal(graph, "/form8995ABusiness4QBI"))
            .isEqualByComparingTo(new BigDecimal("40000.00"));
        assertThat(getFactAsBigDecimal(graph, "/form8995ABusiness5QBI"))
            .isEqualByComparingTo(new BigDecimal("30000.00"));
        assertThat(getFactAsBigDecimal(graph, "/form8995ABusiness4W2Wages"))
            .isEqualByComparingTo(new BigDecimal("5000.00"));
        assertThat(getFactAsBigDecimal(graph, "/form8995ABusiness5W2Wages"))
            .isEqualByComparingTo(new BigDecimal("3000.00"));
        assertThat(getFactAsBigDecimal(graph, "/form8995ABusiness4UBIA"))
            .isEqualByComparingTo(new BigDecimal("15000.00"));
        assertThat(getFactAsBigDecimal(graph, "/form8995ABusiness5UBIA"))
            .isEqualByComparingTo(new BigDecimal("10000.00"));
        assertThat(getFactAsBoolean(graph, "/form8995ABusiness3IsSSTB")).isTrue();
        assertThat(getFactAsBoolean(graph, "/form8995ABusiness4IsSSTB")).isFalse();
        assertThat(getFactAsBoolean(graph, "/form8995ABusiness5IsSSTB")).isFalse();
        assertThat(getFactAsBigDecimal(graph, "/qbi8995A"))
            .isEqualByComparingTo(new BigDecimal("420000.00"));
        assertThat(getFactAsBigDecimal(graph, "/w2Wages8995A"))
            .isEqualByComparingTo(new BigDecimal("98000.00"));
        assertThat(getFactAsBigDecimal(graph, "/ubia8995A"))
            .isEqualByComparingTo(new BigDecimal("195000.00"));
    }

    @Test
    @DisplayName("Form 6251 applies the MFJ AMT exemption and phaseout thresholds")
    void testForm6251UsesMfJThresholds() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-33-wright-amt.json");
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/amtExemption6251"))
            .isEqualByComparingTo(new BigDecimal("137000.00"));
        assertThat(getFactAsBigDecimal(graph, "/amtPhaseoutStart6251"))
            .isEqualByComparingTo(new BigDecimal("1252700.00"));
        assertThat(getFactAsBigDecimal(graph, "/amtRate26Threshold2025"))
            .isEqualByComparingTo(new BigDecimal("239100.00"));
        assertThat(getFactAsBigDecimal(graph, "/excessAMTI"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        assertThat(getFactAsBigDecimal(graph, "/reducedAMTExemption"))
            .isEqualByComparingTo(new BigDecimal("137000.00"));
        assertThat(getFactAsBigDecimal(graph, "/amtiLessExemption"))
            .isEqualByComparingTo(new BigDecimal("799750.00"));
    }

    @Test
    @DisplayName("Schedule 8812 selects the MFJ threshold and rounds phaseout excess up")
    void testForm8812AppliesMfJThresholdAndRounding() {
        Map<String, FactTypeWithItem> facts = new HashMap<>();
        facts.put("/filingStatus", filingStatusWrapper("marriedFilingJointly"));
        facts.put("/hasChildOrDependentCredits", booleanWrapper(true));
        facts.put("/numberOfQualifyingChildren", intWrapper(2));
        facts.put("/numberOfOtherDependents", intWrapper(1));
        facts.put("/modifiedAGI8812", dollarWrapper("400999"));
        facts.put("/earnedIncomeForACTC", dollarWrapper("0"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/applicablePhaseoutThreshold"))
            .isEqualByComparingTo(new BigDecimal("400000.00"));
        assertThat(getFactAsBigDecimal(graph, "/phaseoutExcess8812"))
            .isEqualByComparingTo(new BigDecimal("999.00"));
        assertThat(getFactAsBigDecimal(graph, "/phaseoutReduction8812"))
            .isEqualByComparingTo(new BigDecimal("50.00"));
        assertThat(getFactAsBigDecimal(graph, "/ctcAfterPhaseout"))
            .isEqualByComparingTo(new BigDecimal("4850.00"));
    }

    @Test
    @DisplayName("Form 8949 derives transaction presence and wash sale indicators")
    void testForm8949DerivesTransactionPresenceAndWashSales() {
        Map<String, FactTypeWithItem> facts = new HashMap<>();
        facts.put("/shortTermBoxA", booleanWrapper(true));
        facts.put("/shortTermProceedsBoxA", dollarWrapper("1000"));
        facts.put("/shortTermCostBoxA", dollarWrapper("700"));
        facts.put("/shortTermAdjustmentsBoxA", dollarWrapper("0"));
        facts.put("/shortTermBoxB", booleanWrapper(false));
        facts.put("/shortTermProceedsBoxB", dollarWrapper("0"));
        facts.put("/shortTermCostBoxB", dollarWrapper("0"));
        facts.put("/shortTermBoxC", booleanWrapper(false));
        facts.put("/shortTermProceedsBoxC", dollarWrapper("0"));
        facts.put("/shortTermCostBoxC", dollarWrapper("0"));
        facts.put("/longTermBoxE", booleanWrapper(true));
        facts.put("/longTermProceedsBoxE", dollarWrapper("2000"));
        facts.put("/longTermCostBoxE", dollarWrapper("2300"));
        facts.put("/longTermBoxD", booleanWrapper(false));
        facts.put("/longTermProceedsBoxD", dollarWrapper("0"));
        facts.put("/longTermCostBoxD", dollarWrapper("0"));
        facts.put("/longTermAdjustmentsBoxD", dollarWrapper("0"));
        facts.put("/longTermBoxF", booleanWrapper(false));
        facts.put("/longTermProceedsBoxF", dollarWrapper("0"));
        facts.put("/longTermCostBoxF", dollarWrapper("0"));
        facts.put("/washSaleDisallowedLoss", dollarWrapper("125"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBoolean(graph, "/hasShortTermTransactions")).isTrue();
        assertThat(getFactAsBoolean(graph, "/hasLongTermTransactions")).isTrue();
        assertThat(getFactAsBoolean(graph, "/hasWashSales")).isTrue();
        assertThat(getFactAsBigDecimal(graph, "/shortTermGainLossBoxA"))
            .isEqualByComparingTo(new BigDecimal("300.00"));
        assertThat(getFactAsBigDecimal(graph, "/longTermGainLossBoxE"))
            .isEqualByComparingTo(new BigDecimal("-300.00"));
        assertThat(getFactAsBigDecimal(graph, "/totalShortTermGainLoss"))
            .isEqualByComparingTo(new BigDecimal("300.00"));
        assertThat(getFactAsBigDecimal(graph, "/totalLongTermGainLoss"))
            .isEqualByComparingTo(new BigDecimal("-300.00"));
        assertThat(getFactAsBoolean(graph, "/pdfIncludeForm8949")).isTrue();
        assertThat(getFactAsBoolean(graph, "/form8949IsDone")).isTrue();
    }

    @Test
    @DisplayName("Form 8995 supplementary QBI inputs normalize for 2025")
    void testQbiCarryoverAndReitPtpComponents() {
        Map<String, FactTypeWithItem> facts = new HashMap<>();
        facts.put("/priorYearQBICarryover", dollarWrapper("-2500"));
        facts.put("/reitDividends", dollarWrapper("1500"));
        facts.put("/ptpIncome", dollarWrapper("3000"));

        assertThat(facts.get("/priorYearQBICarryover").item().asText()).isEqualTo("-2500");
        assertThat(facts.get("/reitDividends").item().asText()).isEqualTo("1500");
        assertThat(facts.get("/ptpIncome").item().asText()).isEqualTo("3000");
    }

    @Test
    @DisplayName("Form 4684 keeps the 10% AGI floor unless the loss is a qualified disaster loss")
    void testCasualtyLossQualifiedDisasterHandling() throws IOException {
        Map<String, FactTypeWithItem> ordinaryFacts = scenarioFacts("scenario-1-tara-black.json");
        ordinaryFacts.put("/hasCasualtyOrTheft", booleanWrapper(true));
        ordinaryFacts.put("/isInFederalDisasterArea", booleanWrapper(true));
        ordinaryFacts.put("/isQualifiedDisasterLoss", booleanWrapper(false));
        ordinaryFacts.put("/property1CostBasis", dollarWrapper("1000"));
        ordinaryFacts.put("/property1InsuranceReimbursement", dollarWrapper("0"));
        ordinaryFacts.put("/property1FMVBefore", dollarWrapper("1000"));
        ordinaryFacts.put("/property1FMVAfter", dollarWrapper("0"));

        Graph ordinaryGraph = factGraphService.getGraph(ordinaryFacts);
        assertThat(getFactAsBigDecimal(ordinaryGraph, "/deductibleCasualtyLoss"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));

        Map<String, FactTypeWithItem> qualifiedFacts = new HashMap<>(ordinaryFacts);
        qualifiedFacts.put("/isQualifiedDisasterLoss", booleanWrapper(true));

        Graph qualifiedGraph = factGraphService.getGraph(qualifiedFacts);
        assertThat(getFactAsBigDecimal(qualifiedGraph, "/deductibleCasualtyLoss"))
            .isEqualByComparingTo(new BigDecimal("500.00"));
    }

    @Test
    @DisplayName("Form 1040-NR derives tax on ECI from 2025 nonresident brackets")
    void testForm1040NrDerivesTaxOnEciFrom2025Brackets() {
        Map<String, FactTypeWithItem> facts = new HashMap<>();
        facts.put("/isNonresidentAlien", booleanWrapper(true));
        facts.put("/filingStatus", filingStatusWrapper("marriedFilingSeparately"));
        facts.put("/isFilingStatusSingle", booleanWrapper(false));
        facts.put("/isFilingStatusMFJ", booleanWrapper(false));
        facts.put("/isFilingStatusMFS", booleanWrapper(true));
        facts.put("/isFilingStatusHOH", booleanWrapper(false));
        facts.put("/isFilingStatusQSS", booleanWrapper(false));
        facts.put("/wagesECI", dollarWrapper("100000"));
        facts.put("/businessIncomeECI", dollarWrapper("15000"));
        facts.put("/scholarshipIncomeECI", dollarWrapper("0"));
        facts.put("/capitalGainsECI", dollarWrapper("0"));
        facts.put("/rentalIncomeECI", dollarWrapper("0"));
        facts.put("/partnershipIncomeECI", dollarWrapper("0"));
        facts.put("/otherIncomeECI", dollarWrapper("0"));
        facts.put("/itemizedDeductionsNR", dollarWrapper("10000"));
        facts.put("/dividendsFDAP", dollarWrapper("1000"));
        facts.put("/interestFDAP", dollarWrapper("0"));
        facts.put("/royaltiesFDAP", dollarWrapper("500"));
        facts.put("/rentsFDAP", dollarWrapper("0"));
        facts.put("/gamblingFDAP", dollarWrapper("0"));
        facts.put("/socialSecurityFDAP", dollarWrapper("0"));
        facts.put("/capitalGainsFDAP", dollarWrapper("0"));
        facts.put("/otherFDAP", dollarWrapper("0"));
        facts.put("/treatyExemptIncome", dollarWrapper("0"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/taxableIncomeNR"))
            .isEqualByComparingTo(new BigDecimal("105000.00"));
        assertThat(getFactAsBigDecimal(graph, "/taxOnECI"))
            .isEqualByComparingTo(new BigDecimal("18047.00"));
        assertThat(getFactAsBigDecimal(graph, "/taxOnFDAP"))
            .isEqualByComparingTo(new BigDecimal("450.00"));
        assertThat(getFactAsBoolean(graph, "/hasScheduleNEC")).isTrue();
        assertThat(getFactAsBigDecimal(graph, "/scheduleNECTax"))
            .isEqualByComparingTo(new BigDecimal("450.00"));
        assertThat(getFactAsBigDecimal(graph, "/totalTaxNR"))
            .isEqualByComparingTo(new BigDecimal("18497.00"));
    }

    @Test
    @DisplayName("Form 1040-NR applies treaty-exempt scholarship amounts before ECI tax")
    void testForm1040NrTreatyExemptScholarshipHandling() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-nr5-chen.json");
        facts.remove("/scheduleOIHasForeignAddress");
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsString(graph, "/countryOfCitizenship")).isEqualTo("CN");
        assertThat(getFactAsInt(graph, "/daysInUS")).isEqualTo(120);
        assertThat(getFactAsInt(graph, "/daysInUSPriorYear")).isEqualTo(118);
        assertThat(getFactAsInt(graph, "/daysInUSTwoYearsPrior")).isEqualTo(95);
        assertThat(getFactAsInt(graph, "/substantialPresenceWeightedDays")).isEqualTo(174);
        assertThat(getFactAsBoolean(graph, "/scheduleOIHasForeignAddress")).isTrue();
        assertThat(getFactAsBigDecimal(graph, "/scholarshipIncomeECI"))
            .isEqualByComparingTo(new BigDecimal("5000.00"));
        assertThat(getFactAsBigDecimal(graph, "/treatyExemptIncome"))
            .isEqualByComparingTo(new BigDecimal("5000.00"));
        assertThat(getFactAsBigDecimal(graph, "/taxableScholarshipIncomeECI"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        assertThat(getFactAsBigDecimal(graph, "/otherIncomeECI"))
            .isEqualByComparingTo(new BigDecimal("24000.00"));
        assertThat(getFactAsBoolean(graph, "/hasScheduleOI")).isTrue();
        assertThat(getFactAsBoolean(graph, "/scheduleOIRequiresTreatyDisclosure")).isTrue();
        assertThat(getFactAsBigDecimal(graph, "/totalECI"))
            .isEqualByComparingTo(new BigDecimal("24000.00"));
    }

    @Test
    @DisplayName("Schedule E derives rental totals from ATS rental property facts")
    void testScheduleERentalScenarioDerivation() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-18-thompson-rental.json");
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/totalRentalRoyaltyIncome"))
            .isEqualByComparingTo(new BigDecimal("28800.00"));
        assertThat(getFactAsBigDecimal(graph, "/totalRentalExpenses"))
            .isEqualByComparingTo(new BigDecimal("28103.00"));
        assertThat(getFactAsBigDecimal(graph, "/rentalNetIncomeLoss"))
            .isEqualByComparingTo(new BigDecimal("697.00"));
        assertThat(getFactAsBigDecimal(graph, "/scheduleETotalIncomeLoss"))
            .isEqualByComparingTo(new BigDecimal("697.00"));
    }

    @Test
    @DisplayName("Schedule E derives page 2 partnership totals without pulling in portfolio-only K-1 items")
    void testScheduleEPage2PartnershipDerivation() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-29-white-k1.json");
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBoolean(graph, "/hasRentalIncome")).isFalse();
        assertThat(getFactAsBoolean(graph, "/hasScheduleEPage2Activity")).isTrue();
        assertThat(getFactAsBigDecimal(graph, "/partnershipScheduleEIncome"))
            .isEqualByComparingTo(new BigDecimal("145000.00"));
        assertThat(getFactAsBigDecimal(graph, "/scheduleEPage2IncomeLoss"))
            .isEqualByComparingTo(new BigDecimal("145000.00"));
        assertThat(getFactAsBigDecimal(graph, "/scheduleETotalIncomeLoss"))
            .isEqualByComparingTo(new BigDecimal("145000.00"));
    }

    @Test
    @DisplayName("Form 1040-NR uses explicit Schedule E partnership amounts as ECI")
    void testForm1040NrPartnershipIncomeFallsBackFromScheduleE() throws IOException {
        ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-nr2-desilva.json");
        Map<String, Object> partnershipIncome = new HashMap<>();
        partnershipIncome.put("ordinaryIncome", new BigDecimal("30000"));
        partnershipIncome.put("guaranteedPayments", new BigDecimal("15000"));
        Map<String, Object> scheduleE = new HashMap<>();
        scheduleE.put("partnershipIncome", partnershipIncome);
        scenario.setScheduleE(scheduleE);

        Map<String, FactTypeWithItem> facts = new HashMap<>(converter.convert(scenario));
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/partnershipIncomeECI"))
            .isEqualByComparingTo(new BigDecimal("45000.00"));
        assertThat(getFactAsBigDecimal(graph, "/totalECI"))
            .isEqualByComparingTo(new BigDecimal("45000.00"));
        assertThat(getFactAsBigDecimal(graph, "/totalTaxNR"))
            .isEqualByComparingTo(new BigDecimal("5162.00"));
    }

    @Test
    @DisplayName("Form 1040-NR exposes Schedule NEC line-item tax detail")
    void testForm1040NrScheduleNecLineItemTaxes() {
        ATSScenarioData scenario = createMinimalNonresidentScenario();
        scenario.setForm1099Div(List.of(Map.of("ordinaryDividends", new BigDecimal("1000.00"))));
        scenario.setForm1099Int(List.of(Map.of("taxableInterest", new BigDecimal("500.00"))));
        scenario.setForm1099Misc(List.of(
            Map.of("royalties", new BigDecimal("200.00")),
            Map.of(
                "otherIncome", new BigDecimal("100.00"),
                "description", "Consulting prize payout"
            )
        ));
        Map<String, Object> treatyBenefits = new HashMap<>();
        treatyBenefits.put("articleNumber", "12");
        treatyBenefits.put("description", "Reduced royalty withholding");
        treatyBenefits.put("reducedRate", new BigDecimal("0.15"));
        scenario.setTaxTreatyBenefits(treatyBenefits);
        Graph graph = factGraphService.getGraph(new HashMap<>(converter.convert(scenario)));

        assertThat(getFactAsBigDecimal(graph, "/dividendsFDAPTax"))
            .isEqualByComparingTo(new BigDecimal("150.00"));
        assertThat(getFactAsBigDecimal(graph, "/interestFDAPTax"))
            .isEqualByComparingTo(new BigDecimal("75.00"));
        assertThat(getFactAsBigDecimal(graph, "/royaltiesFDAPTax"))
            .isEqualByComparingTo(new BigDecimal("30.00"));
        assertThat(getFactAsBigDecimal(graph, "/capitalGainsFDAPTax"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        assertThat(getFactAsBigDecimal(graph, "/otherFDAPTax"))
            .isEqualByComparingTo(new BigDecimal("15.00"));
        assertThat(getFactAsString(graph, "/otherFDAPDescription")).isEqualTo("Consulting prize payout");
        assertThat(getFactAsString(graph, "/treatyBenefitDescription")).isEqualTo("Reduced royalty withholding");
        assertThat(getFactAsString(graph, "/treatyArticle")).isEqualTo("12");
        assertThat(getFactAsInt(graph, "/scheduleNECLineItemCount")).isEqualTo(4);
        assertThat(getFactAsBigDecimal(graph, "/scheduleNECTax"))
            .isEqualByComparingTo(new BigDecimal("270.00"));
    }

    private Map<String, FactTypeWithItem> scenarioFacts(String scenarioFileName) throws IOException {
        ATSScenarioData scenario = ATSScenarioLoader.loadScenario(scenarioFileName);
        return new HashMap<>(converter.convert(scenario));
    }

    private void distributeTotalWagesAcrossW2s(Map<String, FactTypeWithItem> facts, BigDecimal totalWages) {
        List<String> wagePaths = facts.keySet().stream()
            .filter(path -> path.startsWith("/formW2s/#") && path.endsWith("/wages"))
            .sorted(Comparator.naturalOrder())
            .toList();

        assertThat(wagePaths).isNotEmpty();

        BigDecimal originalTotalWages = wagePaths.stream()
            .map(path -> new BigDecimal(facts.get(path).item().asText()))
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        if (facts.containsKey("/atsAgiOverride")) {
            BigDecimal originalAgi = new BigDecimal(facts.get("/atsAgiOverride").item().asText());
            BigDecimal wageDelta = totalWages.subtract(originalTotalWages);
            facts.put("/atsAgiOverride", dollarWrapper(originalAgi.add(wageDelta).toPlainString()));
        }

        BigDecimal[] quotientAndRemainder = totalWages.divideAndRemainder(BigDecimal.valueOf(wagePaths.size()));
        BigDecimal evenShare = quotientAndRemainder[0];
        BigDecimal remainder = quotientAndRemainder[1];

        for (int i = 0; i < wagePaths.size(); i++) {
            String wagesPath = wagePaths.get(i);
            BigDecimal amount = evenShare;
            if (i == wagePaths.size() - 1) {
                amount = amount.add(remainder);
            }

            String basePath = wagesPath.substring(0, wagesPath.length() - "/wages".length());
            facts.put(basePath + "/wages", dollarWrapper(amount.toPlainString()));
            facts.put(basePath + "/writableWages", dollarWrapper(amount.toPlainString()));
            facts.put(basePath + "/socialSecurityWages", dollarWrapper(amount.toPlainString()));
            facts.put(basePath + "/medicareWagesAndTips", dollarWrapper(amount.toPlainString()));
            if (facts.containsKey(basePath + "/stateWages")) {
                facts.put(basePath + "/stateWages", dollarWrapper(amount.toPlainString()));
            }
        }
    }

    private FactTypeWithItem booleanWrapper(boolean value) {
        return new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.valueOf(value));
    }

    private FactTypeWithItem dollarWrapper(String value) {
        return new FactTypeWithItem(DOLLAR_WRAPPER, nodeFactory.textNode(value));
    }

    private FactTypeWithItem intWrapper(int value) {
        return new FactTypeWithItem(INT_WRAPPER, nodeFactory.numberNode(value));
    }

    private FactTypeWithItem filingStatusWrapper(String value) {
        var enumNode = nodeFactory.objectNode();
        var valueArray = nodeFactory.arrayNode();
        valueArray.add(value);
        enumNode.set("value", valueArray);
        enumNode.put("enumOptionsPath", "/filingStatusOptions");
        return new FactTypeWithItem(ENUM_WRAPPER, enumNode);
    }

    private ATSScenarioData createMinimalNonresidentScenario() {
        ATSScenarioData scenario = new ATSScenarioData();
        scenario.setTaxYear(2025);
        scenario.setFormType("1040-NR");
        scenario.setFilingStatus(3);
        scenario.setPrimaryTaxpayer(new gov.irs.directfile.api.ats.model.ATSTaxpayer());
        scenario.getPrimaryTaxpayer().setFirstName("Test");
        scenario.getPrimaryTaxpayer().setLastName("Nonresident");
        scenario.getPrimaryTaxpayer().setSsn("123-45-6789");
        return scenario;
    }

    private Map<String, Object> qbiBusiness(
        String businessName,
        String qbi,
        String w2Wages,
        String ubia,
        boolean isSstb
    ) {
        Map<String, Object> business = new HashMap<>();
        business.put("businessName", businessName);
        business.put("qualifiedBusinessIncome", new BigDecimal(qbi));
        business.put("w2Wages", new BigDecimal(w2Wages));
        business.put("ubia", new BigDecimal(ubia));
        business.put("isSpecifiedServiceBusiness", isSstb);
        return business;
    }

    private Boolean getFactAsBoolean(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue()) {
                Object value = result.get();
                if (value instanceof Boolean) {
                    return (Boolean) value;
                }
                if (value != null) {
                    return Boolean.valueOf(value.toString());
                }
            }
        } catch (Exception e) {
            return null;
        }

        return null;
    }

    private BigDecimal getFactAsBigDecimal(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue()) {
                Object value = result.get();
                if (value instanceof scala.math.BigDecimal) {
                    return new BigDecimal(value.toString()).setScale(2, RoundingMode.HALF_UP);
                } else if (value instanceof BigDecimal) {
                    return ((BigDecimal) value).setScale(2, RoundingMode.HALF_UP);
                } else if (value instanceof Number) {
                    return BigDecimal.valueOf(((Number) value).doubleValue())
                        .setScale(2, RoundingMode.HALF_UP);
                } else if (value != null) {
                    return new BigDecimal(value.toString()).setScale(2, RoundingMode.HALF_UP);
                }
            }
        } catch (Exception e) {
            return null;
        }

        return null;
    }

    private String getFactAsString(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue()) {
                Object value = result.get();
                if (value != null) {
                    return value.toString();
                }
            }
        } catch (Exception e) {
            return null;
        }

        return null;
    }

    private Integer getFactAsInt(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue()) {
                Object value = result.get();
                if (value instanceof Number) {
                    return ((Number) value).intValue();
                }
                if (value != null) {
                    return Integer.parseInt(value.toString());
                }
            }
        } catch (Exception e) {
            return null;
        }

        return null;
    }

    private static String buildTestDbUrl(String prefix) {
        return "jdbc:h2:mem:" + prefix + "_" + UUID.randomUUID().toString().replace("-", "")
                + ";DB_CLOSE_DELAY=-1;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DEFAULT_NULL_ORDERING=HIGH";
    }
}
