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
 * Education Credits SubSubcategory
 * Handles Form 8863 American Opportunity and Lifetime Learning credits
 */
export const EducationCreditsSubSubcategory = (
  <SubSubcategory route='education-credits' headingLevel='h2' borderStyle='heavy'>
    <Gate condition='/flowTrue'>
      <Screen route='education-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/education' />
        <Heading i18nKey='/heading/credits-and-deductions/credits/education/intro' />
        <InfoDisplay i18nKey='/info/credits-and-deductions/credits/education/description' />
        <DFModal i18nKey='/info/credits-and-deductions/credits/education/types' />
        <Boolean path='/hasEducationExpenses' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/hasEducationExpenses'>
        <Screen route='education-expenses-ko' isKnockout={true}>
          <IconDisplay name='ErrorOutline' size={9} isCentered />
          <Heading i18nKey='/heading/knockout/education-credits' />
          <InfoDisplay i18nKey='/info/knockout/education-credits/description' />
          <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
          <KnockoutButton i18nKey='button.knockout' />
        </Screen>
      </Gate>
    </Gate>
  </SubSubcategory>
);
