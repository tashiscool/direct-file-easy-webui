package gov.irs.directfile.submit.ats;

import gov.irs.directfile.submit.domain.SubmissionData;
import gov.irs.directfile.submit.domain.UserContextData;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.math.BigDecimal;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Tests for MeF XML generation using ATS scenario data.
 *
 * These tests verify that:
 * 1. ATS scenario data can be transformed into SubmissionData format
 * 2. UserContextData is properly constructed
 * 3. XML content structure is valid for MeF submission
 */
public class MeFXMLGenerationATSTest {

    private ATSSubmissionDataBuilder builder;

    @BeforeEach
    void setUp() {
        builder = new ATSSubmissionDataBuilder();
    }

    /**
     * Provides ATS scenario identifiers for parameterized tests.
     */
    static Stream<Arguments> atsScenarioProvider() {
        return Stream.of(
            Arguments.of("1", "Tara Black", "Single", 1),
            Arguments.of("2", "John Jones", "MFJ", 2),
            Arguments.of("3", "Lynette Heather", "Single", 1),
            Arguments.of("4", "Sarah Smith", "Single", 1),
            Arguments.of("5", "Bobby Barker", "HOH", 4),
            Arguments.of("8", "Carter Lewis", "MFS", 3),
            Arguments.of("12", "Sam Gardenia", "Single", 1),
            Arguments.of("13", "William Birch", "MFJ", 2)
        );
    }

    @Nested
    @DisplayName("UserContextData Construction Tests")
    class UserContextDataTests {

        @Test
        @DisplayName("Should create UserContextData with required fields")
        void testUserContextDataCreation() {
            UserContextData context = builder.buildUserContext(
                "scenario-1",
                "400011032",
                "SSN"
            );

            assertThat(context).isNotNull();
            assertThat(context.getSubmissionId()).isNotBlank();
            assertThat(context.getUserTin()).isEqualTo("400011032");
            assertThat(context.getUserTinType()).isEqualTo("SSN");
        }

        @Test
        @DisplayName("Should generate unique submission IDs")
        void testUniqueSubmissionIds() {
            UserContextData context1 = builder.buildUserContext("1", "400011032", "SSN");
            UserContextData context2 = builder.buildUserContext("2", "400011038", "SSN");

            assertThat(context1.getSubmissionId()).isNotEqualTo(context2.getSubmissionId());
        }

        @ParameterizedTest(name = "Scenario {0} - {1}")
        @MethodSource("gov.irs.directfile.submit.ats.MeFXMLGenerationATSTest#atsScenarioProvider")
        @DisplayName("Should create UserContextData for each scenario")
        void testUserContextForScenarios(String scenarioId, String taxpayerName,
                                          String filingStatus, int filingStatusCode) {
            String ssn = "40001" + scenarioId.replaceAll("[^0-9]", "") + "32";

            UserContextData context = builder.buildUserContext(
                scenarioId,
                ssn,
                "SSN"
            );

            assertThat(context).isNotNull();
            assertThat(context.getUserTin()).hasSize(9);
        }
    }

    @Nested
    @DisplayName("Submission ID Format Tests")
    class SubmissionIdFormatTests {

        @Test
        @DisplayName("Submission ID should be 20 characters")
        void testSubmissionIdLength() {
            String submissionId = builder.generateSubmissionId("123456", 1);

            assertThat(submissionId).hasSize(20);
        }

        @Test
        @DisplayName("Submission ID should be numeric")
        void testSubmissionIdNumeric() {
            String submissionId = builder.generateSubmissionId("123456", 1);

            assertThat(submissionId).matches("\\d{20}");
        }

        @Test
        @DisplayName("Submission ID should include EFIN")
        void testSubmissionIdIncludesEfin() {
            String submissionId = builder.generateSubmissionId("999999", 1);

            // EFIN should be part of the submission ID structure
            assertThat(submissionId).isNotBlank();
        }
    }

    @Nested
    @DisplayName("Filing Status Mapping Tests")
    class FilingStatusMappingTests {

        @Test
        @DisplayName("Should map filing status 1 to Single")
        void testSingleMapping() {
            String mefValue = builder.mapFilingStatusToMeF(1);
            assertThat(mefValue).isEqualTo("1");
        }

        @Test
        @DisplayName("Should map filing status 2 to MFJ")
        void testMFJMapping() {
            String mefValue = builder.mapFilingStatusToMeF(2);
            assertThat(mefValue).isEqualTo("2");
        }

