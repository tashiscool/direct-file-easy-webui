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
 * Adoption Credit SubSubcategory
 * Handles Form 8839 qualified adoption expenses credit
 */
export const AdoptionCreditSubSubcategory = (
  <SubSubcategory route='adoption-credit' headingLevel='h2' borderStyle='heavy'>
    <Gate condition='/flowTrue'>
      <Screen route='adoption-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/adoption' />
        <Heading i18nKey='/heading/credits-and-deductions/credits/adoption/intro' />
        <InfoDisplay i18nKey='/info/credits-and-deductions/credits/adoption/description' />
        <DFModal i18nKey='/info/credits-and-deductions/credits/adoption/what-qualifies' />
        <Boolean path='/hasAdoptionExpenses' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/hasAdoptionExpenses'>
        <Screen route='adoption-ko' isKnockout={true}>
          <IconDisplay name='ErrorOutline' size={9} isCentered />
          <Heading i18nKey='/heading/knockout/adoption-credit' />
          <InfoDisplay i18nKey='/info/knockout/adoption-credit/description' />
          <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
          <KnockoutButton i18nKey='button.knockout' />
        </Screen>
      </Gate>
    </Gate>
  </SubSubcategory>
);
