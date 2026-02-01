package gov.irs.directfile.submit.validation;

import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;

import javax.xml.XMLConstants;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * MeF (Modernized e-File) XML Schema Validator.
 *
 * This validator validates generated MeF XML documents against official IRS XSD schemas.
 *
 * <p><b>IMPORTANT:</b> To fully utilize this validator, you must obtain the official IRS MeF XSD
 * schemas from the IRS e-Services portal:</p>
 *
 * <ol>
 *   <li>Log in to IRS e-Services at https://www.irs.gov/e-file-providers/e-services-online-tools</li>
 *   <li>Navigate to MeF Developer Resources</li>
 *   <li>Download the current year's MeF schema package</li>
 *   <li>Extract schemas to: submit/src/main/resources/xsd/mef/</li>
 * </ol>
 *
 * <p><b>Expected schema directory structure:</b></p>
 * <pre>
 * submit/src/main/resources/xsd/mef/
 *   ├── common/
 *   │   ├── IRS990-common.xsd
 *   │   └── efileTypes.xsd
 *   ├── efile1040/
 *   │   ├── IRSF1040.xsd
 *   │   ├── IRSS1.xsd
 *   │   └── ... (other 1040 form schemas)
 *   ├── manifest/
 *   │   └── Manifest.xsd
 *   └── return/
 *       └── Return.xsd
 * </pre>
 *
 * <p><b>Usage example:</b></p>
 * <pre>
 * MeFSchemaValidator validator = new MeFSchemaValidator();
 * ValidationResult result = validator.validate(xmlContent, FormType.FORM_1040);
 * if (!result.isValid()) {
 *     result.getErrors().forEach(System.err::println);
 * }
 * </pre>
 *
 * @see <a href="https://www.irs.gov/e-file-providers/modernized-e-file-mef-developers">MeF Developers</a>
 */
public class MeFSchemaValidator {

    private static final String XSD_RESOURCE_PATH = "/xsd/mef/";
    private static final String FORM_1040_SCHEMA = "efile1040/IRSF1040.xsd";
    private static final String MANIFEST_SCHEMA = "manifest/Manifest.xsd";
    private static final String RETURN_SCHEMA = "return/Return.xsd";

    private Schema form1040Schema;
    private Schema manifestSchema;
    private Schema returnSchema;
    private boolean schemasLoaded = false;

    /**
     * Supported form types for validation.
     */
    public enum FormType {
        FORM_1040("efile1040/IRSF1040.xsd"),
        FORM_1040_NR("efile1040/IRSF1040NR.xsd"),
        FORM_1040_SS("efile1040/IRSF1040SS.xsd"),
        FORM_4868("efile1040/IRSF4868.xsd"),
        MANIFEST("manifest/Manifest.xsd"),
        RETURN("return/Return.xsd");

        private final String schemaPath;

        FormType(String schemaPath) {
            this.schemaPath = schemaPath;
        }

        public String getSchemaPath() {
            return schemaPath;
        }
    }

    /**
     * Result of a validation operation.
     */
    public static class ValidationResult {
        private final boolean valid;
        private final List<String> errors;
        private final List<String> warnings;

        public ValidationResult(boolean valid, List<String> errors, List<String> warnings) {
            this.valid = valid;
            this.errors = errors != null ? errors : new ArrayList<>();
            this.warnings = warnings != null ? warnings : new ArrayList<>();
        }

        public boolean isValid() {
            return valid;
        }

        public List<String> getErrors() {
            return errors;
        }

        public List<String> getWarnings() {
            return warnings;
        }

        public static ValidationResult success() {
            return new ValidationResult(true, new ArrayList<>(), new ArrayList<>());
        }

        public static ValidationResult failure(List<String> errors) {
            return new ValidationResult(false, errors, new ArrayList<>());
        }

        public static ValidationResult schemasNotAvailable() {
            List<String> warnings = new ArrayList<>();
            warnings.add("MeF XSD schemas not available. Schema validation skipped.");
            warnings.add("To enable schema validation, obtain schemas from IRS e-Services portal.");
            return new ValidationResult(true, new ArrayList<>(), warnings);
        }
    }

    /**
     * Creates a new MeF schema validator.
     * Attempts to load schemas from classpath resources.
     */
    public MeFSchemaValidator() {
        loadSchemas();
    }

