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
 * Foreign Tax Credit SubSubcategory
 * Handles Form 1116 foreign tax credit
 */
export const ForeignTaxCreditSubSubcategory = (
  <SubSubcategory route='foreign-tax-credit' headingLevel='h2' borderStyle='heavy'>
    <Gate condition='/flowTrue'>
      <Screen route='foreign-tax-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/foreign-tax' />
        <Heading i18nKey='/heading/credits-and-deductions/credits/foreign-tax/intro' />
        <InfoDisplay i18nKey='/info/credits-and-deductions/credits/foreign-tax/description' />
        <DFModal i18nKey='/info/credits-and-deductions/credits/foreign-tax/what-qualifies' />
        <Boolean path='/paidForeignTax' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/paidForeignTax'>
        <Screen route='foreign-tax-ko' isKnockout={true}>
          <IconDisplay name='ErrorOutline' size={9} isCentered />
          <Heading i18nKey='/heading/knockout/foreign-tax-credit' />
          <InfoDisplay i18nKey='/info/knockout/foreign-tax-credit/description' />
          <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
          <KnockoutButton i18nKey='button.knockout' />
        </Screen>
      </Gate>
    </Gate>
  </SubSubcategory>
);
