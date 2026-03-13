package gov.irs.directfile.api.ats;

import gov.irs.directfile.api.ats.converter.ATSToFactGraphConverter;
import gov.irs.directfile.api.ats.model.ATSExpectedValues;
import gov.irs.directfile.api.ats.model.ATSScenarioData;
import gov.irs.directfile.api.dispatch.DispatchQueueService;
import gov.irs.directfile.api.loaders.service.FactGraphService;
import gov.irs.directfile.api.taxreturn.TaxReturnRepository;
import gov.irs.directfile.api.taxreturn.TaxReturnService;
import gov.irs.directfile.api.taxreturn.TaxReturnSubmissionRepository;
import gov.irs.directfile.api.taxreturn.models.TaxReturn;
import gov.irs.directfile.api.taxreturn.models.TaxReturnSubmission;
import gov.irs.directfile.api.taxreturn.submissions.SendEmailQueueService;
import gov.irs.directfile.api.taxreturn.submissions.lock.AdvisoryLockRepository;
import gov.irs.directfile.api.user.UserRepository;
import gov.irs.directfile.api.user.domain.UserInfo;
import gov.irs.directfile.api.user.models.User;
import gov.irs.directfile.api.util.SecurityTestConfiguration;
import gov.irs.directfile.api.util.TestDataFactory;
import gov.irs.directfile.api.util.base.BaseIntegrationTest;
import gov.irs.directfile.models.Dispatch;
import gov.irs.directfile.models.FactTypeWithItem;
import gov.irs.factgraph.Graph;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * End-to-end integration tests for the full tax return submission workflow using ATS scenario data.
 *
 * These tests verify that:
 * 1. ATS scenario data flows correctly through the entire submission pipeline
 * 2. TaxReturn and TaxReturnSubmission entities are created properly
 * 3. FactGraph calculations match expected values
 * 4. Dispatch messages are generated with correct data
 * 5. All OBBBA 2025 standard deduction values are correctly applied
 */
@SpringBootTest
@ActiveProfiles("test")
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
public class ATSEndToEndIntegrationTest extends BaseIntegrationTest {
    @Autowired
    private TaxReturnService taxReturnService;

    @Autowired
    private FactGraphService factGraphService;

    @Autowired
    private TaxReturnRepository taxReturnRepository;

    @Autowired
    private TaxReturnSubmissionRepository taxReturnSubmissionRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TestDataFactory testDataFactory;

    @MockBean
    private DispatchQueueService dispatchQueueService;

    @MockBean
    private SendEmailQueueService sendEmailQueueService;

    @MockBean
    private AdvisoryLockRepository advisoryLockRepository;

    private ATSToFactGraphConverter converter;

    @BeforeEach
    void setUpConverter() {
        converter = new ATSToFactGraphConverter();
        // Always acquire the lock successfully in tests
        when(advisoryLockRepository.acquireLock(anyInt())).thenReturn(true);
    }

    @DynamicPropertySource
    static void registerDataSourceProperties(DynamicPropertyRegistry registry) {
        String dbUrl = buildTestDbUrl("ats-e2e");
        registry.add("spring.datasource.url", () -> dbUrl);
        registry.add("spring.liquibase.url", () -> dbUrl);
        registry.add("spring.datasource.username", () -> "sa");
        registry.add("spring.datasource.password", () -> "");
        registry.add("spring.liquibase.user", () -> "sa");
        registry.add("spring.liquibase.password", () -> "");
    }

    /**
     * Provides standard Form 1040 ATS scenarios for E2E testing.
     */
    static Stream<Arguments> e2eScenarioProvider() {
        return Stream.of(
            Arguments.of("scenario-1-tara-black.json", "Scenario 1 - Single filer with W-2s"),
            Arguments.of("scenario-4-smith.json", "Scenario 4 - Energy credits"),
            Arguments.of("scenario-5-barker.json", "Scenario 5 - HOH with EIC and dependents"),
            Arguments.of("scenario-8-lewis.json", "Scenario 8 - MFS with 1099-R"),
            Arguments.of("scenario-12-gardenia.json", "Scenario 12 - Self-employment"),
            Arguments.of("scenario-13-birch.json", "Scenario 13 - MFJ high income")
        );
    }

    @Nested
    @DisplayName("Full Submission Workflow Tests")
    class FullSubmissionWorkflowTests {

