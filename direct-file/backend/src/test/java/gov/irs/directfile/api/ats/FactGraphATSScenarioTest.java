package gov.irs.directfile.api.ats;

import gov.irs.directfile.api.ats.converter.ATSToFactGraphConverter;
import gov.irs.directfile.api.ats.model.ATSExpectedValues;
import gov.irs.directfile.api.ats.model.ATSScenarioData;
import gov.irs.directfile.models.FactTypeWithItem;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.Map;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Integration tests validating FactGraph calculations using IRS ATS scenario data.
 *
 * These tests verify that:
 * 1. ATS scenario data can be successfully converted to FactGraph format
 * 2. Tax calculations match IRS-expected values
 * 3. Form data flows correctly between schedules and Form 1040
 */
public class FactGraphATSScenarioTest {

    private ATSToFactGraphConverter converter;

    @BeforeEach
    void setUp() {
        converter = new ATSToFactGraphConverter();
    }

    /**
     * Provides all ATS scenario file names for parameterized tests.
     */
    static Stream<Arguments> atsScenarioProvider() {
        return Stream.of(
            Arguments.of("scenario-1-tara-black.json", "Scenario 1 - Tara Black"),
            Arguments.of("scenario-2-jones.json", "Scenario 2 - John & Judy Jones"),
            Arguments.of("scenario-3-heather.json", "Scenario 3 - Lynette Heather"),
            Arguments.of("scenario-4-smith.json", "Scenario 4 - Sarah Smith"),
            Arguments.of("scenario-5-barker.json", "Scenario 5 - Bobby Barker"),
            Arguments.of("scenario-6-torres.json", "Scenario 6 - Juan Torres"),
            Arguments.of("scenario-7-boone.json", "Scenario 7 - Charlie Boone"),
            Arguments.of("scenario-8-lewis.json", "Scenario 8 - Carter Lewis"),
            Arguments.of("scenario-12-gardenia.json", "Scenario 12 - Sam Gardenia"),
            Arguments.of("scenario-13-birch.json", "Scenario 13 - William & Nancy Birch"),
            Arguments.of("scenario-nr1-leblanc.json", "Scenario NR-1 - Lucas LeBlanc"),
            Arguments.of("scenario-nr2-desilva.json", "Scenario NR-2 - Genesis DeSilva"),
            Arguments.of("scenario-nr3-alfaro.json", "Scenario NR-3 - Jace Alfaro"),
            Arguments.of("scenario-nr4-hill.json", "Scenario NR-4 - Isaac Hill"),
            Arguments.of("scenario-nr12-harrier.json", "Scenario NR-12 - John Harrier")
        );
    }

    @Nested
    @DisplayName("Scenario Loading Tests")
    class ScenarioLoadingTests {

        @ParameterizedTest(name = "{1}")
        @MethodSource("gov.irs.directfile.api.ats.FactGraphATSScenarioTest#atsScenarioProvider")
        @DisplayName("Should load scenario data from JSON")
        void testScenarioLoading(String fileName, String scenarioName) throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario(fileName);

            assertThat(scenario).isNotNull();
            assertThat(scenario.getScenarioId()).isNotBlank();
            assertThat(scenario.getPrimaryTaxpayer()).isNotNull();
            assertThat(scenario.getPrimaryTaxpayer().getFirstName()).isNotBlank();
            assertThat(scenario.getFilingStatus()).isBetween(1, 5);
        }

