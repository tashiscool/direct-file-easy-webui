package gov.irs.directfile.api.loaders.processor;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import org.springframework.core.io.Resource;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NamedNodeMap;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import gov.irs.directfile.api.loaders.domain.ExportNode;
import gov.irs.directfile.api.loaders.domain.TaxCompNode;
import gov.irs.directfile.api.loaders.domain.TaxDictionaryDigest;
import gov.irs.directfile.api.loaders.domain.TaxFact;
import gov.irs.directfile.api.loaders.domain.TaxLimit;
import gov.irs.directfile.api.loaders.domain.TaxLimitLevel;
import gov.irs.directfile.api.loaders.domain.TaxWritable;
import gov.irs.directfile.api.loaders.errors.XmlProcessorException;

@SuppressFBWarnings(
        value = {"DCN_NULLPOINTER_EXCEPTION"},
        justification = "Initial Spotbugs setup")
public class XmlProcessor {
    private static final String FACT_NAME_CHILD_NAME = "Name";
    private static final String FACT_DESCRIPTION_CHILD_NAME = "Description";
    private static final String FACT_EXPORT_ZERO = "ExportZero";
    private static final String FACT_WRITABLE_CHILD_NAME = "Writable";
    private static final String FACT_DERIVED_CHILD_NAME = "Derived";
    private static final String FACT_PLACEHOLDER_CHILD_NAME = "Placeholder";
    private static final String LIMIT_ELEMENT_NAME = "Limit";
    private static final String LIMIT_TYPE_ATTRIBUTE_NAME = "type";
    private static final String LIMIT_LEVEL_ATTRIBUTE_NAME = "level";
    private static final String TEXT_NODE_VALUE_NAME = "value";
    private static final String INLINE_ENUM_VALUES_OPTION_NAME = "values";
    private static final String COLLECTION_ATTRIBUTE_NAME = "collection";
    private static final String BLOCK_SUBMISSION_ON_TRUE_ELEMENT_NAME = "BlockSubmissionOnTrue";
    private static final String FACT_EXPORT_CHILD_NAME = "Export";

    /**
     * Reads an XML-formatted tax year fact graph configuration file This is known to contain a
     * "FactDictionaryModule" with element "Facts".
     *
     * <p>This reads the configuration into an intermediate set of java classes where the
     * configuration can be stored for easy serialization to the frontend.
     *
     * @param in InputStream
     * @return TaxYearDigest
     */
    @SuppressWarnings(value = {"PMD.CloseResource"}) // suppress this warning for inputStream
    public TaxDictionaryDigest process(final String folderName, final Resource[] xmlFactDictionaryModules) {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        try {
            dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            dbf.setXIncludeAware(false);

            Map<String, TaxFact> factMap = new HashMap<>();
            for (Resource factDictionaryModuleXml : xmlFactDictionaryModules) {
                DocumentBuilder db = dbf.newDocumentBuilder();
                InputStream in = factDictionaryModuleXml.getInputStream();
                Document doc = db.parse(in);
                in.close();
                // facts
                XPath xPath = XPathFactory.newInstance().newXPath();

                NodeList factNodes =
                        (NodeList) xPath.evaluate("/FactDictionaryModule/Facts/Fact", doc, XPathConstants.NODESET);

                for (int i = 0; i < factNodes.getLength(); i++) {
                    TaxFact taxFact = readFact(factNodes.item(i));
                    List<TaxFact> expandedFacts = expandFactWithInlineEnumOptions(taxFact);
                    for (TaxFact expandedFact : expandedFacts) {
                        factMap.put(expandedFact.path(), expandedFact);
                    }
                }
            }
            return new TaxDictionaryDigest(folderName, factMap);
        } catch (IOException e) {
            throw new XmlProcessorException("Could not read xml input file", e);
        } catch (ParserConfigurationException e) {
            throw new XmlProcessorException("Parser configuration failed", e);
        } catch (SAXException | IllegalArgumentException e) {
            throw new XmlProcessorException("Failed to parse XML tax configuration", e);
        } catch (XPathExpressionException e) {
            throw new XmlProcessorException("Invalid xpath", e);
        }
    }

