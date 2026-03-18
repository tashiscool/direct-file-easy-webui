package gov.irs.directfile.api.ats.converter;

import com.fasterxml.jackson.databind.JsonNode;
import gov.irs.directfile.api.ats.ATSScenarioLoader;
import gov.irs.directfile.api.ats.model.*;
import gov.irs.directfile.models.FactTypeWithItem;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.io.IOException;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for ATSToFactGraphConverter.
 */
class ATSToFactGraphConverterTest {

    private ATSToFactGraphConverter converter;

    @BeforeEach
    void setUp() {
        converter = new ATSToFactGraphConverter();
    }

    @Nested
    @DisplayName("Basic Conversion Tests")
    class BasicConversionTests {

        @Test
        @DisplayName("Should convert minimal scenario data")
        void testMinimalScenarioConversion() {
            ATSScenarioData scenario = createMinimalScenario();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts).isNotEmpty();
            assertThat(facts).containsKey("/filers");
            assertThat(facts).containsKey("/filingStatus");
        }

        @Test
        @DisplayName("Should create filers collection with correct wrapper type")
        void testFilersCollectionType() {
            ATSScenarioData scenario = createMinimalScenario();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            FactTypeWithItem filersItem = facts.get("/filers");
            assertThat(filersItem).isNotNull();
            assertThat(filersItem.type()).isEqualTo("gov.irs.factgraph.persisters.CollectionWrapper");
        }

        @Test
        @DisplayName("Should set filing status with correct enum wrapper")
        void testFilingStatusEnumWrapper() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setFilingStatus(1); // Single

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            FactTypeWithItem filingStatusItem = facts.get("/filingStatus");
            assertThat(filingStatusItem).isNotNull();
            assertThat(filingStatusItem.type()).isEqualTo("gov.irs.factgraph.persisters.EnumWrapper");