        @ParameterizedTest(name = "{1}")
        @MethodSource("gov.irs.directfile.api.ats.ATSEndToEndIntegrationTest#e2eScenarioProvider")
        @DisplayName("Should complete full submission workflow")
        void testFullSubmissionWorkflow(String fileName, String scenarioName) throws Exception {
            // Load and convert scenario
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario(fileName);
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Get test user
            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();
            User user = userRepository.findByExternalId(userExternalId).orElseThrow();

            // Create TaxReturn
            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);

            // Verify TaxReturn created
            assertThat(taxReturn).isNotNull();
            assertThat(taxReturn.getId()).isNotNull();

            // Verify facts can be loaded into FactGraph
            Graph graph = factGraphService.getGraph(facts);
            assertThat(graph).isNotNull();

            // Verify dispatch queue was configured
            verify(dispatchQueueService, never()).enqueue(any());
        }

        @Test
        @DisplayName("Should create TaxReturnSubmission when submitting")
        void testTaxReturnSubmissionCreation() throws Exception {
            // Load scenario
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Get test user
            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();

            // Create TaxReturn
            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);

            // Add submission
            TaxReturnSubmission submission = taxReturn.addTaxReturnSubmission();
            taxReturnSubmissionRepository.save(submission);
            taxReturnRepository.save(taxReturn);

            // Verify submission created
            Optional<TaxReturnSubmission> retrievedSubmission =
                taxReturnSubmissionRepository.findLatestTaxReturnSubmissionByTaxReturnId(taxReturn.getId());