    private TaxFact readFact(Node node) {
        Map<String, String> attributeMap = convertAttributesToOptionMap(node.getAttributes());
        String path = attributeMap.getOrDefault("path", null);
        if (path == null) {
            throw new XmlProcessorException("Fact is missing path attribute");
        }

        Element factElement = (Element) node;
        Element nameElement = getDirectChildElement(factElement, FACT_NAME_CHILD_NAME);
        String name = nameElement != null ? nameElement.getTextContent().strip() : "";

        Element descriptionElement = getDirectChildElement(factElement, FACT_DESCRIPTION_CHILD_NAME);
        String description =
                descriptionElement != null ? descriptionElement.getTextContent().strip() : "";

        Element exportZeroElement = getDirectChildElement(factElement, FACT_EXPORT_ZERO);
        boolean exportZero = exportZeroElement != null;

        // writable
        Element writableElement = getDirectChildElement(factElement, FACT_WRITABLE_CHILD_NAME);
        List<Element> writableElementChildren = getAllDirectChildElements(writableElement);
        TaxWritable writable = readWritableNode(writableElementChildren);

        // derived
        TaxCompNode derived = readSingleCompNodeFromChild(factElement, FACT_DERIVED_CHILD_NAME, path);

        // placeholder
        TaxCompNode placeholder = readSingleCompNodeFromChild(factElement, FACT_PLACEHOLDER_CHILD_NAME, path);

        // Export
        Element exportElement = getDirectChildElement(factElement, FACT_EXPORT_CHILD_NAME);
        ExportNode export = readExportNode(exportElement);

        return new TaxFact(path, name, description, exportZero, writable, derived, placeholder, export);
    }

    private List<TaxFact> expandFactWithInlineEnumOptions(TaxFact taxFact) {
        List<TaxFact> facts = new ArrayList<>();
        TaxWritable writable = taxFact.writable();
        if (writable == null) {
            facts.add(taxFact);
            return facts;
        }

        String writableTypeName = writable.typeName();
        boolean isEnumWritable = "Enum".equals(writableTypeName) || "MultiEnum".equals(writableTypeName);
        if (!isEnumWritable) {
            facts.add(taxFact);
            return facts;
        }

        Map<String, String> writableOptions = new HashMap<>(writable.options());
        if (writableOptions.containsKey("optionsPath")
                || !writableOptions.containsKey(INLINE_ENUM_VALUES_OPTION_NAME)) {
            facts.add(taxFact);
            return facts;
        }

        List<String> inlineValues =
                parseInlineEnumValues(writableOptions.remove(INLINE_ENUM_VALUES_OPTION_NAME));
        if (inlineValues.isEmpty()) {
            facts.add(taxFact);
            return facts;
        }

        String optionsPath = buildInlineEnumOptionsPath(taxFact.path());
        writableOptions.put("optionsPath", optionsPath);

        TaxWritable normalizedWritable = new TaxWritable(
                writableTypeName, writableOptions, writable.collectionItemAlias(), writable.limits());
        TaxFact normalizedTaxFact = new TaxFact(
                taxFact.path(),
                taxFact.name(),
                taxFact.description(),
                taxFact.exportZero(),
                normalizedWritable,
                taxFact.derived(),
                taxFact.placeholder(),
                taxFact.export());
        facts.add(normalizedTaxFact);

        TaxCompNode enumOptionsNode = buildInlineEnumOptionsNode(inlineValues);
        TaxFact enumOptionsFact = new TaxFact(
                optionsPath,
                taxFact.name() + " Options",
                taxFact.description(),
                false,
                null,
                enumOptionsNode,
                null,
                null);
        facts.add(enumOptionsFact);
        return facts;
    }

    private TaxWritable readWritableNode(List<Element> writableElementList) {
        if (writableElementList.size() == 0) {
            return null;
        }

        String writableNodeName = null;
        Map<String, String> options = new HashMap<>();
        String collectionItemAlias = null;
        List<TaxLimit> limits = new ArrayList<>();

        boolean foundWritableNode = false;
        for (Element el : writableElementList) {
            if (!LIMIT_ELEMENT_NAME.equals(el.getNodeName())) {
                if (foundWritableNode) {
                    throw new XmlProcessorException("Writable node has more than 1 non-Limit child");
                }
                foundWritableNode = true;
                writableNodeName = normalizeNodeTypeName(el.getNodeName());

                String textNodeValue = "";
                List<String> inlineEnumValues = new ArrayList<>();
                NodeList childNodes = el.getChildNodes();
                for (int i = 0; i < childNodes.getLength(); i++) {
                    Node childNode = childNodes.item(i);
                    if (childNode.getNodeType() == Node.TEXT_NODE) {
                        textNodeValue = childNode.getNodeValue();
                    } else if (childNode.getNodeType() == Node.ELEMENT_NODE) {
                        collectInlineEnumValue((Element) childNode, inlineEnumValues);
                    }
                }
                options = convertTextValueAndAttributesToOptionMap(textNodeValue, el.getAttributes());
                if (!inlineEnumValues.isEmpty()
                        && !options.containsKey(INLINE_ENUM_VALUES_OPTION_NAME)) {
                    options.put(INLINE_ENUM_VALUES_OPTION_NAME, String.join(",", inlineEnumValues));
                }
                options = normalizeOptionsForNodeType(writableNodeName, options);

                // collection aliases are handled specially:  they are passed as an attribute, but
                // stripped
                // off and included separately to the fact graph's WritableConfig
                collectionItemAlias = options.getOrDefault(COLLECTION_ATTRIBUTE_NAME, null);
                options.remove(COLLECTION_ATTRIBUTE_NAME);
            } else {
                TaxLimit limit = readLimit(el);
                limits.add(limit);
            }
        }

        return new TaxWritable(writableNodeName, options, collectionItemAlias, limits);
    }