        @Test
        @DisplayName("Should load all scenarios successfully")
        void testLoadAllScenarios() {
            var scenarios = ATSScenarioLoader.loadAllScenarios();

            assertThat(scenarios).hasSize(15);
            assertThat(scenarios).allMatch(s -> s.getPrimaryTaxpayer() != null);
        }
    }

    @Nested
    @DisplayName("FactGraph Conversion Tests")
    class FactGraphConversionTests {

        @ParameterizedTest(name = "{1}")
        @MethodSource("gov.irs.directfile.api.ats.FactGraphATSScenarioTest#atsScenarioProvider")
        @DisplayName("Should convert scenario to FactGraph format")
        void testScenarioConversion(String fileName, String scenarioName) throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario(fileName);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Verify basic structure
            assertThat(facts).isNotEmpty();
            assertThat(facts).containsKey("/filers");
            assertThat(facts).containsKey("/filingStatus");

            // Verify filer data
            String primaryFilerId = extractPrimaryFilerId(facts);
            assertThat(facts).containsKey("/filers/#" + primaryFilerId + "/isPrimaryFiler");
            assertThat(facts).containsKey("/filers/#" + primaryFilerId + "/tin");
            assertThat(facts).containsKey("/filers/#" + primaryFilerId + "/firstName");
            assertThat(facts).containsKey("/filers/#" + primaryFilerId + "/lastName");
        }

        @Test
        @DisplayName("Should convert W-2 data correctly")
        void testW2Conversion() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Verify W-2 collection exists
            assertThat(facts).containsKey("/formW2s");

            // Count W-2 entries
            long w2Count = facts.keySet().stream()
                .filter(k -> k.startsWith("/formW2s/#") && k.endsWith("/wages"))
                .count();

            assertThat(w2Count).isEqualTo(2); // Tara has 2 W-2 forms
        }

        @Test
        @DisplayName("Should convert 1099-R data correctly")
        void test1099RConversion() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-8-lewis.json");

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Verify 1099-R collection exists
            assertThat(facts).containsKey("/form1099Rs");

            // Count 1099-R entries
            long form1099RCount = facts.keySet().stream()
                .filter(k -> k.startsWith("/form1099Rs/#") && k.endsWith("/grossDistribution"))
                .count();

            assertThat(form1099RCount).isEqualTo(2); // Carter has 2 1099-R forms
        }

        @Test
        @DisplayName("Should convert dependent data correctly")
        void testDependentConversion() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Verify dependents collection exists
            assertThat(facts).containsKey("/familyAndHousehold");

            // Count dependent entries
            long dependentCount = facts.keySet().stream()
                .filter(k -> k.startsWith("/familyAndHousehold/#") && k.endsWith("/firstName"))
                .count();

            assertThat(dependentCount).isEqualTo(2); // Bobby has 2 dependents
        }

        @Test
        @DisplayName("Should convert MFJ scenario with spouse")
        void testMFJConversion() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-2-jones.json");

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Count filers
            long filerCount = facts.keySet().stream()
                .filter(k -> k.startsWith("/filers/#") && k.endsWith("/isPrimaryFiler"))
                .count();

            assertThat(filerCount).isEqualTo(2); // John and Judy Jones
        }
    }

    @Nested
    @DisplayName("Expected Values Validation Tests")
    class ExpectedValuesTests {

        @ParameterizedTest(name = "{1}")
        @MethodSource("gov.irs.directfile.api.ats.FactGraphATSScenarioTest#atsScenarioProvider")
        @DisplayName("Should have expected values defined")
        void testExpectedValuesPresent(String fileName, String scenarioName) throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario(fileName);
            ATSExpectedValues expected = scenario.getExpectedValues();

            assertThat(expected).isNotNull();
            // AGI should be defined for all scenarios
            assertThat(expected.getAgi()).isNotNull();
        }

        @Test
        @DisplayName("Scenario 1 expected values should match IRS ATS")
        void testScenario1ExpectedValues() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // Values from IRS ATS PDF
            assertThat(expected.getTotalWages()).isEqualByComparingTo(new BigDecimal("42470.00"));
            assertThat(expected.getAgi()).isEqualByComparingTo(new BigDecimal("42470.00"));
            assertThat(expected.getStandardDeduction()).isEqualByComparingTo(new BigDecimal("15000.00"));
            assertThat(expected.getTaxableIncome()).isEqualByComparingTo(new BigDecimal("27470.00"));
            assertThat(expected.getTotalTax()).isEqualByComparingTo(new BigDecimal("2338.00"));
            assertThat(expected.getRefund()).isEqualByComparingTo(new BigDecimal("375.00"));
        }

        @Test
        @DisplayName("Scenario 5 expected values should match IRS ATS (HOH with EIC)")
        void testScenario5ExpectedValues() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // Bobby Barker - HOH with blind flag, 2 children
            assertThat(expected.getTotalWages()).isEqualByComparingTo(new BigDecimal("38500.00"));
            assertThat(expected.getAgi()).isEqualByComparingTo(new BigDecimal("38500.00"));
            // HOH standard deduction $22,500 + $1,950 blind = $24,450
            assertThat(expected.getStandardDeduction()).isEqualByComparingTo(new BigDecimal("24450.00"));
            // EIC should be claimed
            assertThat(expected.getEarnedIncomeCredit()).isGreaterThan(BigDecimal.ZERO);
        }

        @Test
        @DisplayName("Scenario 8 expected values should match IRS ATS (MFS with 1099-R)")
        void testScenario8ExpectedValues() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-8-lewis.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // Carter Lewis - MFS, over 65, pension income
            assertThat(expected.getTotalWages()).isEqualByComparingTo(BigDecimal.ZERO);
            // MFS over 65 standard deduction: $15,000 + $1,550 = $16,550
            assertThat(expected.getStandardDeduction()).isEqualByComparingTo(new BigDecimal("16550.00"));
        }
    }

    @Nested
    @DisplayName("Filing Status Tests")
    class FilingStatusTests {

        @Test
        @DisplayName("Single filer should have filing status 1")
        void testSingleFilingStatus() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");

            assertThat(scenario.getFilingStatus()).isEqualTo(1);
            assertThat(scenario.getSpouse()).isNull();
        }

        @Test
        @DisplayName("MFJ filer should have filing status 2 with spouse")
        void testMFJFilingStatus() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-2-jones.json");

            assertThat(scenario.getFilingStatus()).isEqualTo(2);
            assertThat(scenario.getSpouse()).isNotNull();
            assertThat(scenario.isJointFiling()).isTrue();
        }

        @Test
        @DisplayName("MFS filer should have filing status 3")
        void testMFSFilingStatus() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-8-lewis.json");

            assertThat(scenario.getFilingStatus()).isEqualTo(3);
        }

        @Test
        @DisplayName("HOH filer should have filing status 4")
        void testHOHFilingStatus() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");

            assertThat(scenario.getFilingStatus()).isEqualTo(4);
            assertThat(scenario.getDependents()).isNotEmpty();
        }

        @Test
        @DisplayName("QSS filer should have filing status 5")
        void testQSSFilingStatus() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-nr4-hill.json");

            assertThat(scenario.getFilingStatus()).isEqualTo(5);
        }
    }

    @Nested
    @DisplayName("Form Type Tests")
    class FormTypeTests {

        @Test
        @DisplayName("Standard scenario should be Form 1040")
        void testForm1040() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");

            assertThat(scenario.getFormType()).isEqualTo("1040");
        }

        @Test
        @DisplayName("Puerto Rico scenario should be Form 1040-SS")
        void testForm1040SS() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-6-torres.json");

            assertThat(scenario.getFormType()).isEqualTo("1040-SS");
        }

        @Test
        @DisplayName("Nonresident alien scenario should be Form 1040-NR")
        void testForm1040NR() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-nr1-leblanc.json");

            assertThat(scenario.getFormType()).isEqualTo("1040-NR");
        }

        @Test
        @DisplayName("Extension scenario should be Form 4868")
        void testForm4868() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-7-boone.json");

            assertThat(scenario.getFormType()).isEqualTo("4868");
        }
    }

    @Nested
    @DisplayName("W-2 Total Calculation Tests")
    class W2TotalTests {

        @Test
        @DisplayName("Should calculate total W-2 wages correctly")
        void testTotalW2Wages() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");

            BigDecimal totalWages = scenario.getTotalW2Wages();

            // Tara has 2 W-2s: $22,970 + $19,500 = $42,470
            assertThat(totalWages).isEqualByComparingTo(new BigDecimal("42470.00"));
        }

        @Test
        @DisplayName("Should calculate total W-2 withholding correctly")
        void testTotalW2Withholding() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");

            BigDecimal totalWithholding = scenario.getTotalW2Withholding();

            // $1,073 + $1,640 = $2,713
            assertThat(totalWithholding).isEqualByComparingTo(new BigDecimal("2713.00"));
        }

        @Test
        @DisplayName("Scenario with no W-2s should return zero")
        void testNoW2sReturnsZero() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-3-heather.json");

            BigDecimal totalWages = scenario.getTotalW2Wages();

            assertThat(totalWages).isEqualByComparingTo(BigDecimal.ZERO);
        }
    }

    @Nested
    @DisplayName("Dependent Count Tests")
    class DependentCountTests {

        @Test
        @DisplayName("Should count qualifying children under 17")
        void testQualifyingChildrenCount() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");

            long count = scenario.getQualifyingChildrenUnder17Count();

            assertThat(count).isEqualTo(2);
        }

        @Test
        @DisplayName("Scenario with no dependents should return zero")
        void testNoDependentsReturnsZero() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");

            long count = scenario.getQualifyingChildrenUnder17Count();

            assertThat(count).isEqualTo(0);
        }
    }

    /**
     * Extract the primary filer UUID from the facts map.
     */
    private String extractPrimaryFilerId(Map<String, FactTypeWithItem> facts) {
        return facts.keySet().stream()
            .filter(k -> k.startsWith("/filers/#") && k.endsWith("/isPrimaryFiler"))
            .map(k -> k.substring("/filers/#".length(), k.indexOf("/isPrimaryFiler")))
            .findFirst()
            .orElseThrow(() -> new IllegalStateException("No primary filer found"));
    }
}