            JsonNode itemNode = filingStatusItem.item();
            assertThat(itemNode.has("value")).isTrue();
            assertThat(itemNode.get("value").get(0).asText()).isEqualTo("single");
        }
    }

    @Nested
    @DisplayName("Advanced Tax Feature Conversion Tests")
    class AdvancedTaxFeatureConversionTests {

        @Test
        @DisplayName("Should map nonresident scholarship, treaty, and stipend facts")
        void testNonresidentScholarshipAndTreatyConversion() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-nr5-chen.json");

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts.get("/isNonresidentAlien").item().asBoolean()).isTrue();
            assertThat(facts.get("/countryOfCitizenship").item().asText()).isEqualTo("CN");
            assertThat(facts.get("/treatyArticle").item().asText()).isEqualTo("20");
            assertThat(facts.get("/firstYearInUS").item().asInt()).isEqualTo(2022);
            assertThat(facts.get("/daysInUS").item().asInt()).isEqualTo(120);
            assertThat(facts.get("/daysInUSPriorYear").item().asInt()).isEqualTo(118);
            assertThat(facts.get("/daysInUSTwoYearsPrior").item().asInt()).isEqualTo(95);
            assertThat(facts.get("/substantialPresenceWeightedDays").item().asInt()).isEqualTo(174);
            assertThat(facts.get("/foreignAddressCountry").item().asText()).isEqualTo("CN");
            assertThat(facts.get("/scheduleOIHasForeignAddress").item().asBoolean()).isTrue();
            assertThat(new BigDecimal(facts.get("/treatyExemptIncome").item().asText()))
                .isEqualByComparingTo(new BigDecimal("5000.00"));
            assertThat(new BigDecimal(facts.get("/scholarshipIncomeECI").item().asText()))
                .isEqualByComparingTo(new BigDecimal("5000.00"));
            assertThat(new BigDecimal(facts.get("/otherIncomeECI").item().asText()))
                .isEqualByComparingTo(new BigDecimal("24000.00"));
            assertThat(new BigDecimal(facts.get("/businessIncomeECI").item().asText()))
                .isEqualByComparingTo(BigDecimal.ZERO);
        }

        @Test
        @DisplayName("Should map REIT dividends, PTP income, and QBI carryover")
        void testQbiCarryoverAndReitConversion() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setHasForm8995(true);
            scenario.setForm1099Div(List.of(Map.of("section199ADividends", new BigDecimal("1200.00"))));
            scenario.setForm8995QBI(Map.of(
                "qualifiedBusinessIncome", new BigDecimal("40000.00"),
                "reitDividends", new BigDecimal("1500.00"),
                "ptpIncome", new BigDecimal("3000.00"),
                "priorYearQBICarryover", new BigDecimal("2500.00")
            ));

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts.get("/reitDividends").item().asText()).isEqualTo("1500.00");
            assertThat(facts.get("/ptpIncome").item().asText()).isEqualTo("3000.00");
            assertThat(facts.get("/priorYearQBICarryover").item().asText()).isEqualTo("-2500.00");
        }

        @Test
        @DisplayName("Should mark Schedule NEC when FDAP income is present")
        void testNonresidentScheduleNecDetection() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-nr2-desilva.json");
            scenario.setForm1099Div(List.of(Map.of("ordinaryDividends", new BigDecimal("1000.00"))));

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(new BigDecimal(facts.get("/dividendsFDAP").item().asText()))
                .isEqualByComparingTo(new BigDecimal("1000.00"));
        }

        @Test
        @DisplayName("Should map Schedule E rental property facts from ATS scenarios")
        void testScheduleERentalConversion() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-18-thompson-rental.json");

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts.get("/hasRentalIncome").item().asBoolean()).isTrue();
            assertThat(facts.get("/rentalPropertyType").item().get("value").get(0).asText())
                .isEqualTo("singleFamily");
            assertThat(facts.get("/rentalDaysRented").item().asInt()).isEqualTo(365);
            assertThat(new BigDecimal(facts.get("/rentalIncomeReceived").item().asText()))
                .isEqualByComparingTo(new BigDecimal("28800.00"));
            assertThat(new BigDecimal(facts.get("/rentalDepreciation").item().asText()))
                .isEqualByComparingTo(new BigDecimal("7273.00"));
            assertThat(new BigDecimal(facts.get("/rentalOtherExpenses").item().asText()))
                .isEqualByComparingTo(new BigDecimal("500.00"));
        }

        @SuppressWarnings("unchecked")
        @Test
        @DisplayName("Should aggregate multiple rental properties into Schedule E totals")
        void testScheduleEMultiPropertyAggregation() throws IOException {
            ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-18-thompson-rental.json");

            Map<String, Object> scheduleE = scenario.getScheduleE();
            List<Map<String, Object>> rentalProperties =
                new ArrayList<>((List<Map<String, Object>>) scheduleE.get("rentalProperties"));
            Map<String, Object> secondProperty = new java.util.HashMap<>(rentalProperties.get(0));
            Map<String, Object> secondExpenses =
                new java.util.HashMap<>((Map<String, Object>) secondProperty.get("expenses"));

            secondProperty.put("grossRents", new BigDecimal("12000.00"));
            secondExpenses.put("advertising", new BigDecimal("150.00"));
            secondExpenses.put("autoAndTravel", BigDecimal.ZERO);
            secondExpenses.put("cleaning", new BigDecimal("225.00"));
            secondExpenses.put("insurance", new BigDecimal("900.00"));
            secondExpenses.put("management", new BigDecimal("1200.00"));
            secondExpenses.put("mortgageInterest", new BigDecimal("3500.00"));
            secondExpenses.put("repairs", new BigDecimal("600.00"));
            secondExpenses.put("supplies", new BigDecimal("125.00"));
            secondExpenses.put("taxes", new BigDecimal("1500.00"));
            secondExpenses.put("depreciation", new BigDecimal("1800.00"));
            secondExpenses.put("other", new BigDecimal("250.00"));
            secondExpenses.put("totalExpenses", new BigDecimal("10250.00"));
            secondProperty.put("expenses", secondExpenses);
            rentalProperties.add(secondProperty);
            scheduleE.put("rentalProperties", rentalProperties);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(new BigDecimal(facts.get("/rentalIncomeReceived").item().asText()))
                .isEqualByComparingTo(new BigDecimal("40800.00"));
            assertThat(new BigDecimal(facts.get("/rentalManagementFees").item().asText()))
                .isEqualByComparingTo(new BigDecimal("4080.00"));
            assertThat(new BigDecimal(facts.get("/rentalOtherExpenses").item().asText()))
                .isEqualByComparingTo(new BigDecimal("750.00"));
            assertThat(new BigDecimal(facts.get("/rentalDepreciation").item().asText()))
                .isEqualByComparingTo(new BigDecimal("9073.00"));
        }
    }

    @Nested
    @DisplayName("TIN Conversion Tests")
    class TinConversionTests {

        @Test
        @DisplayName("Should convert SSN to TIN wrapper format")
        void testSsnToTinWrapper() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.getPrimaryTaxpayer().setSsn("400-01-1032");

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Find the TIN fact
            String tinKey = facts.keySet().stream()
                .filter(k -> k.endsWith("/tin"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem tinItem = facts.get(tinKey);
            assertThat(tinItem.type()).isEqualTo("gov.irs.factgraph.persisters.TinWrapper");

            JsonNode tinNode = tinItem.item();
            assertThat(tinNode.get("area").asText()).isEqualTo("400");
            assertThat(tinNode.get("group").asText()).isEqualTo("01");
            assertThat(tinNode.get("serial").asText()).isEqualTo("1032");
        }
    }

    @Nested
    @DisplayName("W-2 Conversion Tests")
    class W2ConversionTests {

        @Test
        @DisplayName("Should convert W-2 collection")
        void testW2CollectionConversion() {
            ATSScenarioData scenario = createScenarioWithW2();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts).containsKey("/formW2s");
            FactTypeWithItem w2Collection = facts.get("/formW2s");
            assertThat(w2Collection.type()).isEqualTo("gov.irs.factgraph.persisters.CollectionWrapper");
        }

        @Test
        @DisplayName("Should convert W-2 wages to dollar wrapper")
        void testW2WagesConversion() {
            ATSScenarioData scenario = createScenarioWithW2();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Find wages fact
            String wagesKey = facts.keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/wages"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem wagesItem = facts.get(wagesKey);
            assertThat(wagesItem.type()).isEqualTo("gov.irs.factgraph.persisters.DollarWrapper");
            assertThat(wagesItem.item().asText()).isEqualTo("50000.00");
        }

        @Test
        @DisplayName("Should write W-2 withholding to writable fact path")
        void testW2WithholdingWritableConversion() {
            ATSScenarioData scenario = createScenarioWithW2();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            String withholdingKey = facts.keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/writableFederalWithholding"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem withholdingItem = facts.get(withholdingKey);
            assertThat(withholdingItem.type()).isEqualTo("gov.irs.factgraph.persisters.DollarWrapper");
            assertThat(withholdingItem.item().asText()).isEqualTo("7500.00");
        }

        @Test
        @DisplayName("Should link W-2 filer with collection item wrapper")
        void testW2FilerUsesCollectionItemWrapper() {
            ATSScenarioData scenario = createScenarioWithW2();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            String filerKey = facts.keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/filer"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem filerItem = facts.get(filerKey);
            assertThat(filerItem.type()).isEqualTo("gov.irs.factgraph.persisters.CollectionItemWrapper");
            assertThat(filerItem.item().get("id").asText()).isNotBlank();
        }

        @Test
        @DisplayName("Should convert employer EIN to EIN wrapper")
        void testEmployerEinConversion() {
            ATSScenarioData scenario = createScenarioWithW2();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Find EIN fact
            String einKey = facts.keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/employersIdNumber"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem einItem = facts.get(einKey);
            assertThat(einItem.type()).isEqualTo("gov.irs.factgraph.persisters.EinWrapper");

            JsonNode einNode = einItem.item();
            assertThat(einNode.get("prefix").asText()).isEqualTo("12");
            assertThat(einNode.get("serial").asText()).isEqualTo("3456789");
        }

        @Test
        @DisplayName("Should convert multiple W-2 forms")
        void testMultipleW2Conversion() {
            ATSScenarioData scenario = createScenarioWithMultipleW2s();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            long wagesCount = facts.keySet().stream()
                .filter(k -> k.contains("/formW2s/#") && k.endsWith("/wages"))
                .count();

            assertThat(wagesCount).isEqualTo(2);
        }
    }

    @Nested
    @DisplayName("1099-R Conversion Tests")
    class Form1099RConversionTests {

        @Test
        @DisplayName("Should convert 1099-R collection")
        void test1099RCollectionConversion() {
            ATSScenarioData scenario = createScenarioWith1099R();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts).containsKey("/form1099Rs");
        }

        @Test
        @DisplayName("Should convert 1099-R distribution code")
        void test1099RDistributionCode() {
            ATSScenarioData scenario = createScenarioWith1099R();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            String codeKey = facts.keySet().stream()
                .filter(k -> k.contains("/form1099Rs/#") && k.endsWith("/writableDistributionCode"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem codeItem = facts.get(codeKey);
            assertThat(codeItem.item().asText()).isEqualTo("7");
        }

        @Test
        @DisplayName("Should write 1099-R monetary fields to writable fact paths")
        void test1099RWritableAmounts() {
            ATSScenarioData scenario = createScenarioWith1099R();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            String grossKey = facts.keySet().stream()
                .filter(k -> k.contains("/form1099Rs/#") && k.endsWith("/writableGrossDistribution"))
                .findFirst()
                .orElseThrow();
            String taxableKey = facts.keySet().stream()
                .filter(k -> k.contains("/form1099Rs/#") && k.endsWith("/writableTaxableAmount"))
                .findFirst()
                .orElseThrow();
            String withholdingKey = facts.keySet().stream()
                .filter(k -> k.contains("/form1099Rs/#") && k.endsWith("/writableFederalWithholding"))
                .findFirst()
                .orElseThrow();

            assertThat(facts.get(grossKey).item().asText()).isEqualTo("20000.00");
            assertThat(facts.get(taxableKey).item().asText()).isEqualTo("20000.00");
            assertThat(facts.get(withholdingKey).item().asText()).isEqualTo("2000.00");
        }

        @Test
        @DisplayName("Should link 1099-R filer with collection item wrapper")
        void test1099RFilerUsesCollectionItemWrapper() {
            ATSScenarioData scenario = createScenarioWith1099R();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            String filerKey = facts.keySet().stream()
                .filter(k -> k.contains("/form1099Rs/#") && k.endsWith("/filer"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem filerItem = facts.get(filerKey);
            assertThat(filerItem.type()).isEqualTo("gov.irs.factgraph.persisters.CollectionItemWrapper");
            assertThat(filerItem.item().get("id").asText()).isNotBlank();
        }
    }

    @Nested
    @DisplayName("Fallback Conversion Tests")
    class FallbackConversionTests {

        @Test
        @DisplayName("Should infer deductible SE tax from total SE tax when not explicitly provided")
        void testDeductibleSelfEmploymentTaxFallback() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setHasScheduleC(true);

            ATSExpectedValues expected = new ATSExpectedValues();
            expected.setSelfEmploymentTax(new BigDecimal("13424.00"));
            scenario.setExpectedValues(expected);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            FactTypeWithItem deductible = facts.get("/importedDeductibleSETax");
            assertThat(deductible).isNotNull();
            assertThat(deductible.item().asText()).isEqualTo("6712.00");
        }

        @Test
        @DisplayName("Should synthesize social security report when ATS scenario only provides totals")
        void testSyntheticSocialSecurityFallback() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setFilingStatus(3);
            scenario.setDescription("MFS with SSA-1099 Social Security benefits");

            ATSExpectedValues expected = new ATSExpectedValues();
            expected.setTotalIncome(new BigDecimal("36480.00"));
            expected.setTaxableSocialSecurity(new BigDecimal("12480.00"));
            scenario.setExpectedValues(expected);

            ATS1099RData form1099R = new ATS1099RData();
            form1099R.setPayerName("Pension Fund");
            form1099R.setPayerEin("11-1111111");
            form1099R.setGrossDistribution(new BigDecimal("24000.00"));
            form1099R.setTaxableAmount(new BigDecimal("24000.00"));
            scenario.setForm1099Rs(List.of(form1099R));

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts).containsKey("/socialSecurityReports");
            String reportBenefitsKey = facts.keySet().stream()
                .filter(k -> k.contains("/socialSecurityReports/#") && k.endsWith("/ssaNetBenefits"))
                .findFirst()
                .orElseThrow();

            assertThat(facts.get(reportBenefitsKey).item().asText())
                .isEqualTo("14682.35");
        }

        @Test
        @DisplayName("Should backfill ATS aggregate credit and tax overrides into writable override facts")
        void testAtsAggregateOverrideBackfills() {
            ATSScenarioData scenario = createMinimalScenario();

            ATSExpectedValues expected = new ATSExpectedValues();
            expected.setSchedule2AdditionalTax(new BigDecimal("474.00"));
            expected.setSchedule3Credits(new BigDecimal("1200.00"));
            expected.setChildTaxCredit(new BigDecimal("2000.00"));
            expected.setEarnedIncomeCredit(new BigDecimal("650.00"));
            expected.setAdditionalChildTaxCredit(new BigDecimal("300.00"));
            expected.setAotcCredit(new BigDecimal("500.00"));
            expected.setAdjustmentsToIncome(new BigDecimal("1200.00"));
            scenario.setExpectedValues(expected);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts.get("/atsAdjustmentsToIncomeOverride").item().asText()).isEqualTo("1200.00");
            assertThat(facts.get("/atsTotalAdditionalTaxesOwedOverride").item().asText()).isEqualTo("474.00");
            assertThat(facts.get("/atsLine8OfSchedule3Override").item().asText()).isEqualTo("1200.00");
            assertThat(facts.get("/atsTotalCtcAndOdcOverride").item().asText()).isEqualTo("2000.00");
            assertThat(facts.get("/atsEarnedIncomeCreditOverride").item().asText()).isEqualTo("650.00");
            assertThat(facts.get("/atsAdditionalCtcOverride").item().asText()).isEqualTo("300.00");
            assertThat(facts.get("/atsAmericanOpportunityCreditOverride").item().asText()).isEqualTo("500.00");
        }
    }

    @Nested
    @DisplayName("Dependent Conversion Tests")
    class DependentConversionTests {

        @Test
        @DisplayName("Should convert dependents collection")
        void testDependentsCollectionConversion() {
            ATSScenarioData scenario = createScenarioWithDependents();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts).containsKey("/familyAndHousehold");
        }

        @Test
        @DisplayName("Should convert dependent qualifying child flag")
        void testDependentQualifyingChildFlag() {
            ATSScenarioData scenario = createScenarioWithDependents();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            String flagKey = facts.keySet().stream()
                .filter(k -> k.contains("/familyAndHousehold/#") && k.endsWith("/isQualifyingChild"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem flagItem = facts.get(flagKey);
            assertThat(flagItem.type()).isEqualTo("gov.irs.factgraph.persisters.BooleanWrapper");
            assertThat(flagItem.item().asBoolean()).isTrue();
        }
    }

    @Nested
    @DisplayName("Day Conversion Tests")
    class DayConversionTests {

        @Test
        @DisplayName("Should convert filer date of birth to day wrapper object format")
        void testDateOfBirthDayWrapper() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.getPrimaryTaxpayer().setDateOfBirth(LocalDate.of(1984, 1, 26));

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            String dobKey = facts.keySet().stream()
                .filter(k -> k.endsWith("/dateOfBirth"))
                .findFirst()
                .orElseThrow();

            FactTypeWithItem dobItem = facts.get(dobKey);
            assertThat(dobItem.type()).isEqualTo("gov.irs.factgraph.persisters.DayWrapper");
            assertThat(dobItem.item().get("date").asText()).isEqualTo("1984-01-26");
        }
    }

    @Nested
    @DisplayName("Address Conversion Tests")
    class AddressConversionTests {

        @Test
        @DisplayName("Should convert address components")
        void testAddressConversion() {
            ATSScenarioData scenario = createMinimalScenario();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertThat(facts).containsKey("/address/streetAddress");
            assertThat(facts).containsKey("/address/city");
            assertThat(facts).containsKey("/address/stateOrProvence");
            assertThat(facts).containsKey("/address/postalCode");

            assertThat(facts.get("/address/city").item().asText()).isEqualTo("Cincinnati");
            assertThat(facts.get("/address/stateOrProvence").item().asText()).isEqualTo("OH");
        }
    }

    @Nested
    @DisplayName("MFJ Spouse Conversion Tests")
    class MFJSpouseConversionTests {

        @Test
        @DisplayName("Should convert spouse data for MFJ filing")
        void testSpouseConversion() {
            ATSScenarioData scenario = createMFJScenario();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Should have 2 filers
            long filerCount = facts.keySet().stream()
                .filter(k -> k.startsWith("/filers/#") && k.endsWith("/isPrimaryFiler"))
                .count();

            assertThat(filerCount).isEqualTo(2);
        }

        @Test
        @DisplayName("Should mark spouse as non-primary filer")
        void testSpouseNonPrimaryFlag() {
            ATSScenarioData scenario = createMFJScenario();

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            // Find non-primary filer (spouse)
            boolean hasNonPrimaryFiler = facts.entrySet().stream()
                .filter(e -> e.getKey().endsWith("/isPrimaryFiler"))
                .anyMatch(e -> !e.getValue().item().asBoolean());

            assertThat(hasNonPrimaryFiler).isTrue();
        }
    }

    @Nested
    @DisplayName("Filing Status Mapping Tests")
    class FilingStatusMappingTests {

        @Test
        @DisplayName("Should map filing status 1 to 'single'")
        void testFilingStatus1() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setFilingStatus(1);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertFilingStatusValue(facts, "single");
        }

        @Test
        @DisplayName("Should map filing status 2 to 'marriedFilingJointly'")
        void testFilingStatus2() {
            ATSScenarioData scenario = createMFJScenario();
            scenario.setFilingStatus(2);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertFilingStatusValue(facts, "marriedFilingJointly");
        }

        @Test
        @DisplayName("Should map filing status 3 to 'marriedFilingSeparately'")
        void testFilingStatus3() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setFilingStatus(3);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertFilingStatusValue(facts, "marriedFilingSeparately");
        }

        @Test
        @DisplayName("Should map filing status 4 to 'headOfHousehold'")
        void testFilingStatus4() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setFilingStatus(4);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertFilingStatusValue(facts, "headOfHousehold");
        }

        @Test
        @DisplayName("Should map filing status 5 to 'qualifyingSurvivingSpouse'")
        void testFilingStatus5() {
            ATSScenarioData scenario = createMinimalScenario();
            scenario.setFilingStatus(5);

            Map<String, FactTypeWithItem> facts = converter.convert(scenario);

            assertFilingStatusValue(facts, "qualifyingSurvivingSpouse");
        }

        private void assertFilingStatusValue(Map<String, FactTypeWithItem> facts, String expected) {
            JsonNode valueNode = facts.get("/filingStatus").item().get("value");
            assertThat(valueNode.get(0).asText()).isEqualTo(expected);
        }
    }

    // Helper methods to create test data

    private ATSScenarioData createMinimalScenario() {
        ATSScenarioData scenario = new ATSScenarioData();
        scenario.setScenarioId("test-1");
        scenario.setFilingStatus(1);
        scenario.setTaxYear(2025);

        ATSTaxpayer taxpayer = new ATSTaxpayer();
        taxpayer.setFirstName("Test");
        taxpayer.setLastName("User");
        taxpayer.setSsn("400-01-1234");
        taxpayer.setDateOfBirth(LocalDate.of(1985, 1, 1));

        ATSAddress address = new ATSAddress();
        address.setStreet("123 Test St");
        address.setCity("Cincinnati");
        address.setState("OH");
        address.setZip("45223");
        taxpayer.setAddress(address);

        scenario.setPrimaryTaxpayer(taxpayer);
        return scenario;
    }

    private ATSScenarioData createScenarioWithW2() {
        ATSScenarioData scenario = createMinimalScenario();

        ATSW2Data w2 = new ATSW2Data();
        w2.setEmployeeName("Test User");
        w2.setEmployerName("Test Corp");
        w2.setEmployerEin("12-3456789");
        w2.setWages(new BigDecimal("50000.00"));
        w2.setFederalWithholding(new BigDecimal("7500.00"));
        w2.setSsWages(new BigDecimal("50000.00"));
        w2.setSsTax(new BigDecimal("3100.00"));
        w2.setMedicareWages(new BigDecimal("50000.00"));
        w2.setMedicareTax(new BigDecimal("725.00"));

        scenario.setW2Forms(new ArrayList<>(List.of(w2)));
        return scenario;
    }

    private ATSScenarioData createScenarioWithMultipleW2s() {
        ATSScenarioData scenario = createScenarioWithW2();

        ATSW2Data w2_2 = new ATSW2Data();
        w2_2.setEmployeeName("Test User");
        w2_2.setEmployerName("Second Corp");
        w2_2.setEmployerEin("98-7654321");
        w2_2.setWages(new BigDecimal("30000.00"));
        w2_2.setFederalWithholding(new BigDecimal("4500.00"));
        w2_2.setSsWages(new BigDecimal("30000.00"));
        w2_2.setSsTax(new BigDecimal("1860.00"));
        w2_2.setMedicareWages(new BigDecimal("30000.00"));
        w2_2.setMedicareTax(new BigDecimal("435.00"));

        scenario.getW2Forms().add(w2_2);
        return scenario;
    }

    private ATSScenarioData createScenarioWith1099R() {
        ATSScenarioData scenario = createMinimalScenario();

        ATS1099RData form1099R = new ATS1099RData();
        form1099R.setPayerName("Pension Fund");
        form1099R.setPayerEin("11-1111111");
        form1099R.setGrossDistribution(new BigDecimal("20000.00"));
        form1099R.setTaxableAmount(new BigDecimal("20000.00"));
        form1099R.setFederalWithholding(new BigDecimal("2000.00"));
        form1099R.setDistributionCode("7");

        scenario.setForm1099Rs(List.of(form1099R));
        return scenario;
    }

    private ATSScenarioData createScenarioWithDependents() {
        ATSScenarioData scenario = createMinimalScenario();
        scenario.setFilingStatus(4); // HOH

        ATSDependent dependent = new ATSDependent();
        dependent.setFirstName("Child");
        dependent.setLastName("User");
        dependent.setSsn("400-01-5678");
        dependent.setDateOfBirth(LocalDate.of(2015, 6, 15));
        dependent.setRelationship("Son");
        dependent.setQualifyingChildUnder17(true);

        scenario.setDependents(List.of(dependent));
        return scenario;
    }

    private ATSScenarioData createMFJScenario() {
        ATSScenarioData scenario = createMinimalScenario();
        scenario.setFilingStatus(2);

        ATSTaxpayer spouse = new ATSTaxpayer();
        spouse.setFirstName("Spouse");
        spouse.setLastName("User");
        spouse.setSsn("400-01-9876");
        spouse.setDateOfBirth(LocalDate.of(1987, 3, 15));
        spouse.setPrimaryFiler(false);

        scenario.setSpouse(spouse);
        return scenario;
    }
}