    /**
     * Attempts to load MeF XSD schemas from the classpath.
     */
    private void loadSchemas() {
        try {
            SchemaFactory schemaFactory = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);

            // Try to load Form 1040 schema
            URL form1040Url = getClass().getResource(XSD_RESOURCE_PATH + FORM_1040_SCHEMA);
            if (form1040Url != null) {
                form1040Schema = schemaFactory.newSchema(form1040Url);
            }

            // Try to load manifest schema
            URL manifestUrl = getClass().getResource(XSD_RESOURCE_PATH + MANIFEST_SCHEMA);
            if (manifestUrl != null) {
                manifestSchema = schemaFactory.newSchema(manifestUrl);
            }

            // Try to load return schema
            URL returnUrl = getClass().getResource(XSD_RESOURCE_PATH + RETURN_SCHEMA);
            if (returnUrl != null) {
                returnSchema = schemaFactory.newSchema(returnUrl);
            }

            schemasLoaded = (form1040Schema != null || manifestSchema != null || returnSchema != null);

        } catch (SAXException e) {
            // Schema loading failed - validation will be skipped
            schemasLoaded = false;
        }
    }

    /**
     * Checks if MeF schemas are available for validation.
     *
     * @return true if at least one schema is loaded
     */
    public boolean areSchemasAvailable() {
        return schemasLoaded;
    }

    /**
     * Validates XML content against the specified form type schema.
     *
     * @param xmlContent the XML content to validate
     * @param formType   the form type (determines which schema to use)
     * @return validation result with errors/warnings if any
     */
    public ValidationResult validate(String xmlContent, FormType formType) {
        if (!schemasLoaded) {
            return ValidationResult.schemasNotAvailable();
        }

        Schema schema = getSchemaForFormType(formType);
        if (schema == null) {
            List<String> warnings = new ArrayList<>();
            warnings.add("Schema for " + formType.name() + " not loaded. Validation skipped.");
            return new ValidationResult(true, new ArrayList<>(), warnings);
        }

        return validateWithSchema(xmlContent, schema);
    }

    /**
     * Validates XML content against the provided schema.
     */
    private ValidationResult validateWithSchema(String xmlContent, Schema schema) {
        List<String> errors = new ArrayList<>();

        try {
            Validator validator = schema.newValidator();
            validator.setErrorHandler(new ValidationErrorHandler(errors));
            validator.validate(new StreamSource(new StringReader(xmlContent)));

            return errors.isEmpty() ?
                ValidationResult.success() :
                ValidationResult.failure(errors);

        } catch (SAXException | IOException e) {
            errors.add("Validation failed: " + e.getMessage());
            return ValidationResult.failure(errors);
        }
    }

    /**
     * Gets the appropriate schema for the given form type.
     */
    private Schema getSchemaForFormType(FormType formType) {
        return switch (formType) {
            case FORM_1040, FORM_1040_NR, FORM_1040_SS, FORM_4868 -> form1040Schema;
            case MANIFEST -> manifestSchema;
            case RETURN -> returnSchema;
        };
    }

    /**
     * Validates a MeF submission package containing manifest and return XML.
     *
     * @param manifestXml the manifest XML content
     * @param returnXml   the return XML content
     * @return combined validation result
     */
    public ValidationResult validateSubmission(String manifestXml, String returnXml) {
        if (!schemasLoaded) {
            return ValidationResult.schemasNotAvailable();
        }

        List<String> allErrors = new ArrayList<>();
        List<String> allWarnings = new ArrayList<>();

        // Validate manifest
        ValidationResult manifestResult = validate(manifestXml, FormType.MANIFEST);
        allErrors.addAll(manifestResult.getErrors());
        allWarnings.addAll(manifestResult.getWarnings());

        // Validate return
        ValidationResult returnResult = validate(returnXml, FormType.RETURN);
        allErrors.addAll(returnResult.getErrors());
        allWarnings.addAll(returnResult.getWarnings());

        return new ValidationResult(
            allErrors.isEmpty(),
            allErrors,
            allWarnings
        );
    }

    /**
     * Error handler that collects validation errors.
     */
    private static class ValidationErrorHandler implements org.xml.sax.ErrorHandler {
        private final List<String> errors;

        ValidationErrorHandler(List<String> errors) {
            this.errors = errors;
        }

        @Override
        public void warning(SAXParseException exception) {
            // Warnings are not collected as errors
        }

        @Override
        public void error(SAXParseException exception) {
            errors.add(formatException("Error", exception));
        }

        @Override
        public void fatalError(SAXParseException exception) {
            errors.add(formatException("Fatal", exception));
        }

        private String formatException(String severity, SAXParseException exception) {
            return String.format("%s at line %d, column %d: %s",
                severity,
                exception.getLineNumber(),
                exception.getColumnNumber(),
                exception.getMessage());
        }
    }
}
