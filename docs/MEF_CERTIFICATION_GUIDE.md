# MeF (Modernized e-File) Certification Guide

## Overview

This guide provides comprehensive documentation for obtaining IRS MeF certification for direct-file-easy-webui, enabling electronic filing of federal tax returns directly with the IRS.

---

## Table of Contents

1. [What is MeF?](#what-is-mef)
2. [Benefits of MeF Integration](#benefits-of-mef-integration)
3. [Provider Types](#provider-types)
4. [Certification Process](#certification-process)
5. [Technical Requirements](#technical-requirements)
6. [Architecture for direct-file-easy-webui](#architecture-for-direct-file-easy-webui)
7. [Development Guide](#development-guide)
8. [ATS Testing Process](#ats-testing-process)
9. [Production Deployment Checklist](#production-deployment-checklist)
10. [Annual Recertification](#annual-recertification)
11. [Cost Summary](#cost-summary)
12. [Alternative Approaches](#alternative-approaches)
13. [References](#references)

---

## What is MeF?

The **Modernized e-File (MeF)** system is the IRS's electronic tax filing platform that replaced the legacy e-file system. MeF processes individual tax returns (Form 1040), corporate returns, partnership returns, and various other form types.

### Key Characteristics

| Feature | Description |
|---------|-------------|
| **Protocol** | SOAP 1.2 over HTTPS |
| **Security** | WS-Security with X.509 certificates |
| **Data Format** | XML conforming to IRS schemas |
| **Signatures** | XML-DSIG (XML Digital Signatures) |
| **Availability** | 24/7 with scheduled maintenance windows |
| **Processing** | Near real-time acknowledgments |

### MeF System Components

```
+------------------+     +------------------+     +------------------+
|   Tax Software   | --> |   Transmitter    | --> |    IRS MeF      |
|   (Preparer)     |     |   (Gateway)      |     |    Systems      |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        v                        v                        v
   Generate XML           Sign & Transmit          Validate & Process
   Validate Data          Track Status             Issue Acknowledgments
```

---

## Benefits of MeF Integration

### For Taxpayers

| Benefit | Description |
|---------|-------------|
| **Faster Refunds** | Direct deposit refunds in 10-21 days vs. 6-8 weeks for paper |
| **Immediate Confirmation** | Real-time acknowledgment of return receipt |
| **Accuracy** | Built-in validation reduces errors by 20x compared to paper |
| **Convenience** | File anytime, anywhere with internet access |
| **Security** | Encrypted transmission with digital signatures |

### For Software Providers

| Benefit | Description |
|---------|-------------|
| **Direct IRS Access** | No intermediary fees for transmission |
| **Real-time Status** | Immediate submission and acknowledgment tracking |
| **Comprehensive API** | Support for all major form types |
| **Scalability** | Handle high volumes during peak season |
| **Compliance** | IRS-certified for regulatory requirements |

### Comparison: MeF vs. Paper Filing

| Metric | MeF e-File | Paper Filing |
|--------|------------|--------------|
| Refund Time | 10-21 days | 6-8 weeks |
| Error Rate | < 1% | ~20% |
| Confirmation | Immediate | None |
| Cost per Return | ~$0.50 | ~$5+ |
| Audit Trail | Complete | Limited |

---

## Provider Types

The IRS defines three types of e-file providers, each with distinct roles and requirements:

### 1. Software Developer

**Role**: Creates tax preparation software that generates MeF-compliant XML.

| Requirement | Details |
|-------------|---------|
| **Suitability Check** | FBI fingerprint background check |
| **Application** | Form 8633 (Application for IRS e-file Provider) |
| **Testing** | Pass Assurance Testing System (ATS) |
| **Certification** | Annual software certification |
| **Responsibility** | XML generation, validation, user interface |

### 2. Transmitter

**Role**: Transmits tax returns to IRS MeF and receives acknowledgments.

| Requirement | Details |
|-------------|---------|
| **EFIN** | Electronic Filing Identification Number required |
| **PKI Certificate** | X.509 certificate from IRS-approved CA |
| **Infrastructure** | Secure servers meeting IRS requirements |
| **SLA** | 99.5% uptime during filing season |
| **Responsibility** | SOAP transmission, WS-Security, status tracking |

### 3. Electronic Return Originator (ERO)

**Role**: Originates tax returns from taxpayer data.

| Requirement | Details |
|-------------|---------|
| **EFIN** | Required for each physical location |
| **Background Check** | All principals must pass suitability |
| **Record Keeping** | Retain returns for 3 years |
| **Responsibility** | Taxpayer interaction, data collection, signatures |

### Combined Provider Options

| Configuration | Pros | Cons |
|---------------|------|------|
| **All Three Roles** | Full control, no dependencies | Highest complexity and cost |
| **Software Dev + ERO** | Control over UX, partner for transmission | Transmitter fees |
| **Software Dev Only** | Lowest barrier, focus on software | Dependent on partners |

---

## Certification Process

### Step-by-Step Timeline

```
Month 1-2: Application & Background Check
    |
    v
Month 3-4: Technical Implementation
    |
    v
Month 5: ATS Testing (3-4 weeks)
    |
    v
Month 6: Production Certification
    |
    v
Ongoing: Annual Recertification
```

### Step 1: IRS e-file Application

**Timeline**: 4-8 weeks

1. **Register for e-Services**
   - URL: https://www.irs.gov/e-file-providers/e-services-online-tools-for-tax-professionals
   - Create account and complete identity verification

2. **Submit Form 8633**
   - URL: https://www.irs.gov/pub/irs-pdf/f8633.pdf
   - Include all principals (>10% ownership)
   - Provide fingerprints via approved vendors

3. **Obtain EFIN**
   - Assigned after background check approval
   - Required for transmitter and ERO roles

### Step 2: Technical Setup

**Timeline**: 4-6 weeks

1. **Obtain PKI Certificates**
   - Request from IRS-approved Certificate Authority
   - Types needed:
     - Signing certificate (for XML-DSIG)
     - TLS client certificate (for SOAP connections)

2. **Acquire MeF Schemas**
   - URL: https://www.irs.gov/e-file-providers/current-valid-xml-schemas-and-business-rules
   - Download current year schemas
   - Implement schema validation

3. **Configure Development Environment**
   - Set up SOAP client with WS-Security
   - Implement XML-DSIG signing
   - Configure TLS 1.2+ connections

### Step 3: ATS Testing

**Timeline**: 3-4 weeks

1. **Access ATS Environment**
   - URL: https://www.irs.gov/e-file-providers/assurance-testing-system-ats
   - Use test EFIN and certificates

2. **Execute Test Scenarios**
   - IRS provides mandatory test cases
   - Must pass 100% of required scenarios
   - See [ATS Testing Process](#ats-testing-process) for details

3. **Submit Results**
   - Provide test run evidence to IRS
   - Address any failures with corrections

### Step 4: Production Certification

**Timeline**: 1-2 weeks

1. **Complete Production Checklist**
   - Verify all components production-ready
   - Confirm security controls in place

2. **Execute Production Test**
   - Submit test return to production MeF
   - Verify end-to-end processing

3. **Receive Certification**
   - IRS issues certification letter
   - Software listed in IRS database

### IRS Resources

| Resource | URL |
|----------|-----|
| MeF Program Information | https://www.irs.gov/e-file-providers/modernized-e-file-program-information |
| e-Services Registration | https://www.irs.gov/e-file-providers/e-services-online-tools-for-tax-professionals |
| Publication 3112 | https://www.irs.gov/pub/irs-pdf/p3112.pdf |
| ATS Information | https://www.irs.gov/e-file-providers/assurance-testing-system-ats |
| XML Schemas | https://www.irs.gov/e-file-providers/current-valid-xml-schemas-and-business-rules |
| Business Rules | https://www.irs.gov/e-file-providers/current-year-individual-income-tax-business-rules |

---

## Technical Requirements

### SOAP Web Services

MeF uses SOAP 1.2 with specific WS-* standards:

```xml
<!-- Example SOAP Envelope Structure -->
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Header>
    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <wsse:BinarySecurityToken
        EncodingType="Base64Binary"
        ValueType="X509v3">
        <!-- Base64-encoded X.509 certificate -->
      </wsse:BinarySecurityToken>
      <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
        <!-- XML-DSIG signature over SOAP body -->
      </ds:Signature>
      <wsu:Timestamp xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
        <wsu:Created>2025-01-15T10:00:00Z</wsu:Created>
        <wsu:Expires>2025-01-15T10:05:00Z</wsu:Expires>
      </wsu:Timestamp>
    </wsse:Security>
  </soap:Header>
  <soap:Body>
    <!-- MeF operation payload -->
  </soap:Body>
</soap:Envelope>
```

### WS-Security Implementation

| Component | Standard | Purpose |
|-----------|----------|---------|
| Token Type | X.509 v3 | Client authentication |
| Signature Algorithm | RSA-SHA256 | Message integrity |
| Canonicalization | Exclusive C14N | XML normalization |
| Timestamp | WSU Timestamp | Replay prevention |

### TLS Requirements

| Requirement | Specification |
|-------------|---------------|
| Minimum Version | TLS 1.2 |
| Recommended Version | TLS 1.3 |
| Cipher Suites | AES-256-GCM, AES-128-GCM |
| Certificate Validation | Full chain verification |
| Client Certificate | Required for mutual TLS |

### XML Digital Signatures (XML-DSIG)

Returns must be signed using XML-DSIG (W3C XML Signature):

```xml
<!-- XML-DSIG Signature Structure -->
<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
  <SignedInfo>
    <CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
    <SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
    <Reference URI="#Return">
      <Transforms>
        <Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
      </Transforms>
      <DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
      <DigestValue><!-- Base64-encoded SHA-256 hash --></DigestValue>
    </Reference>
  </SignedInfo>
  <SignatureValue><!-- Base64-encoded RSA signature --></SignatureValue>
  <KeyInfo>
    <X509Data>
      <X509Certificate><!-- Base64-encoded certificate --></X509Certificate>
    </X509Data>
  </KeyInfo>
</Signature>
```

### IRS XML Schema Compliance

Tax returns must validate against IRS-published XSD schemas:

```
efile/
├── Common/
│   ├── efileTypes.xsd
│   ├── efileAttachments.xsd
│   └── ReturnHeader1040x.xsd
├── IndividualIncomeTax/
│   ├── IRS1040/
│   │   ├── IRS1040.xsd
│   │   ├── IRS1040Schedule1.xsd
│   │   ├── IRS1040Schedule2.xsd
│   │   └── IRS1040Schedule3.xsd
│   ├── IRS8812/
│   │   └── IRS8812.xsd
│   └── IRSW2/
│       └── IRSW2.xsd
└── Manifest/
    └── efileManifest.xsd
```

### MeF Type Definitions

The project defines MeF-compliant types in `/direct-file/backend/src/main/resources/tax/mefTypes.xml`:

| Type | Pattern | Description |
|------|---------|-------------|
| `/mefNameType` | `[\sA-Za-z0-9\-]` | Full name characters |
| `/mefZipCodeType` | `[0-9]` | ZIP code digits |
| `/mefBusinessNameLine1Type` | Complex regex | Business name characters |
| `/mefStateEmployerIdType` | Extended ASCII | State employer ID |
| `/mefOccupationType` | `[\sA-Za-z0-9\-]+` | Occupation text |
| `/mefLocalityNmType` | Extended ASCII | Locality names |

---

## Architecture for direct-file-easy-webui

### System Architecture Diagram

```
+------------------------------------------------------------------+
|                     direct-file-easy-webui                        |
+------------------------------------------------------------------+
|                                                                  |
|  +------------------+     +------------------+     +------------+|
|  |   df-client-app  |     |    Backend       |     | ai_service ||
|  |   (React/TS)     |     |    (Scala)       |     | (Python)   ||
|  +--------+---------+     +--------+---------+     +-----+------+|
|           |                        |                     |       |
|           v                        v                     v       |
|  +------------------+     +------------------+     +------------+|
|  |   Fact Graph     |     |  Tax Calculator  |     |  Tax       ||
|  |   (User Input)   |     |  (XML Logic)     |     |  Explainer ||
|  +--------+---------+     +--------+---------+     +------------+|
|           |                        |                             |
|           +----------+-------------+                             |
|                      |                                           |
|                      v                                           |
|           +------------------+                                   |
|           |  XML Generator   |                                   |
|           |  (MeF Schemas)   |                                   |
|           +--------+---------+                                   |
|                    |                                             |
+------------------------------------------------------------------+
                     |
                     v
          +------------------+
          | MeF e-File       |
          | Service          |
          | (Transmitter)    |
          +--------+---------+
                   |
                   | SOAP/HTTPS
                   | WS-Security
                   | XML-DSIG
                   v
          +------------------+
          |    IRS MeF       |
          |    Systems       |
          +------------------+
```

### Component Responsibilities

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **df-client-app** | `df-client/df-client-app/` | User interface, data collection, validation |
| **Fact Graph** | `backend/.../tax/*.xml` | Tax calculation rules, business logic |
| **Backend** | `backend/` | Data persistence, PDF generation, API |
| **ai_service** | `ai_service/` | Tax explanations, document processing |
| **MeF Service** | `ai_service/services/` | e-File transmission (planned) |

### Data Flow

```
1. User Input (df-client-app)
   └── Taxpayer enters data via React forms
   └── Data validated against mefTypes patterns

2. Fact Graph Processing (backend)
   └── Facts computed from user input
   └── Tax calculations performed (taxCalculations.xml)
   └── Derived values computed (eitc.xml, ctcOdc.xml, etc.)

3. XML Generation (backend)
   └── Facts mapped to IRS XML elements
   └── Schemas validated against IRS XSD
   └── Return assembled with attachments

4. Digital Signing (mef_efile_service)
   └── XML-DSIG signature applied
   └── Certificate embedded

5. Transmission (mef_efile_service)
   └── SOAP envelope constructed
   └── WS-Security headers added
   └── Sent to IRS MeF endpoint

6. Acknowledgment Processing
   └── Parse IRS response
   └── Update submission status
   └── Notify taxpayer
```

---

## Development Guide

### Setting Up the MeF e-File Service

The MeF e-file integration is implemented in `ai_service/services/mef_efile_service.py`:

#### Service Structure

```python
"""
MeF e-File Service for direct-file-easy-webui

This module provides the interface for submitting tax returns
to the IRS Modernized e-File (MeF) system.

Location: ai_service/services/mef_efile_service.py
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SubmissionStatus(Enum):
    """MeF submission status codes."""
    PENDING = "pending"
    TRANSMITTED = "transmitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class MeFSubmission:
    """Represents a MeF submission."""
    submission_id: str
    efin: str
    tax_year: int
    form_type: str
    xml_content: str
    status: SubmissionStatus
    acknowledgment_id: Optional[str] = None
    rejection_codes: Optional[List[str]] = None
    timestamp: Optional[datetime] = None


@dataclass
class MeFAcknowledgment:
    """IRS acknowledgment response."""
    submission_id: str
    status: str
    acknowledgment_id: Optional[str]
    rejection_codes: List[Dict[str, str]]
    timestamp: datetime


class MeFEFileService:
    """
    Service for MeF e-File operations.

    This service handles:
    - XML generation from Fact Graph
    - XML-DSIG signing
    - SOAP transmission
    - Acknowledgment processing
    """

    def __init__(
        self,
        efin: str,
        certificate_path: str,
        private_key_path: str,
        environment: str = "ats"  # "ats" or "production"
    ):
        """
        Initialize MeF e-File service.

        Args:
            efin: Electronic Filing Identification Number
            certificate_path: Path to X.509 certificate
            private_key_path: Path to private key
            environment: "ats" for testing, "production" for live
        """
        self.efin = efin
        self.certificate_path = certificate_path
        self.private_key_path = private_key_path
        self.environment = environment

        # MeF endpoints
        self.endpoints = {
            "ats": "https://la.www4.irs.gov/a2a/mef",
            "production": "https://la.www4.irs.gov/a2a/mef"
        }

    def generate_return_xml(
        self,
        facts: Dict[str, Any],
        tax_year: int = 2025
    ) -> str:
        """
        Generate IRS-compliant XML from Fact Graph.

        Args:
            facts: Dictionary of fact values
            tax_year: Tax year for return

        Returns:
            XML string conforming to IRS schemas
        """
        # Build Return element
        return_elem = ET.Element("Return", {
            "xmlns": "http://www.irs.gov/efile",
            "returnVersion": f"{tax_year}v5.0"
        })

        # Add ReturnHeader
        header = self._build_return_header(facts, tax_year)
        return_elem.append(header)

        # Add ReturnData
        data = self._build_return_data(facts, tax_year)
        return_elem.append(data)

        return ET.tostring(return_elem, encoding="unicode")

    def _build_return_header(
        self,
        facts: Dict[str, Any],
        tax_year: int
    ) -> ET.Element:
        """Build ReturnHeader element."""
        header = ET.Element("ReturnHeader", {
            "binaryAttachmentCnt": "0"
        })

        # Tax Year
        ty = ET.SubElement(header, "TaxYr")
        ty.text = str(tax_year)

        # Tax Period Begin/End
        begin = ET.SubElement(header, "TaxPeriodBeginDt")
        begin.text = f"{tax_year}-01-01"

        end = ET.SubElement(header, "TaxPeriodEndDt")
        end.text = f"{tax_year}-12-31"

        # Filer information
        filer = ET.SubElement(header, "Filer")

        # Primary filer from facts
        primary_filer = self._get_primary_filer(facts)
        if primary_filer:
            name = ET.SubElement(filer, "PrimaryNameControlTxt")
            name.text = primary_filer.get("lastName", "")[:4].upper()

            ssn = ET.SubElement(filer, "PrimarySSN")
            ssn.text = self._format_ssn(primary_filer.get("tin", {}))

        return header

    def _build_return_data(
        self,
        facts: Dict[str, Any],
        tax_year: int
    ) -> ET.Element:
        """Build ReturnData element with all forms."""
        data = ET.Element("ReturnData", {
            "documentCnt": "1"
        })

        # IRS1040 main form
        form_1040 = self._build_form_1040(facts, tax_year)
        data.append(form_1040)

        # Add schedules based on facts
        if self._needs_schedule_1(facts):
            data.append(self._build_schedule_1(facts))

        if self._needs_schedule_2(facts):
            data.append(self._build_schedule_2(facts))

        if self._needs_schedule_3(facts):
            data.append(self._build_schedule_3(facts))

        # Add W-2 forms
        for w2 in self._get_w2_forms(facts):
            data.append(self._build_w2(w2))

        return data

    def _build_form_1040(
        self,
        facts: Dict[str, Any],
        tax_year: int
    ) -> ET.Element:
        """Build IRS1040 element."""
        form = ET.Element("IRS1040", {
            "documentId": "IRS1040",
            "referenceDocumentId": ""
        })

        # Filing status
        filing_status = self._get_fact_value(
            facts, "/filingStatus", "single"
        )
        fs_elem = ET.SubElement(form, "IndividualReturnFilingStatusCd")
        fs_elem.text = self._map_filing_status(filing_status)

        # Wages (Line 1)
        wages = self._calculate_total_wages(facts)
        wages_elem = ET.SubElement(form, "WagesSalariesAndTipsAmt")
        wages_elem.text = str(int(wages))

        # Additional form elements...

        return form

    def sign_xml(self, xml_content: str) -> str:
        """
        Apply XML-DSIG signature to return.

        Args:
            xml_content: Unsigned XML

        Returns:
            Signed XML with embedded signature
        """
        # Implementation would use signxml or lxml-xmlsec
        # This is a placeholder for the signing logic
        logger.info("Signing XML return")

        # In production, use proper XML-DSIG library:
        # from signxml import XMLSigner
        # signer = XMLSigner(
        #     method=signxml.methods.enveloped,
        #     signature_algorithm="rsa-sha256",
        #     digest_algorithm="sha256"
        # )
        # signed = signer.sign(xml_content, key=self.private_key, cert=self.certificate)

        return xml_content  # Placeholder

    def transmit(self, submission: MeFSubmission) -> MeFAcknowledgment:
        """
        Transmit signed return to IRS MeF.

        Args:
            submission: MeFSubmission with signed XML

        Returns:
            MeFAcknowledgment from IRS
        """
        logger.info(f"Transmitting submission {submission.submission_id}")

        # Build SOAP envelope with WS-Security
        soap_envelope = self._build_soap_envelope(submission)

        # Send to MeF endpoint
        endpoint = self.endpoints.get(self.environment)

        # In production, use requests or zeep with proper WS-Security:
        # response = self._send_soap_request(endpoint, soap_envelope)

        # Parse acknowledgment
        # ack = self._parse_acknowledgment(response)

        # Placeholder acknowledgment
        return MeFAcknowledgment(
            submission_id=submission.submission_id,
            status="pending",
            acknowledgment_id=None,
            rejection_codes=[],
            timestamp=datetime.now()
        )

    def check_status(self, submission_id: str) -> MeFAcknowledgment:
        """
        Check status of a submitted return.

        Args:
            submission_id: ID of submission to check

        Returns:
            Current acknowledgment status
        """
        logger.info(f"Checking status for {submission_id}")

        # Would call MeF GetAck operation
        # ...

        return MeFAcknowledgment(
            submission_id=submission_id,
            status="pending",
            acknowledgment_id=None,
            rejection_codes=[],
            timestamp=datetime.now()
        )

    def _build_soap_envelope(self, submission: MeFSubmission) -> str:
        """Build SOAP envelope with WS-Security."""
        # SOAP envelope template
        envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:mef="http://www.irs.gov/a2a/mef">
  <soap:Header>
    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <!-- WS-Security headers added here -->
    </wsse:Security>
  </soap:Header>
  <soap:Body>
    <mef:SendSubmissions>
      <mef:SubmissionDataList>
        <mef:SubmissionData>
          <mef:SubmissionId>{submission.submission_id}</mef:SubmissionId>
          <mef:EFIN>{self.efin}</mef:EFIN>
          <mef:ElectronicPostmark>{datetime.now().isoformat()}</mef:ElectronicPostmark>
          <mef:ReturnData>{submission.xml_content}</mef:ReturnData>
        </mef:SubmissionData>
      </mef:SubmissionDataList>
    </mef:SendSubmissions>
  </soap:Body>
</soap:Envelope>'''
        return envelope

    # Helper methods

    def _get_primary_filer(self, facts: Dict[str, Any]) -> Optional[Dict]:
        """Extract primary filer from facts."""
        filers = facts.get("/filers", {}).get("item", {}).get("items", [])
        for filer_id in filers:
            is_primary = facts.get(
                f"/filers/#{filer_id}/isPrimaryFiler", {}
            ).get("item", False)
            if is_primary:
                return {
                    "firstName": facts.get(f"/filers/#{filer_id}/firstName", {}).get("item", ""),
                    "lastName": facts.get(f"/filers/#{filer_id}/lastName", {}).get("item", ""),
                    "tin": facts.get(f"/filers/#{filer_id}/tin", {}).get("item", {}),
                    "dateOfBirth": facts.get(f"/filers/#{filer_id}/dateOfBirth", {}).get("item", {})
                }
        return None

    def _format_ssn(self, tin: Dict) -> str:
        """Format TIN as SSN string."""
        return f"{tin.get('area', '')}{tin.get('group', '')}{tin.get('serial', '')}"

    def _get_fact_value(
        self,
        facts: Dict,
        path: str,
        default: Any = None
    ) -> Any:
        """Get fact value from facts dictionary."""
        fact = facts.get(path, {})
        if isinstance(fact, dict):
            item = fact.get("item")
            if isinstance(item, dict) and "value" in item:
                return item["value"][0] if item["value"] else default
            return item if item is not None else default
        return fact if fact is not None else default

    def _calculate_total_wages(self, facts: Dict) -> float:
        """Calculate total wages from W-2 forms."""
        total = 0.0
        w2s = facts.get("/formW2s", {}).get("item", {}).get("items", [])
        for w2_id in w2s:
            wages = facts.get(f"/formW2s/#{w2_id}/writableWages", {})
            if wages:
                try:
                    total += float(wages.get("item", "0"))
                except (ValueError, TypeError):
                    pass
        return total

    def _map_filing_status(self, status: str) -> str:
        """Map internal status to IRS code."""
        mapping = {
            "single": "1",
            "mfj": "2",
            "mfs": "3",
            "hoh": "4",
            "qss": "5"
        }
        return mapping.get(status, "1")

    def _needs_schedule_1(self, facts: Dict) -> bool:
        """Check if Schedule 1 is needed."""
        # Schedule 1 needed for adjustments or additional income
        return (
            self._get_fact_value(facts, "/hadStudentLoanInterestPayments", False) or
            self._get_fact_value(facts, "/madeIraContributions", False)
        )

    def _needs_schedule_2(self, facts: Dict) -> bool:
        """Check if Schedule 2 is needed."""
        # Schedule 2 needed for additional taxes
        return False  # Implement based on fact conditions

    def _needs_schedule_3(self, facts: Dict) -> bool:
        """Check if Schedule 3 is needed."""
        # Schedule 3 needed for additional credits
        return False  # Implement based on fact conditions

    def _get_w2_forms(self, facts: Dict) -> List[Dict]:
        """Get all W-2 forms from facts."""
        w2s = []
        w2_ids = facts.get("/formW2s", {}).get("item", {}).get("items", [])
        for w2_id in w2_ids:
            w2 = {
                "id": w2_id,
                "employerName": self._get_fact_value(
                    facts, f"/formW2s/#{w2_id}/employerName"
                ),
                "ein": facts.get(f"/formW2s/#{w2_id}/ein", {}).get("item", {}),
                "wages": self._get_fact_value(
                    facts, f"/formW2s/#{w2_id}/writableWages", "0"
                ),
                "federalWithholding": self._get_fact_value(
                    facts, f"/formW2s/#{w2_id}/writableFederalWithholding", "0"
                )
            }
            w2s.append(w2)
        return w2s

    def _build_schedule_1(self, facts: Dict) -> ET.Element:
        """Build IRS1040Schedule1 element."""
        sched = ET.Element("IRS1040Schedule1", {"documentId": "IRS1040S1"})
        # Add schedule 1 elements...
        return sched

    def _build_schedule_2(self, facts: Dict) -> ET.Element:
        """Build IRS1040Schedule2 element."""
        sched = ET.Element("IRS1040Schedule2", {"documentId": "IRS1040S2"})
        # Add schedule 2 elements...
        return sched

    def _build_schedule_3(self, facts: Dict) -> ET.Element:
        """Build IRS1040Schedule3 element."""
        sched = ET.Element("IRS1040Schedule3", {"documentId": "IRS1040S3"})
        # Add schedule 3 elements...
        return sched

    def _build_w2(self, w2: Dict) -> ET.Element:
        """Build IRSW2 element."""
        form = ET.Element("IRSW2", {"documentId": f"W2-{w2['id'][:8]}"})

        # Employer name
        emp_name = ET.SubElement(form, "EmployerNameControlTxt")
        emp_name.text = w2.get("employerName", "")[:4].upper()

        # EIN
        ein_data = w2.get("ein", {})
        ein = ET.SubElement(form, "EmployerEIN")
        ein.text = f"{ein_data.get('prefix', '')}{ein_data.get('serial', '')}"

        # Wages
        wages = ET.SubElement(form, "WagesAmt")
        wages.text = str(int(float(w2.get("wages", "0"))))

        # Withholding
        withhold = ET.SubElement(form, "WithholdingAmt")
        withhold.text = str(int(float(w2.get("federalWithholding", "0"))))

        return form
```

### XML Validation

```python
"""XML validation against IRS schemas."""

from lxml import etree
from pathlib import Path
from typing import List, Tuple


class MeFXMLValidator:
    """Validates MeF XML against IRS schemas."""

    def __init__(self, schema_dir: Path):
        """
        Initialize validator with schema directory.

        Args:
            schema_dir: Directory containing IRS XSD schemas
        """
        self.schema_dir = schema_dir
        self._schemas = {}

    def load_schema(self, form_type: str) -> etree.XMLSchema:
        """Load XSD schema for form type."""
        if form_type not in self._schemas:
            schema_path = self.schema_dir / f"{form_type}.xsd"
            schema_doc = etree.parse(str(schema_path))
            self._schemas[form_type] = etree.XMLSchema(schema_doc)
        return self._schemas[form_type]

    def validate(
        self,
        xml_content: str,
        form_type: str = "IRS1040"
    ) -> Tuple[bool, List[str]]:
        """
        Validate XML against schema.

        Args:
            xml_content: XML string to validate
            form_type: IRS form type

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            schema = self.load_schema(form_type)
            doc = etree.fromstring(xml_content.encode())
            schema.assertValid(doc)
            return True, []
        except etree.DocumentInvalid as e:
            errors = [str(err) for err in schema.error_log]
            return False, errors
        except Exception as e:
            return False, [str(e)]


# Usage example
def validate_return(xml: str, schema_dir: str) -> bool:
    """Validate a tax return XML."""
    validator = MeFXMLValidator(Path(schema_dir))
    is_valid, errors = validator.validate(xml)

    if not is_valid:
        for error in errors:
            print(f"Validation error: {error}")

    return is_valid
```

### Integration with Fact Graph

```python
"""Integration between Fact Graph and MeF service."""

from typing import Dict, Any
import json


def facts_to_mef_submission(
    facts_json: str,
    efin: str,
    tax_year: int = 2025
) -> Dict[str, Any]:
    """
    Convert Fact Graph JSON to MeF submission.

    Args:
        facts_json: JSON string of fact graph
        efin: Electronic Filing Identification Number
        tax_year: Tax year

    Returns:
        Dictionary ready for MeF submission
    """
    facts = json.loads(facts_json)["facts"]

    # Initialize MeF service
    service = MeFEFileService(
        efin=efin,
        certificate_path="/path/to/cert.pem",
        private_key_path="/path/to/key.pem",
        environment="ats"
    )

    # Generate XML
    xml_content = service.generate_return_xml(facts, tax_year)

    # Sign XML
    signed_xml = service.sign_xml(xml_content)

    return {
        "xml": signed_xml,
        "efin": efin,
        "tax_year": tax_year,
        "form_type": "1040"
    }
```

---

## ATS Testing Process

### What is ATS?

The **Assurance Testing System (ATS)** is the IRS's testing environment for validating e-file software before production certification.

### ATS Requirements

| Requirement | Description |
|-------------|-------------|
| **Test Returns** | Submit IRS-provided test scenarios |
| **Pass Rate** | 100% of required scenarios must pass |
| **Timing** | Complete within testing window (typically 3-4 weeks) |
| **Evidence** | Provide acknowledgment IDs and screenshots |

### ATS Test Scenarios

The project includes ATS test scenarios in `direct-file/backend/src/test/resources/scenarios/`:

| Scenario | File | Description |
|----------|------|-------------|
| ATS-1 | `mef-ats-1.json` | Single filer, W-2 income, standard deduction |
| ATS-1-DD | `mef-ats-1-dd.json` | Same as ATS-1 with direct deposit |
| ATS-2 | `mef-ats-2.json` | Married filing jointly |
| ATS-2a | `mef-ats-2a.json` | MFJ variant scenario |
| ATS-4 | `mef-ats-4.json` | Complex income scenario |
| ATS-5 | `mef-ats-5.json` | Credits and deductions |
| ATS-SSA | `mef-ats-SSA.json` | Social Security income |
| ATS-Balance-Due | `mef-ats-balance-due.json` | Tax owed scenario |
| ATS-1040SR-EIC | `mef-ats-1040sr-eic.json` | Form 1040-SR with EITC |

### Running ATS Tests

```bash
# Run ATS test scenarios
cd direct-file/backend
./gradlew test --tests "*MefAts*"

# Verify PDF output matches expected
./gradlew test --tests "*PdfExpected*"

# Generate submission files for ATS environment
./gradlew generateAtsSubmissions
```

### ATS Timeline

```
Week 1: Environment Setup
    - Obtain ATS credentials
    - Configure test certificates
    - Verify connectivity

Week 2: Initial Submissions
    - Submit basic scenarios (ATS-1, ATS-2)
    - Verify acknowledgments
    - Address any rejections

Week 3: Complete Testing
    - Submit remaining scenarios
    - Resubmit corrections if needed
    - Document all acknowledgments

Week 4: Certification
    - Submit ATS completion evidence
    - Receive certification approval
    - Transition to production
```

### ATS Checklist

- [ ] Obtain ATS test credentials from IRS
- [ ] Configure test EFIN and certificates
- [ ] Verify SOAP connectivity to ATS endpoint
- [ ] Submit ATS-1 basic scenario
- [ ] Verify acceptance acknowledgment
- [ ] Submit all required ATS scenarios
- [ ] Document acknowledgment IDs
- [ ] Address any rejections
- [ ] Submit ATS completion form to IRS
- [ ] Receive production certification

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] **Certification Complete**
  - [ ] ATS testing passed
  - [ ] IRS certification letter received
  - [ ] Software listed in IRS database

- [ ] **Security Review**
  - [ ] Production certificates obtained
  - [ ] Key management procedures documented
  - [ ] Access controls configured
  - [ ] Audit logging enabled

- [ ] **Infrastructure Ready**
  - [ ] Production servers provisioned
  - [ ] TLS 1.2+ configured
  - [ ] Firewall rules for IRS endpoints
  - [ ] Load testing completed

### Deployment

- [ ] **Certificate Installation**
  - [ ] Production X.509 certificate installed
  - [ ] Private key secured (HSM recommended)
  - [ ] Certificate chain validated

- [ ] **Configuration**
  - [ ] Production EFIN configured
  - [ ] MeF endpoint URLs set to production
  - [ ] Error handling and retry logic enabled
  - [ ] Monitoring and alerting configured

- [ ] **Validation**
  - [ ] Production connectivity test
  - [ ] Submit test return (if allowed)
  - [ ] Verify acknowledgment processing

### Post-Deployment

- [ ] **Monitoring**
  - [ ] Submission success rate > 99%
  - [ ] Response times < 30 seconds
  - [ ] Error rate tracking
  - [ ] Alert thresholds configured

- [ ] **Documentation**
  - [ ] Runbook for common issues
  - [ ] Escalation procedures
  - [ ] IRS contact information

---

## Annual Recertification

### Recertification Requirements

Each tax year requires recertification to ensure software compatibility with updated IRS schemas and business rules.

### Timeline

| Month | Activity |
|-------|----------|
| **August** | IRS releases draft schemas for next tax year |
| **September** | Begin schema integration and updates |
| **October** | IRS releases final schemas |
| **November** | Complete ATS testing for new tax year |
| **December** | Production certification |
| **January** | Filing season begins |

### Annual Tasks

1. **Schema Updates**
   - Download new XML schemas
   - Update validation logic
   - Test against sample returns

2. **Business Rule Updates**
   - Review IRS business rule changes
   - Update fact calculations
   - Verify form field mappings

3. **ATS Re-Testing**
   - Execute updated ATS scenarios
   - Verify all scenarios pass
   - Document acknowledgments

4. **Security Updates**
   - Renew expiring certificates
   - Review access controls
   - Update encryption algorithms if needed

### Recertification Checklist

- [ ] Download and review new tax year schemas
- [ ] Update `mefTypes.xml` for any type changes
- [ ] Update fact dictionary modules for tax law changes
- [ ] Update standard deduction, bracket, and credit amounts
- [ ] Run comprehensive test suite
- [ ] Execute ATS testing for new tax year
- [ ] Submit recertification evidence to IRS
- [ ] Deploy updated software before filing season

---

## Cost Summary

### Initial Certification Costs

| Item | Cost | Notes |
|------|------|-------|
| **IRS Application Fee** | Free | Form 8633 |
| **Background Check** | ~$50-100/person | FBI fingerprinting |
| **PKI Certificates** | $200-500/year | From approved CA |
| **Development** | Variable | 2-4 months typical |
| **Testing Infrastructure** | $500-2000 | Cloud servers for ATS |
| **Security Review** | $5000-15000 | If third-party audit required |

### Annual Operating Costs

| Item | Cost | Notes |
|------|------|-------|
| **Certificate Renewal** | $200-500/year | PKI certificates |
| **Recertification** | 40-80 hours | Development time |
| **Infrastructure** | $1000-5000/year | Servers, monitoring |
| **Support** | Variable | Filing season staffing |

### Total Estimated Costs

| Approach | Year 1 | Annual |
|----------|--------|--------|
| **Software Dev Only** | $10,000-25,000 | $3,000-8,000 |
| **Software + ERO** | $15,000-35,000 | $5,000-12,000 |
| **Full Stack (All Roles)** | $50,000-100,000 | $15,000-30,000 |

---

## Alternative Approaches

If full MeF certification is not feasible, consider these alternatives:

### 1. Partner with Licensed Transmitter

**Approach**: Build software, partner with existing transmitter.

| Pros | Cons |
|------|------|
| Faster time to market | Per-return fees |
| No transmitter certification | Less control |
| Reduced infrastructure | Dependency on partner |

**Partners to Consider**:
- Drake Software
- TaxSlayer Pro
- Various ERO networks

### 2. IRS Direct File Integration

**Approach**: Integrate with IRS Direct File for simple returns.

| Pros | Cons |
|------|------|
| Free for taxpayers | Limited form support |
| IRS-managed infrastructure | Only for simple returns |
| Built-in validation | Less customization |

**When to Consider**:
- Target audience has simple returns
- W-2 income only
- Standard deduction
- No complex credits

**IRS Direct File**: https://directfile.irs.gov

### 3. Hybrid Approach

**Approach**: Direct File for simple returns, transmitter partner for complex.

```
User Return Assessment
    |
    +-- Simple (W-2, standard deduction)
    |       |
    |       v
    |   IRS Direct File API
    |
    +-- Complex (Schedules, credits)
            |
            v
        Partner Transmitter
```

### Comparison Matrix

| Factor | Full MeF | Partner Transmitter | IRS Direct File |
|--------|----------|---------------------|-----------------|
| **Control** | Full | Partial | Limited |
| **Cost** | High upfront | Per-return | Free |
| **Time to Market** | 6+ months | 1-2 months | Immediate |
| **Form Support** | All | All | Limited |
| **Maintenance** | High | Low | None |

---

## References

### IRS Documentation

| Resource | URL |
|----------|-----|
| MeF Program | https://www.irs.gov/e-file-providers/modernized-e-file-program-information |
| Publication 3112 | https://www.irs.gov/pub/irs-pdf/p3112.pdf |
| Form 8633 | https://www.irs.gov/pub/irs-pdf/f8633.pdf |
| XML Schemas | https://www.irs.gov/e-file-providers/current-valid-xml-schemas-and-business-rules |
| Business Rules | https://www.irs.gov/e-file-providers/current-year-individual-income-tax-business-rules |
| ATS Information | https://www.irs.gov/e-file-providers/assurance-testing-system-ats |
| e-Services | https://www.irs.gov/e-file-providers/e-services-online-tools-for-tax-professionals |

### Technical Standards

| Standard | URL |
|----------|-----|
| SOAP 1.2 | https://www.w3.org/TR/soap12/ |
| WS-Security | https://www.oasis-open.org/committees/wss/ |
| XML-DSIG | https://www.w3.org/TR/xmldsig-core1/ |
| TLS 1.3 | https://datatracker.ietf.org/doc/html/rfc8446 |

### Project Files

| File | Purpose |
|------|---------|
| `direct-file/backend/src/main/resources/tax/mefTypes.xml` | MeF type definitions |
| `direct-file/backend/src/test/resources/scenarios/mef-ats-*.json` | ATS test scenarios |
| `direct-file/backend/src/test/resources/pdf-expected/en/olf-mef-ats-*.yml` | Expected outputs |
| `ai_service/services/mef_efile_service.py` | MeF transmission service (planned) |

### Related Documentation

- [Tax Logic Documentation](./engineering/Tax-Logic.md)
- [Fact Graph Writing Guide](./engineering/tax-flow/writing-facts.md)
- [Testing Documentation](./testing/)

---

## Appendix: MeF Error Codes

Common rejection codes and resolutions:

| Code | Description | Resolution |
|------|-------------|------------|
| `R0000-901-01` | SSN/Name mismatch | Verify taxpayer SSN/name matches SSA records |
| `R0000-902-01` | Duplicate return | Check if return already filed |
| `R0000-194-02` | Invalid date format | Use YYYY-MM-DD format |
| `R0000-500-01` | Schema validation error | Validate against IRS XSD |
| `R0000-503-02` | Business rule violation | Review IRS business rules |
| `R0000-521-01` | Missing required element | Add missing XML element |

---

*Last updated: January 2026*
*Version: 1.0*
*Maintainer: direct-file-easy-webui team*
