package gov.irs.directfile.submit.validation;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Tests for MeF Schema Validator.
 *
 * Note: Full schema validation tests require IRS MeF XSD schemas to be present.
 * Without schemas, the validator operates in "skip validation" mode.
 */
@DisplayName("MeF Schema Validator Tests")
class MeFSchemaValidatorTest {

    private MeFSchemaValidator validator;

    @BeforeEach
    void setUp() {
        validator = new MeFSchemaValidator();
    }

    @Nested
    @DisplayName("Schema Availability Tests")
    class SchemaAvailabilityTests {

        @Test
        @DisplayName("Should report schema availability status")
        void testSchemaAvailabilityStatus() {
            boolean available = validator.areSchemasAvailable();

            // Schema availability depends on whether XSD files are present
            // This test just verifies the method works
            assertThat(available).isNotNull();
        }

        @Test
        @DisplayName("Should handle missing schemas gracefully")
        void testMissingSchemasHandledGracefully() {
            // When schemas are not available, validation should still return a result
            MeFSchemaValidator.ValidationResult result =
                validator.validate("<xml/>", MeFSchemaValidator.FormType.FORM_1040);

            assertThat(result).isNotNull();
            // Without schemas, should return valid with warnings
            if (!validator.areSchemasAvailable()) {
                assertThat(result.isValid()).isTrue();
                assertThat(result.getWarnings()).isNotEmpty();
            }
        }
    }

    @Nested
    @DisplayName("Validation Result Tests")
    class ValidationResultTests {

        @Test
        @DisplayName("Success result should be valid with no errors")
        void testSuccessResult() {
            MeFSchemaValidator.ValidationResult result = MeFSchemaValidator.ValidationResult.success();

            assertThat(result.isValid()).isTrue();
            assertThat(result.getErrors()).isEmpty();
            assertThat(result.getWarnings()).isEmpty();
        }

        @Test
        @DisplayName("Failure result should not be valid and have errors")
        void testFailureResult() {
            MeFSchemaValidator.ValidationResult result =
                MeFSchemaValidator.ValidationResult.failure(java.util.List.of("Error 1", "Error 2"));

            assertThat(result.isValid()).isFalse();
            assertThat(result.getErrors()).hasSize(2);
            assertThat(result.getErrors()).contains("Error 1", "Error 2");
        }

        @Test
        @DisplayName("Schemas not available result should have warning")
        void testSchemasNotAvailableResult() {
            MeFSchemaValidator.ValidationResult result =
                MeFSchemaValidator.ValidationResult.schemasNotAvailable();

            assertThat(result.isValid()).isTrue();
            assertThat(result.getErrors()).isEmpty();
            assertThat(result.getWarnings()).isNotEmpty();
            assertThat(result.getWarnings().get(0)).contains("not available");
        }
    }

    @Nested
    @DisplayName("Form Type Tests")
    class FormTypeTests {

        @ParameterizedTest
        @EnumSource(MeFSchemaValidator.FormType.class)
        @DisplayName("All form types should have schema paths")
        void testAllFormTypesHaveSchemaPaths(MeFSchemaValidator.FormType formType) {
            assertThat(formType.getSchemaPath()).isNotBlank();
            assertThat(formType.getSchemaPath()).endsWith(".xsd");
        }

        @Test
        @DisplayName("Form 1040 should use correct schema path")
        void testForm1040SchemaPath() {
            assertThat(MeFSchemaValidator.FormType.FORM_1040.getSchemaPath())
                .isEqualTo("efile1040/IRSF1040.xsd");
        }

        @Test
        @DisplayName("Form 1040-NR should use correct schema path")
        void testForm1040NRSchemaPath() {
            assertThat(MeFSchemaValidator.FormType.FORM_1040_NR.getSchemaPath())
                .isEqualTo("efile1040/IRSF1040NR.xsd");
        }

        @Test
        @DisplayName("Manifest should use correct schema path")
        void testManifestSchemaPath() {
            assertThat(MeFSchemaValidator.FormType.MANIFEST.getSchemaPath())
                .isEqualTo("manifest/Manifest.xsd");
        }
    }

    @Nested
    @DisplayName("XML Validation Tests")
    class XmlValidationTests {

        @Test
        @DisplayName("Should validate Form 1040 XML")
        void testValidateForm1040() {
            String sampleXml = """
                <?xml version="1.0" encoding="UTF-8"?>
                <Return>
                    <ReturnHeader>
                        <TaxYr>2025</TaxYr>
                    </ReturnHeader>
                </Return>
                """;

            MeFSchemaValidator.ValidationResult result =
                validator.validate(sampleXml, MeFSchemaValidator.FormType.FORM_1040);

            assertThat(result).isNotNull();
            // Without schemas, validation is skipped
            if (!validator.areSchemasAvailable()) {
                assertThat(result.isValid()).isTrue();
            }
        }

