/* eslint-disable max-len */
import { Gate, Screen, SubSubcategory, Assertion } from '../../flowDeclarations.js';
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
 * Retirement Credits SubSubcategory
 * Handles Form 8880 retirement savings contributions credit (Saver's Credit)
 * Note: This extends the existing SaversCreditSubSubcategory with additional retirement-related credits
 */
export const RetirementCreditsSubSubcategory = (
  <SubSubcategory route='retirement-credits' headingLevel='h2' borderStyle='heavy'>
    <Gate condition='/flowTrue'>
      <Screen route='retirement-credits-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/retirement' />
        <Heading i18nKey='/heading/credits-and-deductions/credits/retirement/intro' />
        <InfoDisplay i18nKey='/info/credits-and-deductions/credits/retirement/description' />
        <DFModal i18nKey='/info/credits-and-deductions/credits/retirement/eligibility' />
        <Boolean path='/madeRetirementContributions' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/madeRetirementContributions'>
        <Screen route='retirement-contribution-amount'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/retirement' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/retirement/amount' />
          <InfoDisplay i18nKey='/info/credits-and-deductions/credits/retirement/contribution-types' />
          <DFModal i18nKey='/info/credits-and-deductions/credits/retirement/ira-401k' />
          <Dollar path='/retirementContributionAmount' />
          <SaveAndOrContinueButton />
        </Screen>
        <Assertion
          type='success'
          i18nKey='dataviews./flow/credits-and-deductions/credits.assertions.retirementCreditQualified'
          condition='/retirementSavingsCreditQualified'
        />
        <Screen route='retirement-credit-qualified' condition='/retirementSavingsCreditQualified'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/retirement' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/retirement/qualified' />
          <InfoDisplay i18nKey='/info/credits-and-deductions/credits/retirement/credit-amount' />
          <DFAlert
            i18nKey='/info/credits-and-deductions/credits/retirement/credit-info'
            headingLevel='h3'
            type='success'
          />
          <SaveAndOrContinueButton />
        </Screen>
      </Gate>
    </Gate>
  </SubSubcategory>
);
