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
 * State Credits Subcategory
 * Handles state-specific tax credits and deductions
 */
export const StateCreditsSubcategory = (
  <Subcategory
    route='state-credits'
    completeIf='/stateCreditsIsDone'
    displayOnlyIf='/stateFilingRequired'
    dataItems={[
      {
        itemKey: `stateCreditsApplied`,
        conditions: [`/hasStateCredits`],
      },
      {
        itemKey: `noStateCredits`,
        conditions: [{ operator: `isFalse`, condition: `/hasStateCredits` }],
      },
    ]}
  >
    <SubSubcategory route='state-credits-intro'>
      <Screen route='state-credits-overview'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/state-taxes/credits' />
        <Heading i18nKey='/heading/state-taxes/credits/intro' />
        <InfoDisplay i18nKey='/info/state-taxes/credits/description' />
        <DFModal i18nKey='/info/state-taxes/credits/common-credits' />
        <DFAlert
          i18nKey='/info/state-taxes/credits/auto-applied'
          headingLevel='h3'
          type='info'
        />
        <SaveAndOrContinueButton />
      </Screen>
      <Assertion
        type='success'
        i18nKey='dataviews./flow/state-taxes/credits.assertions.stateCreditsApplied'
        condition='/hasStateCredits'
      />
    </SubSubcategory>
  </Subcategory>
);
