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
  IconDisplay,
  KnockoutButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * Itemized Deductions SubSubcategory
 * Handles Schedule A itemized deductions (medical, taxes, interest, charity)
 */
export const ItemizedDeductionsSubSubcategory = (
  <SubSubcategory route='itemized-deductions' headingLevel='h2' borderStyle='heavy'>
    <Gate condition='/flowTrue'>
      <Screen route='itemized-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/deductions/itemized' />
        <Heading i18nKey='/heading/credits-and-deductions/deductions/itemized/intro' />
        <InfoDisplay i18nKey='/info/credits-and-deductions/deductions/itemized/description' />
        <DFModal i18nKey='/info/credits-and-deductions/deductions/itemized/vs-standard' />
        <Boolean path='/wantsItemizedDeductions' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/wantsItemizedDeductions'>
        <Screen route='itemized-ko' isKnockout={true}>
          <IconDisplay name='ErrorOutline' size={9} isCentered />
          <Heading i18nKey='/heading/knockout/itemized-deductions' />
          <InfoDisplay i18nKey='/info/knockout/itemized-deductions/description' />
          <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
          <KnockoutButton i18nKey='button.knockout' />
        </Screen>
      </Gate>
    </Gate>
  </SubSubcategory>
);
