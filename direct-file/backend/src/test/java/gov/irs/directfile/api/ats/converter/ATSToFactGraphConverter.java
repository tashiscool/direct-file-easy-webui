package gov.irs.directfile.api.ats.converter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.*;
import gov.irs.directfile.api.ats.model.*;
import gov.irs.directfile.models.FactTypeWithItem;

import java.math.BigDecimal;
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
        if (!scenario.getW2Forms().isEmpty()) {
            addW2Forms(facts, scenario.getW2Forms(), primaryFilerId, spouseFilerId);
        }

        // Add 1099-R forms
        if (!scenario.getForm1099Rs().isEmpty()) {
            add1099RForms(facts, scenario.getForm1099Rs(), primaryFilerId);
        }

        // Add dependents
        if (!scenario.getDependents().isEmpty()) {
            addDependents(facts, scenario.getDependents());
        }

        // Add checkboxes
        addCheckboxFacts(facts, scenario);

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
    }

    private void addW2Forms(Map<String, FactTypeWithItem> facts, List<ATSW2Data> w2Forms,
                            String primaryFilerId, String spouseFilerId) {
        ArrayNode w2IdsArray = nodeFactory.arrayNode();

        for (int i = 0; i < w2Forms.size(); i++) {
            ATSW2Data w2 = w2Forms.get(i);
            String w2Id = UUID.randomUUID().toString();
            w2IdsArray.add(w2Id);

            String prefix = "/formW2s/#" + w2Id;

            // Associate with filer (default to primary)
            facts.put(prefix + "/fpiIdentifier", createStringWrapper(primaryFilerId));

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

            // Box 2: Federal withholding
            facts.put(prefix + "/federalIncomeTaxWithheld", createDollarWrapper(w2.getFederalWithholding()));

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
                w2.getDependentCareBenefits().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/dependentCareBenefits", createDollarWrapper(w2.getDependentCareBenefits()));
            }

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
                                String primaryFilerId) {
        ArrayNode formIdsArray = nodeFactory.arrayNode();

        for (ATS1099RData form : forms) {
            String formId = UUID.randomUUID().toString();
            formIdsArray.add(formId);

            String prefix = "/form1099Rs/#" + formId;

            // Associate with filer
            facts.put(prefix + "/fpiIdentifier", createStringWrapper(primaryFilerId));

            // Payer information
            if (form.getPayerName() != null) {
                facts.put(prefix + "/payerName", createStringWrapper(form.getPayerName()));
            }
            if (form.getPayerEin() != null) {
                String einClean = form.getPayerEinClean();
                facts.put(prefix + "/payerTin",
                    createEinWrapper(einClean.substring(0, 2), einClean.substring(2)));
            }

            // Box 1: Gross distribution
            facts.put(prefix + "/grossDistribution", createDollarWrapper(form.getGrossDistribution()));

            // Box 2a: Taxable amount
            facts.put(prefix + "/taxableAmount", createDollarWrapper(form.getTaxableAmount()));

            // Box 2b: Taxable amount not determined
            if (form.isTaxableAmountNotDetermined()) {
                facts.put(prefix + "/taxableAmountNotDetermined",
                    new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.TRUE));
            }

            // Box 2b: Total distribution
            if (form.isTotalDistribution()) {
                facts.put(prefix + "/totalDistribution",
                    new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.TRUE));
            }

            // Box 4: Federal withholding
            facts.put(prefix + "/federalIncomeTaxWithheld",
                createDollarWrapper(form.getFederalWithholding()));

            // Box 5: Employee contributions
            if (form.getEmployeeContributions() != null &&
                form.getEmployeeContributions().compareTo(BigDecimal.ZERO) > 0) {
                facts.put(prefix + "/employeeContributions",
                    createDollarWrapper(form.getEmployeeContributions()));
            }

            // Box 7: Distribution code
            if (form.getDistributionCode() != null) {
                facts.put(prefix + "/distributionCode", createStringWrapper(form.getDistributionCode()));
            }

            // Box 7: IRA/SEP/SIMPLE checkbox
            if (form.isIraSepSimple()) {
                facts.put(prefix + "/iraSepSimple",
                    new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.TRUE));
            }
        }

        // Add 1099-R collection
        ObjectNode collectionNode = nodeFactory.objectNode();
        collectionNode.set("items", formIdsArray);
        facts.put("/form1099Rs", new FactTypeWithItem(COLLECTION_WRAPPER, collectionNode));
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

    private void addCheckboxFacts(Map<String, FactTypeWithItem> facts, ATSScenarioData scenario) {
        // Presidential election campaign
        facts.put("/presidentialElectionCampaignFund",
            new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.valueOf(scenario.isPresidentialCampaign())));

        if (scenario.getSpouse() != null) {
            facts.put("/spousePresidentialElectionCampaignFund",
                new FactTypeWithItem(BOOLEAN_WRAPPER,
                    BooleanNode.valueOf(scenario.isSpousePresidentialCampaign())));
        }

        // Digital assets question
        facts.put("/digitalAssets",
            new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.valueOf(scenario.isDigitalAssets())));
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
        einNode.put("suffix", suffix);
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
        String isoDate = date.format(DateTimeFormatter.ISO_LOCAL_DATE);
        return new FactTypeWithItem(DAY_WRAPPER, nodeFactory.textNode(isoDate));
    }

    private FactTypeWithItem createIntWrapper(int value) {
        return new FactTypeWithItem(INT_WRAPPER, nodeFactory.numberNode(value));
    }
}