    private ExportNode readExportNode(Element expElement) {
        if (expElement == null) {
            return null;
        }

        String exportNodeName = expElement.getNodeName();
        Map<String, String> expOptions = convertAttributesToOptionMap(expElement.getAttributes());

        return new ExportNode(exportNodeName, expOptions);
    }

    private TaxCompNode readSingleCompNodeFromChild(final Element el, final String childName, final String path) {
        Element childElement = getDirectChildElement(el, childName);
        List<Element> grandchildren = getAllDirectChildElements(childElement);
        if (grandchildren.size() > 1) {
            if (FACT_DERIVED_CHILD_NAME.equals(childName)) {
                List<TaxCompNode> derivedExpressions = new ArrayList<>();
                for (Element grandchild : grandchildren) {
                    derivedExpressions.add(readCompNode(grandchild));
                }
                return foldDerivedExpressionsWithAdd(derivedExpressions);
            }
            throw new XmlProcessorException(String.format("Fact %s: %s has more than 1 child", path, childElement));
        } else if (grandchildren.size() == 1) {
            return readCompNode(grandchildren.get(0));
        }
        // child didn't exist
        return null;
    }

    private TaxCompNode foldDerivedExpressionsWithAdd(List<TaxCompNode> expressions) {
        if (expressions.isEmpty()) {
            return null;
        }

        TaxCompNode accumulator = expressions.get(0);
        for (int i = 1; i < expressions.size(); i++) {
            List<TaxCompNode> addChildren = new ArrayList<>();
            addChildren.add(accumulator);
            addChildren.add(expressions.get(i));
            accumulator = new TaxCompNode("Add", new HashMap<>(), addChildren);
        }

        return accumulator;
    }

    private TaxCompNode readCompNode(Node node) {
        List<TaxCompNode> children = new ArrayList<>();
        String textNodeValue = "";

        NodeList childNodes = node.getChildNodes();
        for (int i = 0; i < childNodes.getLength(); i++) {
            Node currentNode = childNodes.item(i);
            if (currentNode.getNodeType() == Node.ELEMENT_NODE) {
                TaxCompNode child = readCompNode(currentNode);
                children.add(child);
            } else if (currentNode.getNodeType() == Node.CDATA_SECTION_NODE) {
                textNodeValue = currentNode.getNodeValue();
            } else if (currentNode.getNodeType() == Node.TEXT_NODE) {
                textNodeValue = currentNode.getNodeValue();
            } else if (currentNode.getNodeType() == Node.COMMENT_NODE) {
                // skip this...
                continue;
            } else {
                throw new RuntimeException("Missing a type of XML node");
            }
        }

        String nodeTypeName = normalizeNodeTypeName(node.getNodeName());
        Map<String, String> options = convertTextValueAndAttributesToOptionMap(textNodeValue, node.getAttributes());
        options = normalizeOptionsForNodeType(nodeTypeName, options);

        return new TaxCompNode(nodeTypeName, options, children);
    }

    private TaxLimit readLimit(Element el) {
        List<Element> limitChildren = getAllDirectChildElements(el);
        if (limitChildren.size() != 1) {
            throw new XmlProcessorException(
                    String.format("Limit requires exactly 1 child (got %d)", limitChildren.size()));
        }
        Map<String, String> limitAttributes = convertAttributesToOptionMap(el.getAttributes());
        String operation = limitAttributes.get(LIMIT_TYPE_ATTRIBUTE_NAME);
        if (operation == null) {
            throw new XmlProcessorException("Limit requires a \"type\" attribute");
        }
        String levelString = limitAttributes.get(LIMIT_LEVEL_ATTRIBUTE_NAME);
        TaxLimitLevel limitLevel = null;
        try {
            limitLevel = TaxLimitLevel.from(levelString);
        } catch (NullPointerException e) {
            throw new XmlProcessorException(String.format("Invalid limit level %s", levelString), e);
        }
        TaxCompNode limitChildCompNode = readCompNode(limitChildren.get(0));
        return new TaxLimit(operation, limitLevel, limitChildCompNode);
    }

