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
  IconDisplay,
  KnockoutButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * Alternative Minimum Tax (AMT) Subcategory
 * Handles Form 6251 AMT calculations
 */
export const AMTSubcategory = (
  <Subcategory
    route='amt'
    completeIf='/form6251IsDone'
    dataItems={[
      {
        itemKey: `amtApplies`,
        conditions: [`/amtApplies`],
      },
      {
        itemKey: `noAmt`,
        conditions: [{ operator: `isFalse`, condition: `/amtApplies` }],
      },
    ]}
  >
    <SubSubcategory route='amt-check'>
      <Screen route='amt-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/your-taxes/amt' />
        <Heading i18nKey='/heading/your-taxes/amt/intro' />
        <InfoDisplay i18nKey='/info/your-taxes/amt/description' />
        <DFModal i18nKey='/info/your-taxes/amt/who-pays' />
        <DFAlert
          i18nKey='/info/your-taxes/amt/auto-calculated'
          headingLevel='h3'
          type='info'
        />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/amtApplies'>
        <Screen route='amt-ko' isKnockout={true}>
          <IconDisplay name='ErrorOutline' size={9} isCentered />
          <Heading i18nKey='/heading/knockout/amt' />
          <InfoDisplay i18nKey='/info/knockout/amt/description' />
          <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
          <KnockoutButton i18nKey='button.knockout' />
        </Screen>
      </Gate>
      <Assertion
        type='info'
        i18nKey='dataviews./flow/your-taxes/amt.assertions.noAmtRequired'
        condition={{ operator: `isFalse`, condition: `/amtApplies` }}
      />
    </SubSubcategory>
  </Subcategory>
);
