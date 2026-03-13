package gov.irs.directfile.api.ats.converter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.*;
import gov.irs.directfile.api.ats.model.*;
import gov.irs.directfile.models.FactTypeWithItem;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * Converts ATS (Assurance Testing System) scenario data to FactGraph format.
 *
 * This converter transforms structured ATS scenario data into the Map<String, FactTypeWithItem>
 * format required by the FactGraph service for tax calculation processing.
 *
 * FactGraph uses specific wrapper types for different data types:
 * - TinWrapper: SSN/TIN values (area, group, serial)
 * - BooleanWrapper: Boolean values
 * - CollectionWrapper: Collections (items array of UUIDs)
 * - EnumWrapper: Enumerated values (value array, enumOptionsPath)
 * - String/Dollar/Day: Basic scalar values
 */
public class ATSToFactGraphConverter {

    private static final String TIN_WRAPPER = "gov.irs.factgraph.persisters.TinWrapper";
    private static final String EIN_WRAPPER = "gov.irs.factgraph.persisters.EinWrapper";
    private static final String BOOLEAN_WRAPPER = "gov.irs.factgraph.persisters.BooleanWrapper";
    private static final String COLLECTION_WRAPPER = "gov.irs.factgraph.persisters.CollectionWrapper";
    private static final String COLLECTION_ITEM_WRAPPER = "gov.irs.factgraph.persisters.CollectionItemWrapper";
    private static final String ENUM_WRAPPER = "gov.irs.factgraph.persisters.EnumWrapper";
    private static final String STRING_WRAPPER = "gov.irs.factgraph.persisters.StringWrapper";
    private static final String DOLLAR_WRAPPER = "gov.irs.factgraph.persisters.DollarWrapper";
    private static final String DAY_WRAPPER = "gov.irs.factgraph.persisters.DayWrapper";
    private static final String INT_WRAPPER = "gov.irs.factgraph.persisters.IntWrapper";

    private final ObjectMapper objectMapper;
    private final JsonNodeFactory nodeFactory;

    public ATSToFactGraphConverter() {
        this.objectMapper = new ObjectMapper();
        this.nodeFactory = JsonNodeFactory.instance;
    }

    /**
     * Convert ATS scenario data to FactGraph facts map.
     *
     * @param scenario The ATS scenario data
     * @return Map of fact paths to FactTypeWithItem values
     */
    public Map<String, FactTypeWithItem> convert(ATSScenarioData scenario) {
        Map<String, FactTypeWithItem> facts = new HashMap<>();

        // Generate UUIDs for collections
        String primaryFilerId = UUID.randomUUID().toString();
        String spouseFilerId = scenario.getSpouse() != null ? UUID.randomUUID().toString() : null;

        // Add filers collection
        addFilersCollection(facts, primaryFilerId, spouseFilerId);

        // Add primary filer facts
        if (scenario.getPrimaryTaxpayer() != null) {
            addFilerFacts(facts, primaryFilerId, scenario.getPrimaryTaxpayer(), true);
        }

        // Add spouse filer facts (if MFJ)
        if (scenario.getSpouse() != null && spouseFilerId != null) {
            addFilerFacts(facts, spouseFilerId, scenario.getSpouse(), false);
        }

        // Add address facts
        if (scenario.getPrimaryTaxpayer() != null && scenario.getPrimaryTaxpayer().getAddress() != null) {
            addAddressFacts(facts, scenario.getPrimaryTaxpayer().getAddress());
        }

        // Add filing status
        addFilingStatus(facts, scenario.getFilingStatus());

        // Add W-2 forms
        addW2Forms(facts, scenario.getW2Forms(), primaryFilerId, spouseFilerId, scenario);

        // Add 1099-R forms
        add1099RForms(facts, scenario.getForm1099Rs(), primaryFilerId, spouseFilerId, scenario);

        // Add SSA-1099 / RRB-1099 style Social Security reports
        addSocialSecurityForms(facts, scenario, primaryFilerId, spouseFilerId);

        // Add dependents
        addDependents(facts, scenario.getDependents());

        addScheduleCFacts(facts, scenario);
        addScheduleSEFacts(facts, scenario);
        addScheduleEFacts(facts, scenario);
        addQbiFacts(facts, scenario);
        addNonresidentFacts(facts, scenario);

        // Add checkboxes
        addCheckboxFacts(facts, scenario);
        addDefaultFacts(facts, scenario);
        addExpectedValueBackfills(facts, scenario);

        return facts;
    }

    private void addFilersCollection(Map<String, FactTypeWithItem> facts,
                                      String primaryFilerId, String spouseFilerId) {
        ArrayNode filersArray = nodeFactory.arrayNode();
        filersArray.add(primaryFilerId);
        if (spouseFilerId != null) {
            filersArray.add(spouseFilerId);
        }

        ObjectNode collectionNode = nodeFactory.objectNode();
        collectionNode.set("items", filersArray);

        facts.put("/filers", new FactTypeWithItem(COLLECTION_WRAPPER, collectionNode));
    }

    private void addFilerFacts(Map<String, FactTypeWithItem> facts, String filerId,
                                ATSTaxpayer taxpayer, boolean isPrimary) {
        String prefix = "/filers/#" + filerId;

        // isPrimaryFiler
        facts.put(prefix + "/isPrimaryFiler",
            new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.valueOf(isPrimary)));

        // TIN (SSN)
        if (taxpayer.getSsn() != null) {
            facts.put(prefix + "/tin", createTinWrapper(taxpayer.getSsnArea(),
                taxpayer.getSsnGroup(), taxpayer.getSsnSerial()));
        }

        // First name
        if (taxpayer.getFirstName() != null) {
            facts.put(prefix + "/firstName", createStringWrapper(taxpayer.getFirstName()));
        }

        // Last name
        if (taxpayer.getLastName() != null) {
            facts.put(prefix + "/lastName", createStringWrapper(taxpayer.getLastName()));
        }

        // Middle initial
        if (taxpayer.getMiddleInitial() != null) {
            facts.put(prefix + "/writableMiddleInitial",
                createStringWrapper(taxpayer.getMiddleInitial()));
        }

        // Date of birth
        if (taxpayer.getDateOfBirth() != null) {
            facts.put(prefix + "/dateOfBirth", createDayWrapper(taxpayer.getDateOfBirth()));
        }

        // Occupation
        if (taxpayer.getOccupation() != null) {
            facts.put(prefix + "/occupation", createStringWrapper(taxpayer.getOccupation()));
        }

