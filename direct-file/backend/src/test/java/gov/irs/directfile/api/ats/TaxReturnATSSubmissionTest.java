package gov.irs.directfile.api.ats;

import gov.irs.directfile.api.ats.converter.ATSToFactGraphConverter;
import gov.irs.directfile.api.ats.model.ATSScenarioData;
import gov.irs.directfile.api.taxreturn.models.TaxReturn;
import gov.irs.directfile.api.util.base.BaseIntegrationTest;
import gov.irs.directfile.models.FactTypeWithItem;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Integration tests for TaxReturn creation and submission using ATS scenario data.
 *
 * These tests verify that:
 * 1. ATS scenario data can be used to create TaxReturn entities
 * 2. Facts are properly persisted and retrievable
 * 3. Tax returns can be prepared for submission workflow
 */
@SpringBootTest
@ActiveProfiles("test")
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
public class TaxReturnATSSubmissionTest extends BaseIntegrationTest {
    private ATSToFactGraphConverter converter;

    @BeforeEach
    void setUpConverter() {
        converter = new ATSToFactGraphConverter();
    }

    @DynamicPropertySource
    static void registerDataSourceProperties(DynamicPropertyRegistry registry) {
        String dbUrl = buildTestDbUrl("ats-submission");
        registry.add("spring.datasource.url", () -> dbUrl);
        registry.add("spring.liquibase.url", () -> dbUrl);
        registry.add("spring.datasource.username", () -> "sa");
        registry.add("spring.datasource.password", () -> "");
        registry.add("spring.liquibase.user", () -> "sa");
        registry.add("spring.liquibase.password", () -> "");
    }

    /**
     * Provides standard Form 1040 ATS scenario file names for parameterized tests.
     * Excludes special forms (1040-SS, 1040-NR, 4868) that require different handling.
     */
    static Stream<Arguments> standardScenarioProvider() {
        return Stream.of(
            Arguments.of("scenario-1-tara-black.json", "Scenario 1 - Single"),
            Arguments.of("scenario-2-jones.json", "Scenario 2 - MFJ with deceased spouse"),
            Arguments.of("scenario-3-heather.json", "Scenario 3 - Farm income"),
            Arguments.of("scenario-4-smith.json", "Scenario 4 - Energy credits"),
            Arguments.of("scenario-5-barker.json", "Scenario 5 - HOH with EIC"),
            Arguments.of("scenario-8-lewis.json", "Scenario 8 - MFS with 1099-R"),
            Arguments.of("scenario-12-gardenia.json", "Scenario 12 - Self-employed"),
            Arguments.of("scenario-13-birch.json", "Scenario 13 - MFJ with AMT")
        );
    }

    @Nested
    @DisplayName("TaxReturn Creation Tests")
    class TaxReturnCreationTests {

        @ParameterizedTest(name = "{1}")
        @MethodSource("gov.irs.directfile.api.ats.TaxReturnATSSubmissionTest#standardScenarioProvider")
        @DisplayName("Should create TaxReturn with ATS scenario facts")
        void testTaxReturnCreation(String fileName, String scenarioName) throws IOException {
            // Load and convert scenario
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario(fileName);
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Create TaxReturn
            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            // Verify TaxReturn created
            assertThat(taxReturn).isNotNull();
            assertThat(taxReturn.getId()).isNotNull();
            assertThat(taxReturn.getTaxYear()).isEqualTo(2024); // TestDataFactory default

            // Verify facts persisted
            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();
            assertThat(retrieved.getFacts()).isNotEmpty();
            assertThat(retrieved.getFacts()).containsKey("/filers");
            assertThat(retrieved.getFacts()).containsKey("/filingStatus");
        }

        @Test
        @DisplayName("Should create TaxReturn with W-2 facts")
        void testTaxReturnWithW2Facts() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify W-2 collection present
            assertThat(retrieved.getFacts()).containsKey("/formW2s");

            // Count W-2 wage entries
            long w2WagesCount = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/wages"))
                .count();

            assertThat(w2WagesCount).isEqualTo(2); // Tara has 2 W-2s
        }

        @Test
        @DisplayName("Should create TaxReturn with dependent facts")
        void testTaxReturnWithDependentFacts() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-5-barker.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify dependents collection present
            assertThat(retrieved.getFacts()).containsKey("/familyAndHousehold");

            // Count dependent entries
            long dependentCount = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/familyAndHousehold/#") && k.endsWith("/firstName"))
                .count();