    private Map<String, String> convertTextValueAndAttributesToOptionMap(String textVal, NamedNodeMap attributes) {
        Map<String, String> options = convertAttributesToOptionMap(attributes);

        String textValue = textVal == null ? "" : textVal.strip();
        if (!"".equals(textValue)) {
            options.put(TEXT_NODE_VALUE_NAME, textValue);
        }

        return options;
    }

    private Map<String, String> convertAttributesToOptionMap(NamedNodeMap attributes) {
        Map<String, String> options = new HashMap<>();

        if (attributes != null) {
            for (int i = 0; i < attributes.getLength(); i++) {
                Node currentNode = attributes.item(i);
                options.put(
                        currentNode.getNodeName(), currentNode.getNodeValue().strip());
            }
        }

        return options;
    }

    private String normalizeNodeTypeName(String nodeTypeName) {
        if ("Decimal".equals(nodeTypeName)) {
            return "Rational";
        }
        return nodeTypeName;
    }

    private Map<String, String> normalizeOptionsForNodeType(String nodeTypeName, Map<String, String> options) {
        if (!"Rational".equals(nodeTypeName)) {
            return options;
        }

        String value = options.get(TEXT_NODE_VALUE_NAME);
        if (value == null || value.contains("/")) {
            return options;
        }

        options.put(TEXT_NODE_VALUE_NAME, decimalStringToRationalLiteral(value));
        return options;
    }

    private String decimalStringToRationalLiteral(String value) {
        String trimmed = value.strip();
        if (trimmed.isEmpty()) {
            return trimmed;
        }

        try {
            BigDecimal decimal = new BigDecimal(trimmed);
            int scale = decimal.scale();
            if (scale <= 0) {
                return decimal.toBigIntegerExact().toString();
            }

            BigInteger numerator = decimal.unscaledValue();
            BigInteger denominator = BigInteger.TEN.pow(scale);
            BigInteger gcd = numerator.gcd(denominator);
            numerator = numerator.divide(gcd);
            denominator = denominator.divide(gcd);

            if (BigInteger.ONE.equals(denominator)) {
                return numerator.toString();
            }
            return numerator + "/" + denominator;
        } catch (NumberFormatException | ArithmeticException ignored) {
            return trimmed;
        }
    }

    private TaxCompNode buildInlineEnumOptionsNode(List<String> enumValues) {
        List<TaxCompNode> optionNodes = new ArrayList<>();
        for (String enumValue : enumValues) {
            Map<String, String> option = new HashMap<>();
            option.put(TEXT_NODE_VALUE_NAME, enumValue);
            optionNodes.add(new TaxCompNode("String", option, new ArrayList<>()));
        }
        return new TaxCompNode("EnumOptions", new HashMap<>(), optionNodes);
    }

    private List<String> parseInlineEnumValues(String rawValues) {
        List<String> values = new ArrayList<>();
        if (rawValues == null || rawValues.isBlank()) {
            return values;
        }

        for (String value : rawValues.split(",")) {
            String normalized = value.strip();
            if (normalized.startsWith("\"") && normalized.endsWith("\"") && normalized.length() >= 2) {
                normalized = normalized.substring(1, normalized.length() - 1).strip();
            }
            if (!normalized.isEmpty()) {
                values.add(normalized);
            }
        }
        return values;
    }

    private String buildInlineEnumOptionsPath(String factPath) {
        String normalizedPath = factPath == null ? "" : factPath.strip();
        if (normalizedPath.startsWith("/")) {
            normalizedPath = normalizedPath.substring(1);
        }
        normalizedPath = normalizedPath.replace('/', '_');
        return "/__enumOptions/" + normalizedPath;
    }

    private void collectInlineEnumValue(Element optionElement, List<String> inlineEnumValues) {
        String nodeName = optionElement.getNodeName();
        if (!"Option".equals(nodeName) && !"EnumOption".equals(nodeName)) {
            return;
        }

        String value = optionElement.getAttribute("value");
        if (value == null || value.isBlank()) {
            value = optionElement.getTextContent();
        }

        if (value != null) {
            String normalized = value.strip();
            if (!normalized.isEmpty()) {
                inlineEnumValues.add(normalized);
            }
        }
    }

    private Element getDirectChildElement(Element parent, String name) {
        for (Node child = parent.getFirstChild(); child != null; child = child.getNextSibling()) {
            if (child.getNodeType() == Node.ELEMENT_NODE && name.equals(child.getNodeName())) {
                return (Element) child;
            }
        }
        return null;
    }

    private List<Element> getAllDirectChildElements(Element parent) {
        ArrayList<Element> childElements = new ArrayList<>();
        if (parent == null) {
            return childElements;
        }
        for (Node child = parent.getFirstChild(); child != null; child = child.getNextSibling()) {
            if (child.getNodeType() == Node.ELEMENT_NODE) {
                childElements.add((Element) child);
            }
        }
        return childElements;
    }
}