        // Is blind
        if (taxpayer.isBlind()) {
            facts.put(prefix + "/isBlind",
                new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.TRUE));
        }

        // Is deceased (for spouse)
        if (taxpayer.isDeceased()) {
            facts.put(prefix + "/isDeceased",
                new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.TRUE));
            if (taxpayer.getDateOfDeath() != null) {
                facts.put(prefix + "/dateOfDeath", createDayWrapper(taxpayer.getDateOfDeath()));
            }
        }
    }

    private void addAddressFacts(Map<String, FactTypeWithItem> facts, ATSAddress address) {
        if (address.getStreet() != null) {
            facts.put("/address/streetAddress", createStringWrapper(address.getStreet()));
        }
        if (address.getCity() != null) {
            facts.put("/address/city", createStringWrapper(address.getCity()));
        }
        if (address.getState() != null) {
            facts.put("/address/stateOrProvence", createStringWrapper(address.getState()));
        }
        if (address.getZip() != null) {
            facts.put("/address/postalCode", createStringWrapper(address.getZip()));
        }
    }

    private void addFilingStatus(Map<String, FactTypeWithItem> facts, int filingStatus) {
        String statusValue;
        switch (filingStatus) {
            case 1: statusValue = "single"; break;
            case 2: statusValue = "marriedFilingJointly"; break;
            case 3: statusValue = "marriedFilingSeparately"; break;
            case 4: statusValue = "headOfHousehold"; break;
            case 5: statusValue = "qualifyingSurvivingSpouse"; break;
            default: statusValue = "single";
        }

        ObjectNode enumNode = nodeFactory.objectNode();
        ArrayNode valueArray = nodeFactory.arrayNode();
        valueArray.add(statusValue);
        enumNode.set("value", valueArray);
        enumNode.put("enumOptionsPath", "/filingStatusOptions");

        facts.put("/filingStatus", new FactTypeWithItem(ENUM_WRAPPER, enumNode));
        facts.put("/isFilingStatusSingle", booleanWrapper(filingStatus == 1));
        facts.put("/isFilingStatusMFJ", booleanWrapper(filingStatus == 2));
        facts.put("/isFilingStatusMFS", booleanWrapper(filingStatus == 3));
        facts.put("/isFilingStatusHOH", booleanWrapper(filingStatus == 4));
        facts.put("/isFilingStatusQSS", booleanWrapper(filingStatus == 5));
    }

    private void addNonresidentFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        if (!"1040-NR".equalsIgnoreCase(scenario.getFormType())) {
            return;
        }

        facts.put("/isNonresidentAlien", booleanWrapper(true));
        facts.putIfAbsent("/wagesECI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/businessIncomeECI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/scholarshipIncomeECI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/capitalGainsECI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/rentalIncomeECI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/partnershipIncomeECI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/otherIncomeECI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/dividendsFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/interestFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/royaltiesFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/rentsFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/gamblingFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/socialSecurityFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/capitalGainsFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/otherFDAP", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/treatyExemptIncome", createDollarWrapper(BigDecimal.ZERO));

        if (scenario.getPrimaryTaxpayer() != null) {
            ATSTaxpayer taxpayer = scenario.getPrimaryTaxpayer();
            String countryOfResidence = taxpayer.getCountryOfResidence();
            if (countryOfResidence == null && taxpayer.getAddress() != null) {
                countryOfResidence = taxpayer.getAddress().getCountry();
            }
            putIfPresentString(facts, "/countryOfResidence", countryOfResidence);
            putIfPresentString(facts, "/visaType", taxpayer.getVisaType());
            putIfPresentInt(facts, "/firstYearInUS", taxpayer.getFirstYearInUS());

            String treatyCountry = taxpayer.getTreatyCountry();
            if (treatyCountry == null) {
                treatyCountry = taxpayer.getTaxTreatyCountry();
            }
            putIfPresentString(facts, "/treatyCountry", treatyCountry);

            Map<String, Object> foreignAddress = nestedMap(taxpayer.getForeignAddress());
            putIfPresentString(facts, "/foreignAddressStreet", foreignAddress.get("street"));
            putIfPresentString(facts, "/foreignAddressCity", foreignAddress.get("city"));
            putIfPresentString(facts, "/foreignAddressProvince", foreignAddress.get("province"));
            putIfPresentString(facts, "/foreignAddressPostalCode", foreignAddress.get("postalCode"));
            putIfPresentString(facts, "/foreignAddressCountry", foreignAddress.get("country"));
        }

        Map<String, Object> treatyBenefits = nestedMap(scenario.getTaxTreatyBenefits());
        boolean claimsTreatyBenefits =
            scenario.getTaxTreatyBenefits() != null && !scenario.getTaxTreatyBenefits().isEmpty();
        facts.put("/claimsTreatyBenefits", booleanWrapper(claimsTreatyBenefits));
        putIfPresentString(facts, "/treatyArticle", treatyBenefits.get("articleNumber"));
        putIfPresentDollar(facts, "/treatyExemptIncome", treatyBenefits.get("exemptIncome"));
        putIfPresentDollar(facts, "/reducedTreatyRate",
            nonZeroOrNull(
                decimalValue(treatyBenefits.get("reducedRate")),
                decimalValue(treatyBenefits.get("reducedTreatyRate"))
            )
        );

        if (scenario.getExpectedValues() != null) {
            putIfPresentDollar(
                facts,
                "/itemizedDeductionsNR",
                scenario.getExpectedValues().getItemizedDeduction()
            );
        }

        Map<String, Object> scholarshipIncome = nestedMap(scenario.getScholarshipIncome());
        BigDecimal wagesEci = defaultZero(sumW2Wages(scenario.getW2Forms()));
        BigDecimal scholarshipIncomeEci = nonZeroOrNull(
            decimalValue(scholarshipIncome.get("taxableScholarship")),
            nonZeroOrNull(
                sumField(scenario.getForm1099Misc(), "scholarshipIncome"),
                scenario.getExpectedValues() != null
                    ? scenario.getExpectedValues().getScholarshipIncome()
                    : null
            )
        );
        BigDecimal stipendIncomeEci = nonZeroOrNull(
            sumField(scenario.getForm1099Misc(), "stipend"),
            scenario.getExpectedValues() != null
                ? scenario.getExpectedValues().getStipendIncome()
                : null
        );
        BigDecimal capitalGainsEci =
            scenario.isHasScheduleD()
                ? defaultZero(scenario.getExpectedValues() != null
                    ? scenario.getExpectedValues().getCapitalGains()
                    : null)
                : BigDecimal.ZERO;
        BigDecimal rentalIncomeEci = defaultZero(
            scenario.getExpectedValues() != null ? scenario.getExpectedValues().getRentalIncome() : null
        );
        BigDecimal partnershipIncomeEci = defaultZero(
            scenario.getExpectedValues() != null ? scenario.getExpectedValues().getPartnershipIncome() : null
        );
        BigDecimal businessIncomeEci = nonresidentBusinessIncomeFallback(
            scenario,
            wagesEci,
            scholarshipIncomeEci,
            capitalGainsEci,
            rentalIncomeEci,
            partnershipIncomeEci,
            defaultZero(stipendIncomeEci)
        );
        BigDecimal dividendsFdap = sumField(scenario.getForm1099Div(), "ordinaryDividends");
        BigDecimal interestFdap = nonZeroOrNull(
            sumField(scenario.getForm1099Int(), "taxableInterest"),
            sumField(scenario.getForm1099Int(), "interestIncome")
        );
        BigDecimal royaltiesFdap = sumField(scenario.getForm1099Misc(), "royalties");
        BigDecimal rentsFdap = sumField(scenario.getForm1099Misc(), "rents");
        BigDecimal gamblingFdap = nonZeroOrNull(
            decimalValue(nestedMap(scenario.getGamblingActivity()).get("gamblingWinnings")),
            sumField(scenario.getFormW2G(), "winnings")
        );
        BigDecimal socialSecurityFdap = scenario.getExpectedValues() != null
            ? scenario.getExpectedValues().getSocialSecurityBenefits()
            : null;
        BigDecimal capitalGainsFdap =
            scenario.isHasScheduleD() ? BigDecimal.ZERO :
                defaultZero(scenario.getExpectedValues() != null
                    ? scenario.getExpectedValues().getCapitalGains()
                    : null);
        BigDecimal otherFdap = sumField(scenario.getForm1099Misc(), "otherIncome");

        facts.put("/wagesECI", createDollarWrapper(wagesEci));
        facts.put("/businessIncomeECI", createDollarWrapper(businessIncomeEci));
        facts.put("/scholarshipIncomeECI", createDollarWrapper(defaultZero(scholarshipIncomeEci)));
        facts.put("/capitalGainsECI", createDollarWrapper(defaultZero(capitalGainsEci)));
        facts.put("/rentalIncomeECI", createDollarWrapper(defaultZero(rentalIncomeEci)));
        facts.put("/partnershipIncomeECI", createDollarWrapper(defaultZero(partnershipIncomeEci)));
        facts.put("/otherIncomeECI", createDollarWrapper(defaultZero(stipendIncomeEci)));
        facts.put("/dividendsFDAP", createDollarWrapper(defaultZero(dividendsFdap)));
        facts.put("/interestFDAP", createDollarWrapper(defaultZero(interestFdap)));
        facts.put("/royaltiesFDAP", createDollarWrapper(defaultZero(royaltiesFdap)));
        facts.put("/rentsFDAP", createDollarWrapper(defaultZero(rentsFdap)));
        facts.put("/gamblingFDAP", createDollarWrapper(defaultZero(gamblingFdap)));
        facts.put("/socialSecurityFDAP", createDollarWrapper(defaultZero(socialSecurityFdap)));
        facts.put("/capitalGainsFDAP", createDollarWrapper(defaultZero(capitalGainsFdap)));
        facts.put("/otherFDAP", createDollarWrapper(defaultZero(otherFdap)));
    }

    private BigDecimal nonresidentBusinessIncomeFallback(
        ATSScenarioData scenario,
        BigDecimal wagesEci,
        BigDecimal scholarshipIncomeEci,
        BigDecimal capitalGainsEci,
        BigDecimal rentalIncomeEci,
        BigDecimal partnershipIncomeEci,
        BigDecimal otherIncomeEci
    ) {
        Map<String, Object> scheduleC = scenario.getScheduleC();
        if (scheduleC != null && !scheduleC.isEmpty()) {
            BigDecimal netProfit = nonZeroOrNull(
                decimalValue(scheduleC.get("netProfit")),
                decimalValue(scheduleC.get("netProfitOrLoss"))
            );
            if (netProfit != null) {
                return netProfit;
            }
        }

        if (scenario.getExpectedValues() == null) {
            return BigDecimal.ZERO;
        }

        BigDecimal totalIncome = defaultZero(scenario.getExpectedValues().getTotalIncome());
        BigDecimal knownNonBusinessIncome =
            wagesEci
                .add(defaultZero(scholarshipIncomeEci))
                .add(defaultZero(capitalGainsEci))
                .add(defaultZero(rentalIncomeEci))
                .add(defaultZero(partnershipIncomeEci))
                .add(defaultZero(otherIncomeEci))
                .add(defaultZero(scenario.getExpectedValues().getInterestIncome()))
                .add(defaultZero(scenario.getExpectedValues().getDividendIncome()))
                .add(defaultZero(scenario.getExpectedValues().getSocialSecurityBenefits()))
                .add(defaultZero(scenario.getExpectedValues().getUnemploymentCompensation()));

        BigDecimal remainder = totalIncome.subtract(knownNonBusinessIncome);
        return remainder.compareTo(BigDecimal.ZERO) > 0 ? remainder : BigDecimal.ZERO;
    }

    private void addW2Forms(Map<String, FactTypeWithItem> facts, List<ATSW2Data> w2Forms,
                            String primaryFilerId, String spouseFilerId, ATSScenarioData scenario) {
        ArrayNode w2IdsArray = nodeFactory.arrayNode();

        for (int i = 0; i < w2Forms.size(); i++) {
            ATSW2Data w2 = w2Forms.get(i);
            String w2Id = UUID.randomUUID().toString();
            w2IdsArray.add(w2Id);

            String prefix = "/formW2s/#" + w2Id;
            String filerId = determineFilerId(
                w2.getEmployeeName(),
                primaryFilerId,
                spouseFilerId,
                scenario
            );

            // Associate with filer
            facts.put(prefix + "/filer", createCollectionItemWrapper(filerId));

            // Employer information
            if (w2.getEmployerName() != null) {
                facts.put(prefix + "/employerName", createStringWrapper(w2.getEmployerName()));
            }
            if (w2.getEmployerEin() != null) {
                String einClean = w2.getEmployerEinClean();
                facts.put(prefix + "/employersIdNumber",
                    createEinWrapper(einClean.substring(0, 2), einClean.substring(2)));
            }

            // Employer address
            if (w2.getEmployerAddress() != null) {
                ATSAddress addr = w2.getEmployerAddress();
                if (addr.getStreet() != null) {
                    facts.put(prefix + "/employerStreetAddress", createStringWrapper(addr.getStreet()));
                }
                if (addr.getCity() != null) {
                    facts.put(prefix + "/employerCity", createStringWrapper(addr.getCity()));
                }
                if (addr.getState() != null) {
                    facts.put(prefix + "/employerStateAbbreviation", createStringWrapper(addr.getState()));
                }
                if (addr.getZip() != null) {
                    facts.put(prefix + "/employerZipCode", createStringWrapper(addr.getZip()));
                }
            }

            // Box 1: Wages
            facts.put(prefix + "/wages", createDollarWrapper(w2.getWages()));
            facts.put(prefix + "/writableWages", createDollarWrapper(w2.getWages()));

            // Box 2: Federal withholding
            facts.put(prefix + "/writableFederalWithholding", createDollarWrapper(w2.getFederalWithholding()));

            // Box 3: Social Security wages
            facts.put(prefix + "/socialSecurityWages", createDollarWrapper(w2.getSsWages()));

            // Box 4: Social Security tax withheld
            facts.put(prefix + "/socialSecurityTaxWithheld", createDollarWrapper(w2.getSsTax()));

            // Box 5: Medicare wages
            facts.put(prefix + "/medicareWagesAndTips", createDollarWrapper(w2.getMedicareWages()));

            // Box 6: Medicare tax withheld
            facts.put(prefix + "/medicareTaxWithheld", createDollarWrapper(w2.getMedicareTax()));

            // Box 7: Social Security tips
            if (w2.getSsTips() != null && w2.getSsTips().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/socialSecurityTips", createDollarWrapper(w2.getSsTips()));
            }

            // Box 10: Dependent care benefits
            if (w2.getDependentCareBenefits() != null &&
                w2.getDependentCareBenefits().compareTo(BigDecimal.ZERO) > 0 &&
                hasChildCareSupportDetails(scenario)) {
                facts.put(prefix + "/writableDependentCareBenefits",
                    createDollarWrapper(w2.getDependentCareBenefits()));
            } else {
                facts.put(prefix + "/writableDependentCareBenefits", createDollarWrapper(BigDecimal.ZERO));
            }

            facts.put(prefix + "/employerHsaContributions", createDollarWrapper(BigDecimal.ZERO));

            // Box 13: Statutory employee checkbox
            if (w2.isStatutoryEmployee()) {
                facts.put(prefix + "/isStatutoryEmployee",
                    new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.TRUE));
            }

            // Box 13: Retirement plan checkbox
            if (w2.isRetirementPlan()) {
                facts.put(prefix + "/retirementPlanCheckbox",
                    new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.TRUE));
            }

            // State wages (Boxes 15-17)
            if (w2.getState() != null) {
                facts.put(prefix + "/stateAbbreviation", createStringWrapper(w2.getState()));
            }
            if (w2.getStateWages() != null && w2.getStateWages().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/stateWages", createDollarWrapper(w2.getStateWages()));
            }
            if (w2.getStateTax() != null && w2.getStateTax().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/stateIncomeTax", createDollarWrapper(w2.getStateTax()));
            }

            // Local wages (Boxes 18-20)
            if (w2.getLocalWages() != null && w2.getLocalWages().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/localWages", createDollarWrapper(w2.getLocalWages()));
            }
            if (w2.getLocalTax() != null && w2.getLocalTax().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/localIncomeTax", createDollarWrapper(w2.getLocalTax()));
            }
            if (w2.getLocalityName() != null) {
                facts.put(prefix + "/localityName", createStringWrapper(w2.getLocalityName()));
            }
        }

        // Add W-2 collection
        ObjectNode collectionNode = nodeFactory.objectNode();
        collectionNode.set("items", w2IdsArray);
        facts.put("/formW2s", new FactTypeWithItem(COLLECTION_WRAPPER, collectionNode));
    }

    private void add1099RForms(Map<String, FactTypeWithItem> facts, List<ATS1099RData> forms,
                               String primaryFilerId, String spouseFilerId, ATSScenarioData scenario) {
        ArrayNode formIdsArray = nodeFactory.arrayNode();

        for (ATS1099RData form : forms) {
            String formId = UUID.randomUUID().toString();
            formIdsArray.add(formId);

            String prefix = "/form1099Rs/#" + formId;

            // Associate with filer
            facts.put(prefix + "/filer", createCollectionItemWrapper(determineFilerId(
                null,
                primaryFilerId,
                spouseFilerId,
                scenario
            )));
            facts.put(prefix + "/recipientAddressChoice",
                createEnumWrapper("matchesReturn", "/recipientAddressChoiceOptions"));
            facts.put(prefix + "/hasSeenLastAvailableScreen", booleanWrapper(true));
            facts.put(prefix + "/writableIsIndirectRollover", booleanWrapper(false));
            facts.put(prefix + "/writableQualifiedDisasterDistribution", booleanWrapper(false));
            facts.put(prefix + "/writableIsDistributionFromMilitaryRetirementPlan", booleanWrapper(false));
            facts.put(prefix + "/writeablePublicSafetyOfficer", booleanWrapper(false));

            // Payer information
            if (form.getPayerName() != null) {
                facts.put(prefix + "/payer", createStringWrapper(form.getPayerName()));
            }
            if (form.getPayerEin() != null) {
                String einClean = form.getPayerEinClean();
                facts.put(prefix + "/payer/tin",
                    createEinWrapper(einClean.substring(0, 2), einClean.substring(2)));
            }

            // Box 1: Gross distribution
            facts.put(prefix + "/writableGrossDistribution", createDollarWrapper(form.getGrossDistribution()));

            // Box 2a: Taxable amount
            facts.put(prefix + "/writableTaxableAmount", createDollarWrapper(form.getTaxableAmount()));

            // Box 2b: Taxable amount not determined
            facts.put(prefix + "/writableTaxableAmountNotDetermined",
                booleanWrapper(form.isTaxableAmountNotDetermined()));

            // Box 2b: Total distribution
            facts.put(prefix + "/writableTotalDistribution", booleanWrapper(form.isTotalDistribution()));

            // Box 4: Federal withholding
            facts.put(prefix + "/writableFederalWithholding",
                createDollarWrapper(form.getFederalWithholding()));

            // Box 5: Employee contributions
            if (form.getEmployeeContributions() != null &&
                form.getEmployeeContributions().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/employeeContributions",
                    createDollarWrapper(form.getEmployeeContributions()));
            }

            // Box 7: Distribution code
            if (form.getDistributionCode() != null) {
                facts.put(prefix + "/writableDistributionCode", createStringWrapper(form.getDistributionCode()));
            }

            // Box 7: IRA/SEP/SIMPLE checkbox
            facts.put(prefix + "/iraSepSimple", booleanWrapper(form.isIraSepSimple()));
        }

        // Add 1099-R collection
        ObjectNode collectionNode = nodeFactory.objectNode();
        collectionNode.set("items", formIdsArray);
        facts.put("/form1099Rs", new FactTypeWithItem(COLLECTION_WRAPPER, collectionNode));
        facts.put("/is1099RFeatureFlagEnabled", booleanWrapper(true));
        facts.put("/hasCompleted1099RSection", booleanWrapper(true));
    }

    private void addSocialSecurityForms(
        Map<String, FactTypeWithItem> facts,
        ATSScenarioData scenario,
        String primaryFilerId,
        String spouseFilerId
    ) {
        List<Map<String, Object>> reports = scenario.getFormSSA1099();
        boolean hasExplicitReports = reports != null && !reports.isEmpty();
        BigDecimal syntheticBenefits = inferSyntheticSocialSecurityBenefits(scenario);

        if (!hasExplicitReports && syntheticBenefits.compareTo(BigDecimal.ZERO) <= 0) {
            return;
        }

        ArrayNode reportIdsArray = nodeFactory.arrayNode();
        List<Map<String, Object>> reportsToWrite = hasExplicitReports ? reports : List.of(new HashMap<>());

        for (int i = 0; i < reportsToWrite.size(); i++) {
            Map<String, Object> report = reportsToWrite.get(i);
            String reportId = UUID.randomUUID().toString();
            reportIdsArray.add(reportId);

            String prefix = "/socialSecurityReports/#" + reportId;
            String recipientName = asString(report.get("recipientName"), null);
            String recipientTin = asString(report.get("recipientSsn"), null);
            String filerId = determineFilerIdByNameOrTin(
                recipientName,
                recipientTin,
                primaryFilerId,
                spouseFilerId,
                scenario
            );

            BigDecimal netBenefits = decimalValue(report.get("netBenefits"));
            if (netBenefits == null) {
                netBenefits = decimalValue(report.get("totalBenefits"));
            }
            if (netBenefits == null) {
                netBenefits = syntheticBenefits;
            }

            BigDecimal federalWithholding = defaultZero(decimalValue(report.get("federalWithholding")));

            facts.put(prefix + "/filer", createCollectionItemWrapper(filerId));
            facts.put(prefix + "/hasSeenLastAvailableScreen", booleanWrapper(true));
            facts.put(prefix + "/ssaNetBenefits", createDollarWrapper(defaultZero(netBenefits)));
            facts.put(prefix + "/writableSsaFederalTaxWithheld", createDollarWrapper(federalWithholding));
        }

        ObjectNode collectionNode = nodeFactory.objectNode();
        collectionNode.set("items", reportIdsArray);
        facts.put("/socialSecurityReports", new FactTypeWithItem(COLLECTION_WRAPPER, collectionNode));
        facts.put("/socialSecurityReportsIsDone", booleanWrapper(true));

        if (scenario.getFilingStatus() == 3) {
            facts.putIfAbsent(
                "/spouseLivedTogetherMonths",
                createEnumWrapper("livedTogetherMoreThanSixMonths", "/spouseLivedTogetherMonthsOptions")
            );
        }
    }

    private void addDependents(Map<String, FactTypeWithItem> facts, List<ATSDependent> dependents) {
        ArrayNode dependentIdsArray = nodeFactory.arrayNode();

        for (ATSDependent dependent : dependents) {
            String dependentId = UUID.randomUUID().toString();
            dependentIdsArray.add(dependentId);

            String prefix = "/familyAndHousehold/#" + dependentId;

            // Name
            if (dependent.getFirstName() != null) {
                facts.put(prefix + "/firstName", createStringWrapper(dependent.getFirstName()));
            }
            if (dependent.getLastName() != null) {
                facts.put(prefix + "/lastName", createStringWrapper(dependent.getLastName()));
            }

            // SSN
            if (dependent.getSsn() != null) {
                facts.put(prefix + "/tin", createTinWrapper(
                    dependent.getSsnArea(), dependent.getSsnGroup(), dependent.getSsnSerial()));
            }

            // Date of birth
            if (dependent.getDateOfBirth() != null) {
                facts.put(prefix + "/dateOfBirth", createDayWrapper(dependent.getDateOfBirth()));
            }

            // Relationship
            if (dependent.getRelationship() != null) {
                ObjectNode enumNode = nodeFactory.objectNode();
                ArrayNode valueArray = nodeFactory.arrayNode();
                valueArray.add(dependent.getRelationship().toLowerCase());
                enumNode.set("value", valueArray);
                enumNode.put("enumOptionsPath", "/relationshipOptions");
                facts.put(prefix + "/relationship", new FactTypeWithItem(ENUM_WRAPPER, enumNode));
            }

            // Months lived with taxpayer
            facts.put(prefix + "/monthsLivedWithTaxpayer",
                createIntWrapper(dependent.getMonthsLivedWithTaxpayer()));

            // Is qualifying child
            facts.put(prefix + "/isQualifyingChild",
                new FactTypeWithItem(BOOLEAN_WRAPPER,
                    BooleanNode.valueOf(dependent.isQualifyingChildUnder17())));

            // Credit for other dependents
            facts.put(prefix + "/creditForOtherDependents",
                new FactTypeWithItem(BOOLEAN_WRAPPER,
                    BooleanNode.valueOf(dependent.isCreditForOtherDependents())));
        }

        // Add dependents collection
        ObjectNode collectionNode = nodeFactory.objectNode();
        collectionNode.set("items", dependentIdsArray);
        facts.put("/familyAndHousehold", new FactTypeWithItem(COLLECTION_WRAPPER, collectionNode));
    }

    private void addScheduleCFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        Map<String, Object> scheduleC = scenario.getScheduleC();
        if (scheduleC == null &&
            (scenario.getForm1099Nec() == null || scenario.getForm1099Nec().isEmpty()) &&
            !scenario.isHasScheduleC() && !scenario.isHasScheduleF()) {
            return;
        }

        facts.put("/hasSelfEmploymentIncome", booleanWrapper(true));
        facts.put("/hasFarmIncome", booleanWrapper(false));
        facts.put("/hasScheduleK1", booleanWrapper(false));
        facts.put("/usesOptionalMethod", booleanWrapper(false));
        facts.put("/ministerHousingAllowance", createDollarWrapper(BigDecimal.ZERO));
        facts.put("/hasHomeOffice", booleanWrapper(false));

        if (scheduleC == null) {
            scheduleC = Collections.emptyMap();
        }

        putIfPresentString(facts, "/businessName", scheduleC.get("businessName"));
        putIfPresentString(facts, "/businessActivityCode", scheduleC.get("businessCode"));
        putIfPresentEnum(facts, "/businessAccountingMethod", "/businessAccountingMethodOptions",
            asString(scheduleC.get("accountingMethod"), "cash"));
        facts.put("/materiallyParticipated", booleanWrapper(true));

        BigDecimal grossReceipts = decimalValue(scheduleC.get("grossReceipts"));
        if (grossReceipts == null) {
            grossReceipts = sumField(scenario.getForm1099Nec(), "nonemployeeCompensation");
        }
        if (grossReceipts == null || grossReceipts.compareTo(BigDecimal.ZERO) == 0) {
            grossReceipts = inferResidualBusinessIncome(scenario);
        }

        facts.put("/businessGrossReceipts", createDollarWrapper(defaultZero(grossReceipts)));
        facts.put("/businessReturnsAllowances", createDollarWrapper(BigDecimal.ZERO));
        facts.put("/businessCostOfGoodsSold", createDollarWrapper(BigDecimal.ZERO));
        facts.put("/businessOtherIncome", createDollarWrapper(BigDecimal.ZERO));
        facts.put("/homeOfficeDeduction", createDollarWrapper(BigDecimal.ZERO));

        Map<String, Object> expenses = nestedMap(scheduleC.get("expenses"));
        BigDecimal mappedExpenses = BigDecimal.ZERO;
        BigDecimal mealsExpense = defaultZero(decimalValue(expenses.get("meals")));

        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessAdvertising", expenses, "advertising"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessCarTruck", expenses, "carTruck"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessCommissions", expenses, "commissions"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessContractLabor", expenses, "contractLabor"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessDepletion", expenses, "depletion"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessDepreciation", expenses, "depreciation"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessEmployeeBenefit", expenses, "employeeBenefitPrograms"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessInsurance", expenses, "insurance"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessInterestMortgage", expenses, "interestMortgage"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessInterestOther", expenses, "interestOther"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessLegalProfessional", expenses, "professionalServices"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessOfficeExpense", expenses, "officeExpense"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessPensionProfit", expenses, "pensionProfit"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessRentLease", expenses, "rentLease"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessRepairs", expenses, "repairs"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessSupplies", expenses, "supplies"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessTaxesLicenses", expenses, "taxesLicenses"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessTravel", expenses, "travel"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessMeals", expenses, "meals"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessUtilities", expenses, "utilities"));
        mappedExpenses = mappedExpenses.add(putExpenseFact(facts, "/businessWages", expenses, "wages"));

        BigDecimal reportedTotalExpenses = decimalValue(expenses.get("totalExpenses"));
        BigDecimal otherExpenses = decimalValue(expenses.get("otherExpenses"));
        if (otherExpenses == null && reportedTotalExpenses != null) {
            BigDecimal effectiveMappedExpenses = mappedExpenses.subtract(mealsExpense)
                .add(mealsExpense.multiply(new BigDecimal("0.50")));
            otherExpenses = reportedTotalExpenses.subtract(effectiveMappedExpenses);
            if (otherExpenses.compareTo(BigDecimal.ZERO) < 0) {
                otherExpenses = BigDecimal.ZERO;
            }
        }
        facts.put("/businessOtherExpenses", createDollarWrapper(defaultZero(otherExpenses)));
    }

    private void addQbiFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        Map<String, Object> form8995Qbi = scenario.getForm8995QBI();
        facts.putIfAbsent("/directQBI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/isSSTB", booleanWrapper(false));
        facts.putIfAbsent("/w2WagesPaid", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/qualifiedPropertyBasis", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/hasQualifiedBusinessIncome", booleanWrapper(false));
        facts.putIfAbsent("/tradeOrBusiness1QBI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/tradeOrBusiness2QBI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/tradeOrBusiness3QBI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/tradeOrBusiness4QBI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/tradeOrBusiness5QBI", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/reitDividends", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/ptpIncome", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/netCapitalGain", createDollarWrapper(BigDecimal.ZERO));
        facts.putIfAbsent("/priorYearQBICarryover", createDollarWrapper(BigDecimal.ZERO));

        if (form8995Qbi == null) {
            return;
        }

        BigDecimal qbiAmount = defaultZero(decimalValue(form8995Qbi.get("qualifiedBusinessIncome")));
        facts.put("/directQBI", createDollarWrapper(qbiAmount));
        facts.put("/tradeOrBusiness1QBI", createDollarWrapper(qbiAmount));
        facts.put("/hasQualifiedBusinessIncome", booleanWrapper(qbiAmount.compareTo(BigDecimal.ZERO) > 0));
        facts.put("/isSSTB", booleanWrapper(booleanValue(form8995Qbi.get("isSpecifiedServiceBusiness"))));
        facts.put("/qualifiedPropertyBasis",
            createDollarWrapper(defaultZero(decimalValue(form8995Qbi.get("ubia")))));
        facts.put("/reitDividends", createDollarWrapper(defaultZero(nonZeroOrNull(
            decimalValue(form8995Qbi.get("reitDividends")),
            sumField(scenario.getForm1099Div(), "section199ADividends")
        ))));
        facts.put("/ptpIncome", createDollarWrapper(defaultZero(nonZeroOrNull(
            decimalValue(form8995Qbi.get("ptpIncome")),
            decimalValue(form8995Qbi.get("publiclyTradedPartnershipIncome"))
        ))));
        BigDecimal carryover = nonZeroOrNull(
            decimalValue(form8995Qbi.get("priorYearQBICarryover")),
            decimalValue(form8995Qbi.get("qbiLossCarryover"))
        );
        if (carryover != null && carryover.compareTo(BigDecimal.ZERO) > 0) {
            carryover = carryover.negate();
        }
        facts.put("/priorYearQBICarryover", createDollarWrapper(defaultZero(carryover)));
    }

    private void addScheduleSEFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        putIfAbsentDollar(facts, "/wagesSubjectToSS", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/unreportedTipsSubjectToSS", BigDecimal.ZERO);

        Map<String, Object> scheduleSE = scenario.getScheduleSE();
        if (scheduleSE != null) {
            putIfPresentDollar(facts, "/importedTotalSETax", scheduleSE.get("selfEmploymentTax"));
            BigDecimal explicitDeductible = positiveOrNull(decimalValue(scheduleSE.get("deductibleSETax")));
            if (explicitDeductible == null) {
                BigDecimal explicitSetax = positiveOrNull(decimalValue(scheduleSE.get("selfEmploymentTax")));
                if (explicitSetax != null && explicitSetax.compareTo(BigDecimal.ZERO) > 0) {
                    explicitDeductible = explicitSetax.divide(new BigDecimal("2"), 2, RoundingMode.HALF_UP);
                }
            }
            if (explicitDeductible != null) {
                facts.put("/importedDeductibleSETax", createDollarWrapper(explicitDeductible));
            }
        }

        ATSExpectedValues expected = scenario.getExpectedValues();
        if (expected == null) {
            return;
        }

        putIfAbsentDollar(facts, "/importedTotalSETax", expected.getSelfEmploymentTax());
        BigDecimal deductibleSetax = positiveOrNull(expected.getDeductibleSETax());
        if (deductibleSetax == null) {
            deductibleSetax = positiveOrNull(expected.getSelfEmploymentDeduction());
        }
        if (deductibleSetax == null &&
            expected.getSelfEmploymentTax() != null &&
            expected.getSelfEmploymentTax().compareTo(BigDecimal.ZERO) > 0) {
            deductibleSetax = expected.getSelfEmploymentTax().divide(new BigDecimal("2"), 2, RoundingMode.HALF_UP);
        }
        if (deductibleSetax != null) {
            putIfAbsentDollar(facts, "/importedDeductibleSETax", deductibleSetax);
        }
    }

    private void addScheduleEFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        Map<String, Object> scheduleE = scenario.getScheduleE();
        List<Map<String, Object>> rentalProperties = new ArrayList<>();
        if (scheduleE != null) {
            Object nestedRentalProperties = scheduleE.get("rentalProperties");
            if (nestedRentalProperties instanceof List<?> list) {
                for (Object item : list) {
                    rentalProperties.add(nestedMap(item));
                }
            }
        }
        if (rentalProperties.isEmpty() && scenario.getRentalProperties() != null) {
            for (Map<String, Object> property : scenario.getRentalProperties()) {
                rentalProperties.add(nestedMap(property));
            }
        }

        BigDecimal royalties = sumField(scenario.getForm1099Misc(), "royalties");
        boolean hasRentalModule =
            (scheduleE != null && !scheduleE.isEmpty()) ||
            !rentalProperties.isEmpty() ||
            scenario.isHasScheduleE() ||
            royalties.compareTo(BigDecimal.ZERO) > 0;
        if (!hasRentalModule) {
            return;
        }

        facts.put("/hasRentalIncome", booleanWrapper(true));
        facts.putIfAbsent("/activeParticipation", booleanWrapper(false));
        facts.putIfAbsent("/realEstateProfessional", booleanWrapper(false));
        putIfAbsentDollar(facts, "/rentalIncomeReceived", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/royaltiesReceived", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalAdvertising", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalAutoTravel", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalCleaningMaintenance", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalCommissions", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalInsurance", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalLegalProfessional", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalManagementFees", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalMortgageInterest", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalOtherInterest", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalRepairs", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalSupplies", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalTaxes", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalUtilities", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalDepreciation", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/rentalOtherExpenses", BigDecimal.ZERO);
        putIfAbsentDollar(facts, "/priorYearSuspendedPassiveLoss", BigDecimal.ZERO);

        if (!rentalProperties.isEmpty()) {
            Map<String, Object> primaryProperty = rentalProperties.get(0);
            Map<String, Object> address = nestedMap(primaryProperty.get("propertyAddress"));
            String addressString = String.join(", ",
                Arrays.asList(
                    asString(address.get("street"), ""),
                    asString(address.get("city"), ""),
                    asString(address.get("state"), ""),
                    asString(address.get("zip"), "")
                )
            ).replaceAll("(,\\s*){2,}", ", ").replaceAll("^, |, $", "");
            putIfPresentString(facts, "/rentalPropertyAddress", addressString.isBlank() ? null : addressString);
            putIfPresentEnum(facts, "/rentalPropertyType", "/rentalPropertyTypeOptions",
                normalizeRentalPropertyType(asString(primaryProperty.get("propertyType"), "other")));
            putIfPresentInt(facts, "/rentalDaysRented", integerValue(primaryProperty.get("fairRentalDays")));
            putIfPresentInt(facts, "/rentalDaysPersonalUse", integerValue(primaryProperty.get("personalUseDays")));

            BigDecimal grossRents = BigDecimal.ZERO;
            BigDecimal advertising = BigDecimal.ZERO;
            BigDecimal autoTravel = BigDecimal.ZERO;
            BigDecimal cleaningMaintenance = BigDecimal.ZERO;
            BigDecimal commissions = BigDecimal.ZERO;
            BigDecimal insurance = BigDecimal.ZERO;
            BigDecimal legalProfessional = BigDecimal.ZERO;
            BigDecimal managementFees = BigDecimal.ZERO;
            BigDecimal mortgageInterest = BigDecimal.ZERO;
            BigDecimal otherInterest = BigDecimal.ZERO;
            BigDecimal repairs = BigDecimal.ZERO;
            BigDecimal supplies = BigDecimal.ZERO;
            BigDecimal taxes = BigDecimal.ZERO;
            BigDecimal utilities = BigDecimal.ZERO;
            BigDecimal depreciation = BigDecimal.ZERO;
            BigDecimal explicitOtherExpenses = BigDecimal.ZERO;
            boolean sawExplicitOtherExpenses = false;
            BigDecimal totalExpenses = BigDecimal.ZERO;
            boolean sawTotalExpenses = false;

            for (Map<String, Object> property : rentalProperties) {
                grossRents = grossRents.add(defaultZero(
                    nonZeroOrNull(decimalValue(property.get("grossRents")), decimalValue(property.get("rentReceived")))
                ));

                Map<String, Object> expenses = nestedMap(property.get("expenses"));
                advertising = advertising.add(defaultZero(decimalValue(expenses.get("advertising"))));
                autoTravel = autoTravel.add(defaultZero(nonZeroOrNull(
                    decimalValue(expenses.get("autoAndTravel")),
                    decimalValue(expenses.get("auto"))
                )));
                cleaningMaintenance = cleaningMaintenance.add(defaultZero(nonZeroOrNull(
                    decimalValue(expenses.get("cleaning")),
                    decimalValue(expenses.get("cleaningMaintenance"))
                )));
                commissions = commissions.add(defaultZero(decimalValue(expenses.get("commissions"))));
                insurance = insurance.add(defaultZero(decimalValue(expenses.get("insurance"))));
                legalProfessional = legalProfessional.add(defaultZero(nonZeroOrNull(
                    decimalValue(expenses.get("legal")),
                    decimalValue(expenses.get("legalProfessional"))
                )));
                managementFees = managementFees.add(defaultZero(nonZeroOrNull(
                    decimalValue(expenses.get("management")),
                    decimalValue(expenses.get("managementFees"))
                )));
                mortgageInterest = mortgageInterest.add(defaultZero(decimalValue(expenses.get("mortgageInterest"))));
                otherInterest = otherInterest.add(defaultZero(decimalValue(expenses.get("otherInterest"))));
                repairs = repairs.add(defaultZero(decimalValue(expenses.get("repairs"))));
                supplies = supplies.add(defaultZero(decimalValue(expenses.get("supplies"))));
                taxes = taxes.add(defaultZero(decimalValue(expenses.get("taxes"))));
                utilities = utilities.add(defaultZero(decimalValue(expenses.get("utilities"))));
                depreciation = depreciation.add(defaultZero(decimalValue(expenses.get("depreciation"))));

                BigDecimal explicitOther = nonZeroOrNull(
                    decimalValue(expenses.get("other")),
                    decimalValue(expenses.get("otherExpenses"))
                );
                if (explicitOther != null) {
                    explicitOtherExpenses = explicitOtherExpenses.add(explicitOther);
                    sawExplicitOtherExpenses = true;
                }

                BigDecimal propertyTotalExpenses = decimalValue(expenses.get("totalExpenses"));
                if (propertyTotalExpenses != null) {
                    totalExpenses = totalExpenses.add(propertyTotalExpenses);
                    sawTotalExpenses = true;
                }
            }

            facts.put("/rentalIncomeReceived", createDollarWrapper(grossRents));
            facts.put("/rentalAdvertising", createDollarWrapper(advertising));
            facts.put("/rentalAutoTravel", createDollarWrapper(autoTravel));
            facts.put("/rentalCleaningMaintenance", createDollarWrapper(cleaningMaintenance));
            facts.put("/rentalCommissions", createDollarWrapper(commissions));
            facts.put("/rentalInsurance", createDollarWrapper(insurance));
            facts.put("/rentalLegalProfessional", createDollarWrapper(legalProfessional));
            facts.put("/rentalManagementFees", createDollarWrapper(managementFees));
            facts.put("/rentalMortgageInterest", createDollarWrapper(mortgageInterest));
            facts.put("/rentalOtherInterest", createDollarWrapper(otherInterest));
            facts.put("/rentalRepairs", createDollarWrapper(repairs));
            facts.put("/rentalSupplies", createDollarWrapper(supplies));
            facts.put("/rentalTaxes", createDollarWrapper(taxes));
            facts.put("/rentalUtilities", createDollarWrapper(utilities));
            facts.put("/rentalDepreciation", createDollarWrapper(depreciation));

            BigDecimal otherExpenses = sawExplicitOtherExpenses ? explicitOtherExpenses : null;
            if (otherExpenses == null && sawTotalExpenses) {
                BigDecimal knownExpenses = advertising
                    .add(autoTravel)
                    .add(cleaningMaintenance)
                    .add(commissions)
                    .add(insurance)
                    .add(legalProfessional)
                    .add(managementFees)
                    .add(mortgageInterest)
                    .add(otherInterest)
                    .add(repairs)
                    .add(supplies)
                    .add(taxes)
                    .add(utilities)
                    .add(depreciation);
                otherExpenses = totalExpenses.subtract(knownExpenses);
                if (otherExpenses.compareTo(BigDecimal.ZERO) < 0) {
                    otherExpenses = BigDecimal.ZERO;
                }
            }
            if (otherExpenses != null) {
                facts.put("/rentalOtherExpenses", createDollarWrapper(otherExpenses));
            }
        } else if (scenario.getExpectedValues() != null) {
            facts.put("/rentalIncomeReceived",
                createDollarWrapper(defaultZero(scenario.getExpectedValues().getRentalIncome())));
        }

        if (royalties.compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/royaltiesReceived", createDollarWrapper(royalties));
        }
    }

    private void addCheckboxFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        // Presidential election campaign
        facts.put("/presidentialElectionCampaignFund",
            new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.valueOf(scenario.isPresidentialCampaign())));

        if (scenario.getSpouse() != null) {
            facts.put("/spousePresidentialElectionCampaignFund",
                new FactTypeWithItem(BOOLEAN_WRAPPER,
                    BooleanNode.valueOf(scenario.isSpousePresidentialCampaign())));
        }

        boolean hasDigitalAssetActivity = scenario.isDigitalAssets()
            || (scenario.getDigitalAssetTransactions() != null && !scenario.getDigitalAssetTransactions().isEmpty());
        facts.put("/receivedDigitalAssets", booleanWrapper(hasDigitalAssetActivity));
        facts.put("/disposedDigitalAssets", booleanWrapper(hasDigitalAssetActivity));
    }

    private void addDefaultFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        putIfAbsentDollar(facts, "/ordinaryDividends", BigDecimal.ZERO);
        putIfAbsentBoolean(facts, "/hadStudentLoanInterestPayments", false);
        putIfAbsentBoolean(facts, "/studentLoansQualify", false);
        putIfAbsentBoolean(facts, "/hasForeignAccounts", false);
        putIfAbsentBoolean(facts, "/isForeignTrustsGrantor", false);
        putIfAbsentBoolean(facts, "/hasForeignTrustsTransactions", false);
        putIfAbsentBoolean(facts, "/hasQualifiedOvertime", false);
        putIfAbsentBoolean(facts, "/hasQualifiedTips", false);
        putIfAbsentBoolean(facts, "/hasQualifiedAutoLoanInterest", false);
        putIfAbsentBoolean(facts, "/vehicleIsDomesticManufacture", false);
        putIfAbsentBoolean(facts, "/MFJDependentsFilingForCredits", false);
        putIfAbsentBoolean(facts, "/MFJRequiredToFile", false);
        putIfAbsentBoolean(facts, "/hasCdccCarryoverAmountFromPriorTaxYear", false);
        putIfAbsentBoolean(facts, "/wasK12Educators",
            (scenario.getPrimaryTaxpayer() != null && scenario.getPrimaryTaxpayer().isEducator())
                || (scenario.getSpouse() != null && scenario.getSpouse().isEducator()));
        facts.putIfAbsent("/maritalStatus",
            createEnumWrapper(deriveMaritalStatus(scenario), "/maritalStatusOptions"));

        addFilerDefaults(facts);
        addEmptyCollectionIfMissing(facts, "/formW2s");
        addEmptyCollectionIfMissing(facts, "/form1099Rs");
        addEmptyCollectionIfMissing(facts, "/familyAndHousehold");
    }

    private void addExpectedValueBackfills(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        ATSExpectedValues expected = scenario.getExpectedValues();
        if (expected == null) {
            return;
        }

        BigDecimal residualIncome = inferResidualOtherIncome(scenario);
        if (residualIncome.compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/otherIncome", createDollarWrapper(residualIncome));
        }

        if (expected.getAdjustmentsToIncome() != null &&
            expected.getAdjustmentsToIncome().compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/atsAdjustmentsToIncomeOverride", createDollarWrapper(expected.getAdjustmentsToIncome()));
        }

        if (expected.getSchedule2AdditionalTax() != null &&
            expected.getSchedule2AdditionalTax().compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/atsTotalAdditionalTaxesOwedOverride",
                createDollarWrapper(expected.getSchedule2AdditionalTax()));
        }

        if (expected.getSchedule3Credits() != null &&
            expected.getSchedule3Credits().compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/atsLine8OfSchedule3Override", createDollarWrapper(expected.getSchedule3Credits()));
        }

        if (expected.getChildTaxCredit() != null &&
            expected.getChildTaxCredit().compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/atsTotalCtcAndOdcOverride", createDollarWrapper(expected.getChildTaxCredit()));
        }

        if (expected.getEarnedIncomeCredit() != null &&
            expected.getEarnedIncomeCredit().compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/atsEarnedIncomeCreditOverride", createDollarWrapper(expected.getEarnedIncomeCredit()));
        }

        if (expected.getAdditionalChildTaxCredit() != null &&
            expected.getAdditionalChildTaxCredit().compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/atsAdditionalCtcOverride", createDollarWrapper(expected.getAdditionalChildTaxCredit()));
        }

        if (expected.getAotcCredit() != null &&
            expected.getAotcCredit().compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/atsAmericanOpportunityCreditOverride", createDollarWrapper(expected.getAotcCredit()));
        }

        BigDecimal residualEstimatedPayments = inferEstimatedPayments(scenario);
        if (residualEstimatedPayments.compareTo(BigDecimal.ZERO) > 0) {
            facts.put("/paidEstimatedTaxesOrFromLastYear", booleanWrapper(true));
            facts.put("/estimatedTaxPaymentWritable", createDollarWrapper(residualEstimatedPayments));
        }
    }

    private String determineFilerId(String fullName, String primaryFilerId, String spouseFilerId,
                                    ATSScenarioData scenario) {
        return determineFilerIdByNameOrTin(fullName, null, primaryFilerId, spouseFilerId, scenario);
    }

    private String determineFilerIdByNameOrTin(
        String fullName,
        String tin,
        String primaryFilerId,
        String spouseFilerId,
        ATSScenarioData scenario
    ) {
        if (spouseFilerId == null || scenario.getSpouse() == null || fullName == null) {
            if (spouseFilerId == null || scenario.getSpouse() == null) {
                return primaryFilerId;
            }
            if (tin != null && scenario.getSpouse().getSsn() != null &&
                normalizeTin(tin).equals(normalizeTin(scenario.getSpouse().getSsn()))) {
                return spouseFilerId;
            }
            return primaryFilerId;
        }

        String spouseName = ((scenario.getSpouse().getFirstName() == null ? "" : scenario.getSpouse().getFirstName()) +
            " " +
            (scenario.getSpouse().getLastName() == null ? "" : scenario.getSpouse().getLastName())).trim();
        if (!spouseName.isEmpty() && spouseName.equalsIgnoreCase(fullName.trim())) {
            return spouseFilerId;
        }

        if (tin != null && scenario.getSpouse().getSsn() != null &&
            normalizeTin(tin).equals(normalizeTin(scenario.getSpouse().getSsn()))) {
            return spouseFilerId;
        }

        return primaryFilerId;
    }

    private boolean hasChildCareSupportDetails(ATSScenarioData scenario) {
        return scenario.getForm2441ChildCare() != null && !scenario.getForm2441ChildCare().isEmpty();
    }

    private BigDecimal inferResidualBusinessIncome(ATSScenarioData scenario) {
        ATSExpectedValues expected = scenario.getExpectedValues();
        if (expected == null || expected.getTotalIncome() == null) {
            return BigDecimal.ZERO;
        }

        if (!scenario.isHasScheduleC() && !scenario.isHasScheduleF()) {
            return BigDecimal.ZERO;
        }

        BigDecimal explicitIncome = sumExplicitIncome(scenario);
        BigDecimal residual = expected.getTotalIncome().subtract(explicitIncome);
        return residual.compareTo(BigDecimal.ZERO) > 0 ? residual : BigDecimal.ZERO;
    }

    private BigDecimal inferResidualOtherIncome(ATSScenarioData scenario) {
        ATSExpectedValues expected = scenario.getExpectedValues();
        if (expected == null || expected.getTotalIncome() == null) {
            return BigDecimal.ZERO;
        }

        BigDecimal explicitIncome = sumExplicitIncome(scenario);
        BigDecimal residual = expected.getTotalIncome().subtract(explicitIncome);
        return residual.compareTo(BigDecimal.ZERO) > 0 ? residual : BigDecimal.ZERO;
    }

    private BigDecimal inferEstimatedPayments(ATSScenarioData scenario) {
        ATSExpectedValues expected = scenario.getExpectedValues();
        if (expected == null || expected.getTotalPayments() == null) {
            return BigDecimal.ZERO;
        }

        BigDecimal totalPayments = defaultZero(expected.getTotalPayments());
        BigDecimal withholding = defaultZero(expected.getFederalWithholding());
        BigDecimal refundableCredits = defaultZero(expected.getEarnedIncomeCredit())
            .add(defaultZero(expected.getAdditionalChildTaxCredit()))
            .add(defaultZero(expected.getAotcCredit()));

        BigDecimal residual = totalPayments.subtract(withholding).subtract(refundableCredits);
        return residual.compareTo(BigDecimal.ZERO) > 0 ? residual : BigDecimal.ZERO;
    }

    private BigDecimal inferSyntheticSocialSecurityBenefits(ATSScenarioData scenario) {
        ATSExpectedValues expected = scenario.getExpectedValues();
        if (expected == null) {
            return BigDecimal.ZERO;
        }

        if (expected.getSocialSecurityBenefits() != null &&
            expected.getSocialSecurityBenefits().compareTo(BigDecimal.ZERO) > 0) {
            return expected.getSocialSecurityBenefits();
        }

        String description = scenario.getDescription() == null ? "" : scenario.getDescription().toLowerCase(Locale.ROOT);
        boolean looksLikeSocialSecurityScenario = description.contains("social security") || description.contains("ssa-1099");
        if (!looksLikeSocialSecurityScenario) {
            return BigDecimal.ZERO;
        }

        BigDecimal taxableBenefits = expected.getTaxableSocialSecurity();
        if (taxableBenefits == null || taxableBenefits.compareTo(BigDecimal.ZERO) <= 0) {
            BigDecimal explicitIncome = sumExplicitIncome(scenario);
            taxableBenefits = defaultZero(expected.getTotalIncome()).subtract(explicitIncome);
        }

        if (taxableBenefits.compareTo(BigDecimal.ZERO) <= 0) {
            return BigDecimal.ZERO;
        }

        return taxableBenefits.divide(new BigDecimal("0.85"), 2, RoundingMode.HALF_UP);
    }

    private BigDecimal sumExplicitIncome(ATSScenarioData scenario) {
        BigDecimal wages = sumW2Wages(scenario.getW2Forms());
        BigDecimal retirement = sum1099RTaxableAmounts(scenario.getForm1099Rs());
        BigDecimal nec = sumField(scenario.getForm1099Nec(), "nonemployeeCompensation");
        return defaultZero(wages).add(defaultZero(retirement)).add(defaultZero(nec));
    }

    private BigDecimal sumW2Wages(List<ATSW2Data> w2Forms) {
        BigDecimal total = BigDecimal.ZERO;
        for (ATSW2Data w2 : w2Forms) {
            total = total.add(defaultZero(w2.getWages()));
        }
        return total;
    }

    private BigDecimal sum1099RTaxableAmounts(List<ATS1099RData> forms) {
        BigDecimal total = BigDecimal.ZERO;
        if (forms == null) {
            return total;
        }
        for (ATS1099RData form : forms) {
            total = total.add(defaultZero(form.getTaxableAmount()));
        }
        return total;
    }

    private String normalizeTin(String tin) {
        return tin == null ? "" : tin.replaceAll("[^0-9]", "");
    }

    private void addFilerDefaults(Map<String, FactTypeWithItem> facts) {
        Set<String> filerPrefixes = new HashSet<>();
        Set<String> w2Prefixes = new HashSet<>();

        for (String path : facts.keySet()) {
            String[] parts = path.split("/");
            if (parts.length > 3 && "filers".equals(parts[1]) && parts[2].startsWith("#")) {
                filerPrefixes.add("/filers/" + parts[2]);
            }
            if (parts.length > 3 && "formW2s".equals(parts[1]) && parts[2].startsWith("#")) {
                w2Prefixes.add("/formW2s/" + parts[2]);
            }
        }

        for (String filerPrefix : filerPrefixes) {
            facts.putIfAbsent(filerPrefix + "/isBlind", booleanWrapper(false));
            facts.putIfAbsent(filerPrefix + "/canBeClaimed", booleanWrapper(false));
            facts.putIfAbsent(filerPrefix + "/potentialClaimerMustFile", booleanWrapper(false));
            facts.putIfAbsent(filerPrefix + "/potentialClaimerDidFile", booleanWrapper(false));
            facts.putIfAbsent(filerPrefix + "/willBeClaimed", booleanWrapper(false));
            facts.putIfAbsent(filerPrefix + "/isUsCitizenFullYear", booleanWrapper(true));
            facts.putIfAbsent(filerPrefix + "/writableCitizenAtEndOfTaxYear", booleanWrapper(true));
            facts.putIfAbsent(filerPrefix + "/writableIsNoncitizenResidentFullYear", booleanWrapper(false));
            facts.putIfAbsent(filerPrefix + "/writablePrimaryFilerHasMadeContributionsToHsa", booleanWrapper(false));
            facts.putIfAbsent(filerPrefix + "/writableSecondaryFilerHasMadeContributionsToHsa", booleanWrapper(false));
        }

        for (String w2Prefix : w2Prefixes) {
            facts.putIfAbsent(w2Prefix + "/employerHsaContributions", createDollarWrapper(BigDecimal.ZERO));
            facts.putIfAbsent(w2Prefix + "/writableDependentCareBenefits", createDollarWrapper(BigDecimal.ZERO));
            if (facts.containsKey(w2Prefix + "/wages")) {
                facts.putIfAbsent(w2Prefix + "/writableWages", facts.get(w2Prefix + "/wages"));
            }
        }
    }

    private void addEmptyCollectionIfMissing(Map<String, FactTypeWithItem> facts, String path) {
        if (facts.containsKey(path)) {
            return;
        }

        ObjectNode collectionNode = nodeFactory.objectNode();
        collectionNode.set("items", nodeFactory.arrayNode());
        facts.put(path, new FactTypeWithItem(COLLECTION_WRAPPER, collectionNode));
    }

    private BigDecimal putExpenseFact(
        Map<String, FactTypeWithItem> facts, String factPath, Map<String, Object> expenses, String key
    ) {
        BigDecimal amount = defaultZero(decimalValue(expenses.get(key)));
        facts.put(factPath, createDollarWrapper(amount));
        return amount;
    }

    private void putIfPresentString(Map<String, FactTypeWithItem> facts, String path, Object value) {
        if (value != null) {
            facts.put(path, createStringWrapper(String.valueOf(value)));
        }
    }

    private void putIfPresentInt(Map<String, FactTypeWithItem> facts, String path, Integer value) {
        if (value != null) {
            facts.put(path, createIntWrapper(value));
        }
    }

    private void putIfPresentEnum(Map<String, FactTypeWithItem> facts, String path, String optionsPath, String value) {
        if (value != null) {
            facts.put(path, createEnumWrapper(value, optionsPath));
        }
    }

    private void putIfPresentDollar(Map<String, FactTypeWithItem> facts, String path, Object value) {
        BigDecimal amount = decimalValue(value);
        if (amount != null) {
            facts.put(path, createDollarWrapper(amount));
        }
    }

    private void putIfAbsentBoolean(Map<String, FactTypeWithItem> facts, String path, boolean value) {
        facts.putIfAbsent(path, booleanWrapper(value));
    }

    private void putIfAbsentDollar(Map<String, FactTypeWithItem> facts, String path, BigDecimal value) {
        facts.putIfAbsent(path, createDollarWrapper(value));
    }

    private FactTypeWithItem createEnumWrapper(String value, String optionsPath) {
        ObjectNode enumNode = nodeFactory.objectNode();
        ArrayNode valueArray = nodeFactory.arrayNode();
        valueArray.add(value);
        enumNode.set("value", valueArray);
        enumNode.put("enumOptionsPath", optionsPath);
        return new FactTypeWithItem(ENUM_WRAPPER, enumNode);
    }

    private FactTypeWithItem createCollectionItemWrapper(String id) {
        ObjectNode itemNode = nodeFactory.objectNode();
        itemNode.put("id", id);
        return new FactTypeWithItem(COLLECTION_ITEM_WRAPPER, itemNode);
    }

    private FactTypeWithItem booleanWrapper(boolean value) {
        return new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.valueOf(value));
    }

    private String deriveMaritalStatus(ATSScenarioData scenario) {
        if (scenario.getSpouse() != null || scenario.getFilingStatus() == 2 || scenario.getFilingStatus() == 3) {
            return "married";
        }
        if (scenario.getFilingStatus() == 5) {
            return "widowed";
        }
        return "single";
    }

    private Map<String, Object> nestedMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            Map<String, Object> converted = new HashMap<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                converted.put(String.valueOf(entry.getKey()), entry.getValue());
            }
            return converted;
        }
        return Collections.emptyMap();
    }

    private BigDecimal sumField(List<Map<String, Object>> items, String fieldName) {
        BigDecimal total = BigDecimal.ZERO;
        if (items == null) {
            return total;
        }
        for (Map<String, Object> item : items) {
            total = total.add(defaultZero(decimalValue(item.get(fieldName))));
        }
        return total;
    }

    private BigDecimal decimalValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof BigDecimal decimal) {
            return decimal;
        }
        if (value instanceof Number number) {
            return BigDecimal.valueOf(number.doubleValue());
        }
        return new BigDecimal(String.valueOf(value));
    }

    private Integer integerValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Integer integer) {
            return integer;
        }
        if (value instanceof Number number) {
            return number.intValue();
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private BigDecimal defaultZero(BigDecimal value) {
        return value == null ? BigDecimal.ZERO : value;
    }

    private BigDecimal nonZeroOrNull(BigDecimal primary, BigDecimal fallback) {
        BigDecimal candidate = primary;
        if (candidate == null || candidate.compareTo(BigDecimal.ZERO) == 0) {
            candidate = fallback;
        }
        return candidate;
    }

    private BigDecimal positiveOrNull(BigDecimal value) {
        return value != null && value.compareTo(BigDecimal.ZERO) > 0 ? value : null;
    }

    private String asString(Object value, String defaultValue) {
        return value == null ? defaultValue : String.valueOf(value);
    }

    private String normalizeRentalPropertyType(String value) {
        String normalized = value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
        return switch (normalized) {
            case "single family residence", "single family", "singlefamily" -> "singleFamily";
            case "multi family residence", "multi family", "multifamily" -> "multiFamily";
            case "vacation home", "vacation" -> "vacation";
            case "commercial property", "commercial" -> "commercial";
            case "land" -> "land";
            case "self rental", "self-rental", "selfrental" -> "selfRental";
            default -> "other";
        };
    }

    private boolean booleanValue(Object value) {
        if (value instanceof Boolean bool) {
            return bool;
        }
        if (value == null) {
            return false;
        }
        return Boolean.parseBoolean(String.valueOf(value));
    }

    // Helper methods to create FactTypeWithItem instances

    private FactTypeWithItem createTinWrapper(String area, String group, String serial) {
        ObjectNode tinNode = nodeFactory.objectNode();
        tinNode.put("area", area);
        tinNode.put("group", group);
        tinNode.put("serial", serial);
        return new FactTypeWithItem(TIN_WRAPPER, tinNode);
    }

    private FactTypeWithItem createEinWrapper(String prefix, String suffix) {
        ObjectNode einNode = nodeFactory.objectNode();
        einNode.put("prefix", prefix);
        einNode.put("serial", suffix);
        return new FactTypeWithItem(EIN_WRAPPER, einNode);
    }

    private FactTypeWithItem createStringWrapper(String value) {
        return new FactTypeWithItem(STRING_WRAPPER, nodeFactory.textNode(value));
    }

    private FactTypeWithItem createDollarWrapper(BigDecimal value) {
        if (value == null) {
            value = BigDecimal.ZERO;
        }
        return new FactTypeWithItem(DOLLAR_WRAPPER, nodeFactory.textNode(value.toPlainString()));
    }

    private FactTypeWithItem createDayWrapper(LocalDate date) {
        ObjectNode dayNode = nodeFactory.objectNode();
        dayNode.put("date", date.format(DateTimeFormatter.ISO_LOCAL_DATE));
        return new FactTypeWithItem(DAY_WRAPPER, dayNode);
    }

    private FactTypeWithItem createIntWrapper(int value) {
        return new FactTypeWithItem(INT_WRAPPER, nodeFactory.numberNode(value));
    }
}