            assertThat(dependentCount).isEqualTo(2); // Bobby has 2 children
        }

        @Test
        @DisplayName("Should create TaxReturn with MFJ spouse facts")
        void testTaxReturnWithSpouseFacts() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-2-jones.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Count filer entries (should be 2 for MFJ)
            long filerCount = retrieved.getFacts().keySet().stream()
                .filter(k -> k.startsWith("/filers/#") && k.endsWith("/isPrimaryFiler"))
                .count();

            assertThat(filerCount).isEqualTo(2);
        }
    }

    @Nested
    @DisplayName("Facts Persistence Tests")
    class FactsPersistenceTests {

        @Test
        @DisplayName("Should persist TIN wrapper correctly")
        void testTinWrapperPersistence() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Find TIN fact
            String tinKey = retrieved.getFacts().keySet().stream()
                .filter(k -> k.endsWith("/tin") && k.contains("/filers/#"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem tinFact = retrieved.getFacts().get(tinKey);
            assertThat(tinFact.type()).isEqualTo("gov.irs.factgraph.persisters.TinWrapper");
            assertThat(tinFact.item().get("area").asText()).isEqualTo("400");
        }

        @Test
        @DisplayName("Should persist dollar wrapper correctly")
        void testDollarWrapperPersistence() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Find wages fact
            String wagesKey = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/wages"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem wagesFact = retrieved.getFacts().get(wagesKey);
            assertThat(wagesFact.type()).isEqualTo("gov.irs.factgraph.persisters.DollarWrapper");
        }

        @Test
        @DisplayName("Should persist enum wrapper correctly")
        void testEnumWrapperPersistence() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-1-tara-black.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            FactTypeWithItem filingStatusFact = retrieved.getFacts().get("/filingStatus");
            assertThat(filingStatusFact.type()).isEqualTo("gov.irs.factgraph.persisters.EnumWrapper");
            assertThat(filingStatusFact.item().get("value").get(0).asText()).isEqualTo("single");
        }
    }

    @Nested
    @DisplayName("Scenario Coverage Tests")
    class ScenarioCoverageTests {

        @Test
        @DisplayName("Should handle scenario with no W-2 forms")
        void testScenarioWithoutW2s() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-3-heather.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Should still create valid facts map
            assertThat(facts).isNotEmpty();
            assertThat(facts).containsKey("/filers");

            // W-2 collection may be absent or empty
            if (facts.containsKey("/formW2s")) {
                long w2Count = facts.keySet().stream()
                    .filter(k -> k.contains("/formW2s/#") && k.endsWith("/wages"))
                    .count();
                assertThat(w2Count).isEqualTo(0);
            }
        }

        @Test
        @DisplayName("Should handle scenario with 1099-R forms")
        void testScenarioWith1099R() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-8-lewis.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify 1099-R collection
            assertThat(retrieved.getFacts()).containsKey("/form1099Rs");

            long form1099RCount = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/form1099Rs/#") && k.endsWith("/writableGrossDistribution"))
                .count();

            assertThat(form1099RCount).isEqualTo(2);
        }

        @Test
        @DisplayName("Should handle high-income MFJ scenario")
        void testHighIncomeMFJScenario() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-13-birch.json");
            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            UUID userExternalId = gov.irs.directfile.api.util.SecurityTestConfiguration.testUserMap
                .get(gov.irs.directfile.api.util.SecurityTestConfiguration.TEST_USER_1).getExternalId();

            TaxReturn taxReturn = testDataFactory.addTaxReturnToUserByUserExternalId(
                userExternalId, facts);

            TaxReturn retrieved = taxReturnRepository.findById(taxReturn.getId()).orElseThrow();

            // Verify both W-2s present (William and Nancy)
            long w2Count = retrieved.getFacts().keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/wages"))
                .count();

            assertThat(w2Count).isEqualTo(2);

            // Verify MFJ filing status
            assertThat(retrieved.getFacts().get("/filingStatus")
                .item().get("value").get(0).asText()).isEqualTo("marriedFilingJointly");
        }
    }

    private static String buildTestDbUrl(String prefix) {
        return "jdbc:h2:mem:" + prefix + "_" + UUID.randomUUID().toString().replace("-", "")
                + ";DB_CLOSE_DELAY=-1;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DEFAULT_NULL_ORDERING=HIGH";
    }
}