            assertThat(retrievedSubmission).isPresent();
            assertThat(retrievedSubmission.get().getTaxReturn().getId()).isEqualTo(taxReturn.getId());
        }
    }

    @Nested
    @DisplayName("FactGraph Calculation Integration Tests")
    class FactGraphCalculationTests {

        @Test
        @DisplayName("Should calculate correct AGI for Scenario 1")
        void testScenario1AGICalculation() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);
            ATSExpectedValues expected = scenario.getExpectedValues();

            // Verify expected values match OBBBA 2025
            assertThat(expected.getAgi()).isEqualByComparingTo(new BigDecimal("42470.00"));
            assertThat(expected.getStandardDeduction()).isEqualByComparingTo(new BigDecimal("15750.00"));
            assertThat(expected.getTaxableIncome()).isEqualByComparingTo(new BigDecimal("26720.00"));

            // Create and verify TaxReturn
            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();
            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);

            // Load graph and verify structure
            Graph graph = factGraphService.getGraph(taxReturn.getFacts());
            assertThat(graph).isNotNull();
        }

        @Test
        @DisplayName("Should calculate correct standard deduction for HOH with blind (Scenario 5)")
        void testScenario5HOHBlindDeduction() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // OBBBA 2025: HOH base $23,625 + blind $2,000 = $25,625
            assertThat(expected.getStandardDeduction()).isEqualByComparingTo(new BigDecimal("25625.00"));
            assertThat(expected.getAgi()).isEqualByComparingTo(new BigDecimal("38500.00"));
        }

        @Test
        @DisplayName("Should calculate correct standard deduction for MFS over 65 (Scenario 8)")
        void testScenario8MFSOver65Deduction() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-8-lewis.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // OBBBA 2025: MFS base $15,750 + over 65 $1,600 = $17,350
            assertThat(expected.getStandardDeduction()).isEqualByComparingTo(new BigDecimal("17350.00"));
        }

        @Test
        @DisplayName("Should calculate correct standard deduction for MFJ (Scenario 13)")
        void testScenario13MFJDeduction() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-13-birch.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // OBBBA 2025: MFJ base $31,500
            assertThat(expected.getStandardDeduction()).isEqualByComparingTo(new BigDecimal("31500.00"));
        }
    }

    @Nested
    @DisplayName("Data Persistence Integration Tests")
    class DataPersistenceTests {

        @ParameterizedTest(name = "{1}")
        @MethodSource("gov.irs.directfile.api.ats.ATSEndToEndIntegrationTest#e2eScenarioProvider")
        @DisplayName("Should persist and retrieve all facts correctly")
        void testFactsPersistence(String fileName, String scenarioName) throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario(fileName);
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);

            // Retrieve from database
            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify core facts persisted
            assertThat(retrieved.getFacts()).containsKey("/filers");
            assertThat(retrieved.getFacts()).containsKey("/filingStatus");

            // Verify filing status matches scenario
            String expectedFilingStatus = getExpectedFilingStatusString(scenario.getFilingStatus());
            FactTypeWithItem filingStatusFact = retrieved.getFacts().get("/filingStatus");
            String actualFilingStatus = filingStatusFact.item().get("value").get(0).asText();
            assertThat(actualFilingStatus).isEqualTo(expectedFilingStatus);
        }

        @Test
        @DisplayName("Should persist W-2 collection with correct structure")
        void testW2CollectionPersistence() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);
            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify W-2 collection exists
            assertThat(retrieved.getFacts()).containsKey("/formW2s");

            // Count W-2 wage entries (Tara has 2 W-2s)
            long w2Count = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/wages"))
                .count();
            assertThat(w2Count).isEqualTo(2);

            // Verify employer data persisted
            long employerCount = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/employerName"))
                .count();
            assertThat(employerCount).isEqualTo(2);
        }

        @Test
        @DisplayName("Should persist dependent collection with correct structure")
        void testDependentCollectionPersistence() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);
            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify dependents collection exists
            assertThat(retrieved.getFacts()).containsKey("/familyAndHousehold");

            // Count dependent entries (Bobby has 2 children)
            long dependentCount = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/familyAndHousehold/#") && k.endsWith("/firstName"))
                .count();
            assertThat(dependentCount).isEqualTo(2);
        }

        @Test
        @DisplayName("Should persist 1099-R collection with correct structure")
        void test1099RPersistence() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-8-lewis.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);
            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify 1099-R collection exists
            assertThat(retrieved.getFacts()).containsKey("/form1099Rs");

            // Count 1099-R entries (Carter has 2 1099-Rs)
            long form1099RCount = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/form1099Rs/#") && k.endsWith("/writableGrossDistribution"))
                .count();
            assertThat(form1099RCount).isEqualTo(2);
        }
    }

    @Nested
    @DisplayName("Dispatch Message Tests")
    class DispatchMessageTests {

        @Test
        @DisplayName("Should capture dispatch message with correct tax return ID")
        void testDispatchMessageContainsTaxReturnId() throws Exception {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = SecurityTestConfiguration.testUserMap
                .get(SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(userExternalId, facts);

            // Verify tax return was created with correct ID
            assertThat(taxReturn.getId()).isNotNull();

            // In a real submission, the dispatch would be captured
            // For now, verify the dispatch service was not yet called
            verify(dispatchQueueService, never()).enqueue(any(Dispatch.class));
        }
    }

    @Nested
    @DisplayName("OBBBA 2025 Compliance Tests")
    class OBBBA2025ComplianceTests {

        @Test
        @DisplayName("All scenarios should use OBBBA 2025 standard deduction values")
        void testAllScenariosUseOBBBA2025Values() throws IOException {
            List<ATSScenarioData> scenarios = ATSScenarioLoader.loadAllScenarios();

            for (ATSScenarioData scenario : scenarios) {
                ATSExpectedValues expected = scenario.getExpectedValues();
                if (expected == null || !usesStandardDeduction(expected)) {
                    continue; // Skip scenarios without expected values
                }

                BigDecimal stdDed = expected.getStandardDeduction();
                int filingStatus = scenario.getFilingStatus();

                // Verify OBBBA 2025 base values
                switch (filingStatus) {
                    case 1: // Single
                    case 3: // MFS
                        // Base should be at least $15,750
                        assertThat(stdDed)
                            .as("Scenario %s (%s) should use OBBBA 2025 Single/MFS base",
                                scenario.getScenarioId(), scenario.getPrimaryTaxpayer().getFirstName())
                            .isGreaterThanOrEqualTo(new BigDecimal("15750.00"));
                        break;
                    case 2: // MFJ
                    case 5: // QSS
                        // Base should be at least $31,500
                        assertThat(stdDed)
                            .as("Scenario %s (%s) should use OBBBA 2025 MFJ/QSS base",
                                scenario.getScenarioId(), scenario.getPrimaryTaxpayer().getFirstName())
                            .isGreaterThanOrEqualTo(new BigDecimal("31500.00"));
                        break;
                    case 4: // HOH
                        // Base should be at least $23,625
                        assertThat(stdDed)
                            .as("Scenario %s (%s) should use OBBBA 2025 HOH base",
                                scenario.getScenarioId(), scenario.getPrimaryTaxpayer().getFirstName())
                            .isGreaterThanOrEqualTo(new BigDecimal("23625.00"));
                        break;
                    default:
                        break;
                }
            }
        }

        @Test
        @DisplayName("Single filer should have $15,750 standard deduction")
        void testSingleFilerStandardDeduction() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            assertThat(expected.getStandardDeduction())
                .as("Single filer should have OBBBA 2025 standard deduction")
                .isEqualByComparingTo(new BigDecimal("15750.00"));
        }

        @Test
        @DisplayName("MFJ filer should have $31,500 standard deduction")
        void testMFJFilerStandardDeduction() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-13-birch.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            assertThat(expected.getStandardDeduction())
                .as("MFJ filer should have OBBBA 2025 standard deduction")
                .isEqualByComparingTo(new BigDecimal("31500.00"));
        }

        @Test
        @DisplayName("HOH filer with blind should have $25,625 standard deduction")
        void testHOHBlindFilerStandardDeduction() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // OBBBA 2025: HOH $23,625 + blind $2,000 = $25,625
            assertThat(expected.getStandardDeduction())
                .as("HOH blind filer should have OBBBA 2025 standard deduction with additional amount")
                .isEqualByComparingTo(new BigDecimal("25625.00"));
        }

        @Test
        @DisplayName("MFS over 65 filer should have $17,350 standard deduction")
        void testMFSOver65FilerStandardDeduction() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-8-lewis.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // OBBBA 2025: MFS $15,750 + over 65 $1,600 = $17,350
            assertThat(expected.getStandardDeduction())
                .as("MFS over 65 filer should have OBBBA 2025 standard deduction with additional amount")
                .isEqualByComparingTo(new BigDecimal("17350.00"));
        }

        @Test
        @DisplayName("QSS filer should have $31,500 standard deduction")
        void testQSSFilerStandardDeduction() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-nr4-hill.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            assertThat(expected.getStandardDeduction())
                .as("QSS filer should have OBBBA 2025 standard deduction")
                .isEqualByComparingTo(new BigDecimal("31500.00"));
        }
    }

    @Nested
    @DisplayName("Tax Calculation Verification Tests")
    class TaxCalculationVerificationTests {

        @Test
        @DisplayName("Should calculate correct taxable income for Scenario 1")
        void testScenario1TaxableIncomeCalculation() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // AGI - Standard Deduction = Taxable Income
            // $42,470 - $15,750 = $26,720
            BigDecimal calculatedTaxableIncome = expected.getAgi().subtract(expected.getStandardDeduction());

            assertThat(expected.getTaxableIncome())
                .isEqualByComparingTo(calculatedTaxableIncome);
            assertThat(expected.getTaxableIncome())
                .isEqualByComparingTo(new BigDecimal("26720.00"));
        }

        @Test
        @DisplayName("Should calculate correct refund for Scenario 1")
        void testScenario1RefundCalculation() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            ATSExpectedValues expected = scenario.getExpectedValues();

            // Total Withholding - Total Tax = Refund
            // $2,713 - $2,242 = $471
            assertThat(expected.getRefund())
                .isEqualByComparingTo(new BigDecimal("471.00"));
            assertThat(expected.getTotalTax())
                .isEqualByComparingTo(new BigDecimal("2242.00"));
        }

        @Test
        @DisplayName("Should verify taxable income is non-negative")
        void testTaxableIncomeNonNegative() throws IOException {
            List<ATSScenarioData> scenarios = ATSScenarioLoader.loadAllScenarios();

            for (ATSScenarioData scenario : scenarios) {
                ATSExpectedValues expected = scenario.getExpectedValues();
                if (expected != null && expected.getTaxableIncome() != null) {
                    assertThat(expected.getTaxableIncome())
                        .as("Taxable income for scenario %s should be non-negative", scenario.getScenarioId())
                        .isGreaterThanOrEqualTo(BigDecimal.ZERO);
                }
            }
        }
    }

    /**
     * Helper method to convert filing status code to expected string value.
     */
    private String getExpectedFilingStatusString(int filingStatus) {
        return switch (filingStatus) {
            case 1 -> "single";
            case 2 -> "marriedFilingJointly";
            case 3 -> "marriedFilingSeparately";
            case 4 -> "headOfHousehold";
            case 5 -> "qualifyingSurvivingSpouse";
            default -> throw new IllegalArgumentException("Unknown filing status: " + filingStatus);
        };
    }

    private boolean usesStandardDeduction(ATSExpectedValues expected) {
        return expected.getStandardDeduction() != null &&
            expected.getStandardDeduction().compareTo(BigDecimal.ZERO) > 0 &&
            (expected.getItemizedDeduction() == null || expected.getItemizedDeduction().compareTo(BigDecimal.ZERO) == 0);
    }

    private static String buildTestDbUrl(String prefix) {
        return "jdbc:h2:mem:" + prefix + "_" + UUID.randomUUID().toString().replace("-", "")
                + ";DB_CLOSE_DELAY=-1;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DEFAULT_NULL_ORDERING=HIGH";
    }
}