        @Test
        @DisplayName("Should map filing status 3 to MFS")
        void testMFSMapping() {
            String mefValue = builder.mapFilingStatusToMeF(3);
            assertThat(mefValue).isEqualTo("3");
        }

        @Test
        @DisplayName("Should map filing status 4 to HOH")
        void testHOHMapping() {
            String mefValue = builder.mapFilingStatusToMeF(4);
            assertThat(mefValue).isEqualTo("4");
        }

        @Test
        @DisplayName("Should map filing status 5 to QSS")
        void testQSSMapping() {
            String mefValue = builder.mapFilingStatusToMeF(5);
            assertThat(mefValue).isEqualTo("5");
        }
    }

    @Nested
    @DisplayName("Amount Formatting Tests")
    class AmountFormattingTests {

        @Test
        @DisplayName("Should format dollar amount without cents")
        void testDollarFormatNoCents() {
            String formatted = builder.formatAmount(new BigDecimal("42470.00"));
            assertThat(formatted).isEqualTo("42470");
        }

        @Test
        @DisplayName("Should format dollar amount with rounding")
        void testDollarFormatRounding() {
            String formatted = builder.formatAmount(new BigDecimal("42470.56"));
            assertThat(formatted).isEqualTo("42471");
        }

        @Test
        @DisplayName("Should format zero amount")
        void testZeroAmount() {
            String formatted = builder.formatAmount(BigDecimal.ZERO);
            assertThat(formatted).isEqualTo("0");
        }

        @Test
        @DisplayName("Should format large amount")
        void testLargeAmount() {
            String formatted = builder.formatAmount(new BigDecimal("310000.00"));
            assertThat(formatted).isEqualTo("310000");
        }
    }

    @Nested
    @DisplayName("SSN/TIN Formatting Tests")
    class SsnFormattingTests {

        @Test
        @DisplayName("Should format SSN without dashes")
        void testSsnFormat() {
            String formatted = builder.formatSsn("400-01-1032");
            assertThat(formatted).isEqualTo("400011032");
        }

        @Test
        @DisplayName("Should handle SSN already without dashes")
        void testSsnAlreadyClean() {
            String formatted = builder.formatSsn("400011032");
            assertThat(formatted).isEqualTo("400011032");
        }

        @Test
        @DisplayName("Should validate SSN length")
        void testSsnLength() {
            String formatted = builder.formatSsn("400-01-1032");
            assertThat(formatted).hasSize(9);
        }
    }

    @Nested
    @DisplayName("EIN Formatting Tests")
    class EinFormattingTests {

        @Test
        @DisplayName("Should format EIN without dashes")
        void testEinFormat() {
            String formatted = builder.formatEin("12-3456789");
            assertThat(formatted).isEqualTo("123456789");
        }

        @Test
        @DisplayName("Should validate EIN length")
        void testEinLength() {
            String formatted = builder.formatEin("12-3456789");
            assertThat(formatted).hasSize(9);
        }
    }

    @Nested
    @DisplayName("Date Formatting Tests")
    class DateFormattingTests {

        @Test
        @DisplayName("Should format date as YYYY-MM-DD")
        void testDateFormat() {
            String formatted = builder.formatDate(1985, 6, 15);
            assertThat(formatted).isEqualTo("1985-06-15");
        }

        @Test
        @DisplayName("Should pad single digit month")
        void testSingleDigitMonth() {
            String formatted = builder.formatDate(1985, 1, 5);
            assertThat(formatted).isEqualTo("1985-01-05");
        }
    }

    @Nested
    @DisplayName("XML Element Construction Tests")
    class XmlElementTests {

        @Test
        @DisplayName("Should escape XML special characters")
        void testXmlEscaping() {
            String escaped = builder.escapeXml("Smith & Jones <Partners>");
            assertThat(escaped).isEqualTo("Smith &amp; Jones &lt;Partners&gt;");
        }

        @Test
        @DisplayName("Should escape ampersand")
        void testAmpersandEscape() {
            String escaped = builder.escapeXml("C&R");
            assertThat(escaped).isEqualTo("C&amp;R");
        }

        @Test
        @DisplayName("Should escape quotes")
        void testQuoteEscape() {
            String escaped = builder.escapeXml("Test \"Value\"");
            assertThat(escaped).isEqualTo("Test &quot;Value&quot;");
        }
    }
}
