/* eslint-disable max-len */
import { Gate, Screen, Subcategory, SubSubcategory, Assertion } from '../../flowDeclarations.js';
import {
  Boolean,
  ContextHeading,
  DFModal,
  Dollar,
  Heading,
  InfoDisplay,
  SaveAndOrContinueButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * OBBBA Income Subcategory
 * Handles One Big Beautiful Bill Act (2025) special income provisions:
 * - Trump Savings Account (Form 4547)
 * - Tip income exemption for service workers
 * - Senior citizen Social Security exemption
 * - Overtime pay tax exemption
 */
export const OBBBAIncomeSubcategory = (
  <Subcategory
    route='obbba-income'
    completeIf='/obbbaIncomeIsDone'
    dataItems={[
      {
        itemKey: `hasTrumpSavingsAccount`,
        conditions: [`/hasTrumpSavingsAccount`],
      },
      {
        itemKey: `hasTipIncomeExemption`,
        conditions: [`/tipIncomeExemptionQualified`],
      },
      {
        itemKey: `hasSeniorSocialSecurityExemption`,
        conditions: [`/seniorSocialSecurityExemptionQualified`],
      },
      {
        itemKey: `hasOvertimeExemption`,
        conditions: [`/overtimePayExemptionQualified`],
      },
    ]}
  >
    <SubSubcategory route='trump-savings-account'>
      <Screen route='trump-savings-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/obbba/trump-savings' />
        <Heading i18nKey='/heading/income/obbba/trump-savings/intro' />
        <InfoDisplay i18nKey='/info/income/obbba/trump-savings/description' />
        <DFModal i18nKey='/info/income/obbba/trump-savings/eligibility' />
        <Boolean path='/hasTrumpSavingsAccount' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/hasTrumpSavingsAccount'>
        <Screen route='trump-savings-contributions'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/obbba/trump-savings' />
          <Heading i18nKey='/heading/income/obbba/trump-savings/contributions' />
          <InfoDisplay i18nKey='/info/income/obbba/trump-savings/contribution-limits' />
          <Dollar path='/trumpSavingsContributions' />
          <SaveAndOrContinueButton />
        </Screen>
      </Gate>
    </SubSubcategory>
    <SubSubcategory route='tip-income-exemption'>
      <Screen route='tip-income-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/obbba/tips' />
        <Heading i18nKey='/heading/income/obbba/tips/intro' />
        <InfoDisplay i18nKey='/info/income/obbba/tips/description' />
        <DFModal i18nKey='/info/income/obbba/tips/who-qualifies' />
        <Boolean path='/isServiceWorkerWithTips' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/isServiceWorkerWithTips'>
        <Screen route='tip-income-amount'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/obbba/tips' />
          <Heading i18nKey='/heading/income/obbba/tips/amount' />
          <InfoDisplay i18nKey='/info/income/obbba/tips/exemption-limit' />
          <Dollar path='/tipIncomeAmount' />
          <SaveAndOrContinueButton />
        </Screen>
        <Assertion
          type='success'
          i18nKey='dataviews./flow/income/obbba.assertions.tipExemptionQualified'
          condition='/tipIncomeExemptionQualified'
        />
      </Gate>
    </SubSubcategory>
    <SubSubcategory route='senior-social-security'>
      <Screen route='senior-ss-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/obbba/senior-ss' />
        <Heading i18nKey='/heading/income/obbba/senior-ss/intro' />
        <InfoDisplay i18nKey='/info/income/obbba/senior-ss/description' />
        <DFModal i18nKey='/info/income/obbba/senior-ss/eligibility' />
        <DFAlert
          i18nKey='/info/income/obbba/senior-ss/auto-calculated'
          headingLevel='h3'
          type='info'
          condition='/seniorSocialSecurityExemptionQualified'
        />
        <SaveAndOrContinueButton />
      </Screen>
      <Assertion
        type='success'
        i18nKey='dataviews./flow/income/obbba.assertions.seniorSSExemptionQualified'
        condition='/seniorSocialSecurityExemptionQualified'
      />
    </SubSubcategory>
    <SubSubcategory route='overtime-exemption'>
      <Screen route='overtime-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/obbba/overtime' />
        <Heading i18nKey='/heading/income/obbba/overtime/intro' />
        <InfoDisplay i18nKey='/info/income/obbba/overtime/description' />
        <DFModal i18nKey='/info/income/obbba/overtime/who-qualifies' />
        <Boolean path='/hasOvertimePay' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/hasOvertimePay'>
        <Screen route='overtime-amount'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/obbba/overtime' />
          <Heading i18nKey='/heading/income/obbba/overtime/amount' />
          <InfoDisplay i18nKey='/info/income/obbba/overtime/how-to-calculate' />
          <Dollar path='/overtimePayAmount' />
          <SaveAndOrContinueButton />
        </Screen>
        <Assertion
          type='success'
          i18nKey='dataviews./flow/income/obbba.assertions.overtimeExemptionQualified'
          condition='/overtimePayExemptionQualified'
        />
      </Gate>
    </SubSubcategory>
  </Subcategory>
);