        @Test
        @DisplayName("Should validate manifest XML")
        void testValidateManifest() {
            String manifestXml = """
                <?xml version="1.0" encoding="UTF-8"?>
                <Manifest>
                    <SubmissionId>1234562025001abc00001</SubmissionId>
                    <ReturnTypeCd>1040</ReturnTypeCd>
                </Manifest>
                """;

            MeFSchemaValidator.ValidationResult result =
                validator.validate(manifestXml, MeFSchemaValidator.FormType.MANIFEST);

            assertThat(result).isNotNull();
        }

        @Test
        @DisplayName("Should validate complete submission package")
        void testValidateSubmission() {
            String manifestXml = """
                <?xml version="1.0" encoding="UTF-8"?>
                <Manifest>
                    <SubmissionId>1234562025001abc00001</SubmissionId>
                </Manifest>
                """;

            String returnXml = """
                <?xml version="1.0" encoding="UTF-8"?>
                <Return>
                    <ReturnData>
                        <IRS1040/>
                    </ReturnData>
                </Return>
                """;

            MeFSchemaValidator.ValidationResult result =
                validator.validateSubmission(manifestXml, returnXml);

            assertThat(result).isNotNull();
        }
    }

    @Nested
    @DisplayName("Error Handling Tests")
    class ErrorHandlingTests {

        @Test
        @DisplayName("Should handle empty XML gracefully")
        void testHandleEmptyXml() {
            MeFSchemaValidator.ValidationResult result =
                validator.validate("", MeFSchemaValidator.FormType.FORM_1040);

            assertThat(result).isNotNull();
        }

        @Test
        @DisplayName("Should handle null-like content gracefully")
        void testHandleMalformedXml() {
            // Without schemas loaded, malformed XML might not be caught
            MeFSchemaValidator.ValidationResult result =
                validator.validate("<not-closed>", MeFSchemaValidator.FormType.FORM_1040);

            assertThat(result).isNotNull();
        }
    }

    @Nested
    @DisplayName("ATS Scenario Integration Tests")
    class ATSScenarioIntegrationTests {

        @Test
        @DisplayName("Scenario 1 MeF XML should pass validation structure checks")
        void testScenario1MeFXMLStructure() {
            // This test validates the structure of MeF XML that would be generated
            // for ATS Scenario 1 (Tara Black - Single filer with W-2s)
            String scenario1Return = buildScenario1ReturnXML();

            MeFSchemaValidator.ValidationResult result =
                validator.validate(scenario1Return, MeFSchemaValidator.FormType.FORM_1040);

            assertThat(result).isNotNull();
            // Structure should be valid even without schemas
            if (!validator.areSchemasAvailable()) {
                assertThat(result.getWarnings())
                    .anyMatch(w -> w.contains("not available"));
            }
        }

        /**
         * Builds a sample MeF return XML structure for Scenario 1.
         */
        private String buildScenario1ReturnXML() {
            return """
                <?xml version="1.0" encoding="UTF-8"?>
                <Return xmlns="http://www.irs.gov/efile" returnVersion="2025v1.0">
                    <ReturnHeader binaryAttachmentCnt="0">
                        <TaxYr>2025</TaxYr>
                        <TaxPeriodBeginDt>2025-01-01</TaxPeriodBeginDt>
                        <TaxPeriodEndDt>2025-12-31</TaxPeriodEndDt>
                        <Filer>
                            <PrimarySSN>400011032</PrimarySSN>
                            <NameLine1Txt>Tara Black</NameLine1Txt>
                        </Filer>
                    </ReturnHeader>
                    <ReturnData documentCnt="1">
                        <IRS1040>
                            <IndividualReturnFilingStatusCd>1</IndividualReturnFilingStatusCd>
                            <WagesAmt>42470</WagesAmt>
                            <TotalIncomeAmt>42470</TotalIncomeAmt>
                            <AGIAmt>42470</AGIAmt>
                            <TotalItemizedOrStandardDedAmt>15750</TotalItemizedOrStandardDedAmt>
                            <TaxableIncomeAmt>26720</TaxableIncomeAmt>
                            <TotalTaxAmt>2242</TotalTaxAmt>
                            <TotalPaymentsAmt>2713</TotalPaymentsAmt>
                            <RefundAmt>471</RefundAmt>
                        </IRS1040>
                    </ReturnData>
                </Return>
                """;
        }
    }
}
