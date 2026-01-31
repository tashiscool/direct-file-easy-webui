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
 * Qualified Business Income (QBI) Deduction Subcategory
 * Handles Form 8995/8995-A QBI deduction (Section 199A)
 */
export const QBIDeductionSubcategory = (
  <Subcategory
    route='qbi-deduction'
    completeIf='/form8995IsDone'
    dataItems={[
      {
        itemKey: `qbiDeductionApplies`,
        conditions: [`/hasQBI`],
      },
      {
        itemKey: `noQbiDeduction`,
        conditions: [{ operator: `isFalse`, condition: `/hasQBI` }],
      },
    ]}
  >
    <SubSubcategory route='qbi-intro'>
      <Screen route='qbi-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/business/qbi' />
        <Heading i18nKey='/heading/business/qbi/intro' />
        <InfoDisplay i18nKey='/info/business/qbi/description' />
        <DFModal i18nKey='/info/business/qbi/what-qualifies' />
        <Boolean path='/hasQBI' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasQBI'>
      <Screen route='qbi-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/qbi' />
        <InfoDisplay i18nKey='/info/knockout/qbi/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);
