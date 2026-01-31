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
  DFAlert,
  Enum,
} from '../../ContentDeclarations.js';

/**
 * Home Energy Credit SubSubcategory
 * Handles Form 5695 residential energy credits
 */
export const HomeEnergyCreditSubSubcategory = (
  <SubSubcategory route='home-energy' headingLevel='h2' borderStyle='heavy'>
    <Gate condition='/flowTrue'>
      <Screen route='home-energy-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/home-energy' />
        <Heading i18nKey='/heading/credits-and-deductions/credits/home-energy/intro' />
        <InfoDisplay i18nKey='/info/credits-and-deductions/credits/home-energy/description' />
        <DFModal i18nKey='/info/credits-and-deductions/credits/home-energy/what-qualifies' />
        <Boolean path='/madeHomeEnergyImprovements' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/madeHomeEnergyImprovements'>
        <Screen route='home-energy-type'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/home-energy' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/home-energy/type' />
          <InfoDisplay i18nKey='/info/credits-and-deductions/credits/home-energy/categories' />
          <Enum path='/homeEnergyImprovementType' />
          <SaveAndOrContinueButton />
        </Screen>
        <Screen route='home-energy-cost'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/home-energy' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/home-energy/cost' />
          <DFModal i18nKey='/info/credits-and-deductions/credits/home-energy/credit-limits' />
          <Dollar path='/homeEnergyImprovementCost' />
          <SaveAndOrContinueButton />
        </Screen>
        <Assertion
          type='success'
          i18nKey='dataviews./flow/credits-and-deductions/credits.assertions.homeEnergyQualified'
          condition='/homeEnergyCreditQualified'
        />
        <Screen route='home-energy-qualified' condition='/homeEnergyCreditQualified'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/home-energy' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/home-energy/qualified' />
          <InfoDisplay i18nKey='/info/credits-and-deductions/credits/home-energy/credit-amount' />
          <DFAlert
            i18nKey='/info/credits-and-deductions/credits/home-energy/credit-info'
            headingLevel='h3'
            type='success'
          />
          <SaveAndOrContinueButton />
        </Screen>
      </Gate>
    </Gate>
  </SubSubcategory>
);
